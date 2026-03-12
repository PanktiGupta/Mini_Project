from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Optional
import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum

from .models import (
    Classroom,
    DutyAllocation,
    ExamSchedule,
    Faculty,
    PhD_Scholar,
    SeatingAllocation,
    TimeSlot,
    UFMRecord,
    Designation,
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
        lookup = Q(faculty=person)
    else:
        lookup = Q(phd_scholar=person)

    return DutyAllocation.objects.filter(
        lookup,
        exam__date=exam.date,
        exam__time_slot=exam.time_slot,
    ).exists()


def _annotate_ufm_counts_for_faculty() -> dict[int, int]:
    data = (
        UFMRecord.objects.values("faculty_id")
        .annotate(total=Sum("count"))
        .filter(faculty_id__isnull=False)
    )
    return {row["faculty_id"]: row["total"] for row in data}


def _annotate_ufm_counts_for_phd() -> dict[int, int]:
    data = (
        UFMRecord.objects.values("phd_scholar_id")
        .annotate(total=Sum("count"))
        .filter(phd_scholar_id__isnull=False)
    )
    return {row["phd_scholar_id"]: row["total"] for row in data}


def _ordered_faculty_queryset(designation: str) -> Iterable[Faculty]:
    """
    Base queryset for a designation, annotated with duty_count.
    UFM-based weighting is applied later in the allocator.
    """
    qs = Faculty.objects.filter(designation=designation).annotate(
        duty_count=Count("duties", distinct=True),
    )
    return qs.order_by("duty_count", "name")


def _ordered_phd_queryset() -> Iterable[PhD_Scholar]:
    qs = PhD_Scholar.objects.annotate(
        duty_count=Count("duties", distinct=True)
    ).order_by("duty_count", "name")
    return qs


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
                "ufm": self.ufm_phd.get(p.pk, 0),
                "assigned_this_exam": False,
            }

        # Track per-person duties per date to enforce minimum 1-slot gap
        self.duties_per_person_date: dict[str, set] = defaultdict(set)
        self._preload_existing_duties()

    def _preload_existing_duties(self) -> None:
        existing_allocs = DutyAllocation.objects.filter(exam__date=self.exam.date)
        for alloc in existing_allocs.select_related("faculty", "phd_scholar", "exam"):
            key = None
            if alloc.faculty:
                key = f"F-{alloc.faculty}"
            elif alloc.phd_scholar:
                key = f"P-{alloc.phd_scholar}"
            if key:
                self.duties_per_person_date[key].add(alloc.exam.id)

    def _weight_faculty(self, faculty_id: int) -> float:
        state = self.faculty_state[faculty_id]
        base_load = 1 + state["duty_count"]
        ufm = state["ufm"]
        # Odd-even rotation: odd UFM counts get a stronger penalty.
        ufm_factor = 1 + ufm
        if ufm % 2 == 1:
            ufm_factor += 1
        return 1.0 / (base_load * ufm_factor)

    def _weight_phd(self, phd_id: int) -> float:
        state = self.phd_state[phd_id]
        base_load = 1 + state["duty_count"]
        ufm = state["ufm"]
        ufm_factor = 1 + ufm
        if ufm % 2 == 1:
            ufm_factor += 1
        return 1.0 / (base_load * ufm_factor)

    def _can_assign_faculty(self, f: Faculty) -> bool:
        if _person_has_conflict(f, self.exam):
            return False
        key = f"F-{f.pk}"
        # Minimum 1-slot gap = at most one duty per date.
        if self.exam.pk in self.duties_per_person_date[key]:
            return False
        # No multiple duties within the same exam / slot.
        if self.faculty_state.get(f.pk, {}).get("assigned_this_exam"):
            return False
        return True

    def _can_assign_phd(self, p: PhD_Scholar) -> bool:
        if _person_has_conflict(p, self.exam):
            return False
        key = f"P-{p.pk}"
        if self.exam.pk in self.duties_per_person_date[key]:
            return False
        if self.phd_state.get(p.pk, {}).get("assigned_this_exam"):
            return False
        max_duties = p.max_duties or 0
        if max_duties and len(self.duties_per_person_date[key]) >= max_duties:
            return False
        return True

    def _pick_weighted_faculty(
        self, designation: str, needed: int
    ) -> List[Faculty]:
        source = self.professors if designation == Designation.PROFESSOR else self.assistants
        selected: List[Faculty] = []
        available_ids = [f.pk for f in source]

        while len(selected) < needed and available_ids:
            candidates = [
                fid
                for fid in available_ids
                if self._can_assign_faculty(self.faculty_state[fid]["obj"])
            ]
            if not candidates:
                break
            weights = [self._weight_faculty(fid) for fid in candidates]
            chosen_id = random.choices(candidates, weights=weights, k=1)[0]
            chosen = self.faculty_state[chosen_id]["obj"]
            selected.append(chosen)
            available_ids.remove(chosen_id)

        return selected

    def _pick_weighted_phd(self, needed: int) -> List[PhD_Scholar]:
        selected: List[PhD_Scholar] = []
        available_ids = [p.pk for p in self.phd_scholars]

        while len(selected) < needed and available_ids:
            candidates = [
                pid
                for pid in available_ids
                if self._can_assign_phd(self.phd_state[pid]["obj"])
            ]
            if not candidates:
                break
            weights = [self._weight_phd(pid) for pid in candidates]
            chosen_id = random.choices(candidates, weights=weights, k=1)[0]
            chosen = self.phd_state[chosen_id]["obj"]
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
                f"Insufficient Professors to cover all rooms. "
                f"Shortage occurred while allocating room {room.name}."
            )

        # 2 Assistant Professors
        assistants = self._pick_weighted_faculty(
            Designation.ASSISTANT_PROFESSOR, needed=2
        )
        if len(assistants) < 2:
            raise ValidationError(
                f"Insufficient Assistant Professors to cover all rooms. "
                f"Shortage occurred while allocating room {room.name}."
            )

        # 3 PhD Scholars
        phds = self._pick_weighted_phd(needed=3)
        if len(phds) < 3:
            raise ValidationError(
                f"Insufficient PhD Scholars to cover all rooms. "
                f"Shortage occurred while allocating room {room.name}."
            )

        # Create allocations and update state
        for f in profs + assistants:
            alloc = DutyAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                faculty=f,
            )
            created_allocations.append(alloc)
            state = self.faculty_state[f.pk]
            state["assigned_this_exam"] = True
            key = f"F-{f.pk}"
            self.duties_per_person_date[key].add(self.exam.pk)

        for p in phds:
            alloc = DutyAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                phd_scholar=p,
            )
            created_allocations.append(alloc)
            state = self.phd_state[p.pk]
            state["assigned_this_exam"] = True
            key = f"P-{p.pk}"
            self.duties_per_person_date[key].add(self.exam.pk)

    def _generate_seating(
        self,
    ) -> tuple[List[SeatingAllocation], List[str]]:
        seating_allocations: List[SeatingAllocation] = []
        alerts: List[str] = []

        expected = self.exam.expected_students or 0
        if expected <= 0:
            return seating_allocations, alerts

        total_capacity = self.exam.total_classroom_capacity
        if total_capacity < expected:
            alerts.append(
                "Detained alert (shortage): expected students exceed total classroom "
                "capacity. Some students may not have seats."
            )
        else:
            alerts.append(
                "Detained alert (doubt round): capacity looks sufficient; monitor "
                "for late entries and questions."
            )

        remaining = expected
        current_roll = 1
        for room in self.exam.classrooms.all().order_by("name"):
            if remaining <= 0:
                break
            seats_for_room = min(room.capacity, remaining)
            start_roll = current_roll
            end_roll = current_roll + seats_for_room - 1
            seating = SeatingAllocation.objects.create(
                exam=self.exam,
                classroom=room,
                start_roll=start_roll,
                end_roll=end_roll,
                capacity_used=seats_for_room,
            )
            seating_allocations.append(seating)
            current_roll = end_roll + 1
            remaining -= seats_for_room

        if remaining > 0:
            alerts.append(
                "Detained alert (shortage): not all students could be seated within "
                "available classroom capacities."
            )

        return seating_allocations, alerts

    def run(self) -> AllocationResult:
        created_allocations: List[DutyAllocation] = []
        detained_alerts: List[str] = []
        capacity_warnings: List[str] = []

        # Capacity-level warning (question paper planning)
        if (
            self.exam.expected_students
            and self.exam.total_classroom_capacity < self.exam.expected_students
        ):
            capacity_warnings.append(
                f"Total classroom capacity ({self.exam.total_classroom_capacity}) "
                f"is less than expected students ({self.exam.expected_students}) "
                f"for exam {self.exam}."
            )

        # Allocate duties per classroom
        for room in self.exam.classrooms.all().order_by("name"):
            self._assign_to_room(room, created_allocations)

        # Seating allocation and detained alerts
        seating_allocations, alerts = self._generate_seating()
        detained_alerts.extend(alerts)

        return AllocationResult(
            created_allocations=created_allocations,
            seating_allocations=seating_allocations,
            detained_alerts=detained_alerts,
            capacity_warnings=capacity_warnings,
        )


@transaction.atomic
def allocate_duties_for_exam(exam: ExamSchedule) -> AllocationResult:
    """
    Public API to run the allocation for a given exam and return the
    final allocation list, seating plan, and detained alerts.
    """
    allocator = DutyAllocator(exam)
    return allocator.run()

