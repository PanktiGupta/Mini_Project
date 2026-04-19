from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Optional
import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum

from .emails import send_duty_allocation_email
from collections import defaultdict

from .emails import send_duty_allocation_email

from .models import (
    Classroom,
    DutyAllocation,
    ExamSchedule,
    Faculty,
    PhDScholar,
    SeatingAllocation,
    
    UFMRecord,
    Designation,
    Role,
)


@dataclass
class AllocationResult:
    created_allocations: List[DutyAllocation]
    seating_allocations: List[SeatingAllocation]
    detained_alerts: List[str]
    capacity_warnings: List[str]


def _person_has_conflict(person, exam: ExamSchedule) -> bool:
    """Check if person already has duty in the same date & slot."""
    if isinstance(person, Faculty):
        lookup = Q(assigned_to = person.user, role= Role.FACULTY)
    else:
        lookup = Q(assigned_to = person.user, role= Role.PHD)

    return DutyAllocation.objects.filter(
        lookup,
        exam__date=exam.date,
        exam__time_slot=exam.time_slot,
    ).exists()


def _annotate_ufm_counts_for_faculty() -> dict[int, int]:
    data = (
        UFMRecord.objects.filter(user__faculty__isnull=False)
        .values("user_id")
        .annotate(total=Sum("count"))
        
    )
    return {row["user_id"]: row["total"] for row in data}


def _annotate_ufm_counts_for_phd() -> dict[int, int]:
    data = (
        UFMRecord.objects.filter(user__phdscholar__isnull=False)
        .values("user_id")
        .annotate(total=Sum("count"))
       
    )
    return {row["user_id"]: row["total"] for row in data}


def _ordered_faculty_queryset(designation: str) -> Iterable[Faculty]:
    """
    Base queryset for a designation, annotated with duty_count.
    UFM-based weighting is applied later in the allocator.
    """
    qs = Faculty.objects.filter(designation=designation, is_active = True).annotate(
        duty_count=Count("user__duties", distinct=True),
    )
    return qs.order_by("duty_count", "user__first_name")


def _ordered_phd_queryset() -> Iterable[PhDScholar]:
    return PhDScholar.objects.filter(is_active = True).annotate(
        duty_count=Count("user__duties", distinct=True)
    ).order_by("duty_count", "user__first_name")


class DutyAllocator:
    """
    Object-oriented allocator implementing the full set of rules:

    - Per classroom: 1 Professor, 2 Assistant Professors, 3 PhD Scholars.
    - No overlapping duties per time slot.
    - Minimum 1-slot gap for Professors and PhD Scholars (max 1 duty per date).
    - UFM-based odd-even style weighting to reduce chance for high-UFM staff.
    - Fair, random, weighted distribution across all faculty.
    - Validation error if there is insufficient staff to satisfy all rooms.
    - Seating allocation based on classroom capacity and roll number ranges.
    - Detained alerts based on shortage / doubt conditions.
    """

    def __init__(self, exam: ExamSchedule) -> None:
        self.exam = exam
        self.ufm_faculty = _annotate_ufm_counts_for_faculty()
        self.ufm_phd = _annotate_ufm_counts_for_phd()

        self.professors = list(_ordered_faculty_queryset(Designation.PROFESSOR))
        self.assistants = list(_ordered_faculty_queryset(Designation.ASSISTANT_PROFESSOR))
        self.phd_scholars = list(_ordered_phd_queryset())

        self.faculty_state: dict[int, dict] = {}
        for f in self.professors + self.assistants:
            self.faculty_state[f.pk] = {
                "obj": f,
                "duty_count": getattr(f, "duty_count", 0),
                "ufm": self.ufm_faculty.get(f.pk, 0),
                "assigned_this_exam": False,
            }

        self.phd_state: dict[int, dict] = {}
        for p in self.phd_scholars:
            self.phd_state[p.pk] = {
                "obj": p,
                "duty_count": getattr(p, "duty_count", 0),
                "ufm": self.ufm_phd.get(p.user.pk, 0),
                "assigned_this_exam": False,
            }

        # Track per-person duties per date to enforce minimum 1-slot gap
        self.duties_per_person_date: dict[str, set] = defaultdict(set)
        self._preload_existing_duties()

    def _preload_existing_duties(self) -> None:
        existing_allocs = DutyAllocation.objects.filter(exam__date=self.exam.date).select_related("assigned_to", "exam")
        for alloc in existing_allocs:
            
            prefix = "F" if alloc.role == Role.FACULTY else "P"
            key = f"{prefix}-{alloc.assigned_to.pk}"
            self.duties_per_person_date[key].add(alloc.exam.pk)


    def _weight_faculty(self, user_id: int) -> float:
        state     = self.faculty_state[user_id]
        base_load = 1 + state["duty_count"]
        ufm       = state["ufm"]
        ufm_factor = 1 + ufm + (1 if ufm % 2 == 1 else 0)  
        return 1.0 / (base_load * ufm_factor)

    def _weight_phd(self, user_id: int) -> float:
        state     = self.phd_state[user_id]
        base_load = 1 + state["duty_count"]
        ufm       = state["ufm"]
        ufm_factor = 1 + ufm + (1 if ufm % 2 == 1 else 0)  
        return 1.0 / (base_load * ufm_factor)

    def _can_assign_faculty(self, f: Faculty) -> bool:
        if _person_has_conflict(f, self.exam):
            return False
        key   = f"F-{f.user.pk}"                            
        state = self.faculty_state.get(f.user.pk, {})
        return (
            self.exam.pk not in self.duties_per_person_date[key]
            and not state.get("assigned_this_exam")
        )

    def _can_assign_phd(self, p: PhDScholar) -> bool:
        if _person_has_conflict(p, self.exam):
            return False
        key        = f"P-{p.user.pk}"                       
        state      = self.phd_state.get(p.user.pk, {})
        max_duties = p.max_duties or 0
        if max_duties and len(self.duties_per_person_date[key]) >= max_duties:
            return False
        return (
            self.exam.pk not in self.duties_per_person_date[key]
            and not state.get("assigned_this_exam")
        )

    def _can_assign_phd(self, p: PhDScholar) -> bool:
        if _person_has_conflict(p, self.exam):
            return False
        key        = f"P-{p.user.pk}"                       
        state      = self.phd_state.get(p.user.pk, {})
        max_duties = p.max_duties or 0
        if max_duties and len(self.duties_per_person_date[key]) >= max_duties:
            return False
        return (
            self.exam.pk not in self.duties_per_person_date[key]
            and not state.get("assigned_this_exam")
        )
    def _pick_weighted_faculty(self, designation: str, needed: int) -> List[Faculty]:
        source        = self.professors if designation == Designation.PROFESSOR else self.assistants
        selected: List[Faculty] = []
        available_ids = [f.user.pk for f in source]        

        while len(selected) < needed and available_ids:
            candidates = [
                uid for uid in available_ids
                if self._can_assign_faculty(self.faculty_state[uid]["obj"])
            ]
            if not candidates:
                break
            weights   = [self._weight_faculty(uid) for uid in candidates]
            chosen_id = random.choices(candidates, weights=weights, k=1)[0]
            chosen    = self.faculty_state[chosen_id]["obj"]
            selected.append(chosen)
            available_ids.remove(chosen_id)

        return selected
    def _pick_weighted_phd(self, needed: int) -> List[PhDScholar]:
        selected: List[PhDScholar] = []
        available_ids = [p.user.pk for p in self.phd_scholars]  

        while len(selected) < needed and available_ids:
            candidates = [
                uid for uid in available_ids
                if self._can_assign_phd(self.phd_state[uid]["obj"])
            ]
            if not candidates:
                break
            weights   = [self._weight_phd(uid) for uid in candidates]
            chosen_id = random.choices(candidates, weights=weights, k=1)[0]
            chosen    = self.phd_state[chosen_id]["obj"]
            selected.append(chosen)
            available_ids.remove(chosen_id)

        return selected


    def _assign_to_room(
        self, room: Classroom, created_allocations: List[DutyAllocation]
    ) -> None:

        # 1 Professor
        profs = self._pick_weighted_faculty(Designation.PROFESSOR, needed=1)
        if len(profs) < 1:
            raise ValidationError(
                f"Insufficient Professors for room {room.name}."
            )

        # 2 Assistant Professors
        assistants = self._pick_weighted_faculty(Designation.ASSISTANT_PROFESSOR, needed=2)
        if len(assistants) < 2:
            raise ValidationError(
                f"Insufficient Assistant Professors for room {room.name}."
            )

        # 3 PhD Scholars
        phds = self._pick_weighted_phd(needed=3)
        if len(phds) < 3:
            raise ValidationError(
                f"Insufficient PhD Scholars for room {room.name}."
            )

        for f in profs + assistants:
            alloc = DutyAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                assigned_to=f.user,                         
                role=Role.FACULTY,                          
            )
            created_allocations.append(alloc)
            self.faculty_state[f.user.pk]["assigned_this_exam"] = True
            self.duties_per_person_date[f"F-{f.user.pk}"].add(self.exam.pk)

        for p in phds:
            alloc = DutyAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                assigned_to=p.user,                         
                role=Role.PHD,                              
            )
            created_allocations.append(alloc)
            self.phd_state[p.user.pk]["assigned_this_exam"] = True
            self.duties_per_person_date[f"P-{p.user.pk}"].add(self.exam.pk)
    def _generate_seating(self) -> tuple[List[SeatingAllocation], List[str]]:
        seating_allocations: List[SeatingAllocation] = []
        alerts: List[str] = []

        expected = self.exam.expected_students or 0
        if expected <= 0:
            return seating_allocations, alerts

        total_capacity = self.exam.total_classroom_capacity
        if total_capacity < expected:
            alerts.append(
                "Detained alert (shortage): expected students exceed total "
                "classroom capacity. Some students may not have seats."
            )
        else:
            alerts.append(
                "Detained alert (doubt round): capacity sufficient; monitor "
                "for late entries."
            )

        remaining    = expected
        current_roll = 1

        for room in self.exam.classrooms.filter(is_available=True).order_by("name"):  
            if remaining <= 0:
                break
            seats_for_room = min(room.capacity, remaining)
            start_roll     = current_roll
            end_roll       = current_roll + seats_for_room - 1

            seating = SeatingAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                start_roll=start_roll,
                end_roll=end_roll,
                capacity_used=seats_for_room,
            )
            seating_allocations.append(seating)
            current_roll = end_roll + 1
            remaining   -= seats_for_room

        if remaining > 0:
            alerts.append(
                "Detained alert (shortage): not all students could be seated "
                "within available classroom capacities."
            )

        return seating_allocations, alerts
    
    def run(self) -> AllocationResult:
        created_allocations: List[DutyAllocation] = []
        detained_alerts: List[str]                = []
        capacity_warnings: List[str]              = []

        # Capacity warning
        if (
            self.exam.expected_students
            and self.exam.total_classroom_capacity < self.exam.expected_students
        ):
            capacity_warnings.append(
                f"Total capacity ({self.exam.total_classroom_capacity}) "
                f"is less than expected students ({self.exam.expected_students}) "
                f"for {self.exam}."
            )

        # Allocate duties per classroom
        for room in self.exam.classrooms.filter(is_available=True).order_by("name"):  
            self._assign_to_room(room, created_allocations)

        # Seating + alerts
        seating_allocations, alerts = self._generate_seating()
        detained_alerts.extend(alerts)

        self._send_allocation_emails(created_allocations)


        return AllocationResult(
            created_allocations=created_allocations,
            seating_allocations=seating_allocations,
            detained_alerts=detained_alerts,
            capacity_warnings=capacity_warnings,
        )
    
    def _send_allocation_emails(
        self, allocations: List[DutyAllocation]
    ) -> None:
        """
        Group allocations by user and send
        one email per person with all duties listed.
        """
        user_allocations: dict = defaultdict(list)
        for alloc in allocations:
            user_allocations[alloc.assigned_to].append(alloc)

        for user, user_allocs in user_allocations.items():
            send_duty_allocation_email(user, user_allocs)

@transaction.atomic
def allocate_duties_for_exam(exam: ExamSchedule) -> AllocationResult:
    """
    Public API to run the allocation for a given exam and return the
    final allocation list, seating plan, and detained alerts.
    """
    allocator = DutyAllocator(exam)
    return allocator.run()    





