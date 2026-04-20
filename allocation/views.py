from __future__ import annotations

import csv
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    AllocationRunForm,
    ClassroomForm,
    ExamScheduleForm,
    FacultyForm,
    PhDScholarForm,
)
from .models import (
    Classroom,
    DutyAllocation,
    ExamSchedule,
    Faculty,
    PhDScholar,
    Role,
    SeatingAllocation,
    UFMRecord,
)
from .services import allocate_duties_for_exam


# ─────────────────────────────────────
# Dashboard
# ─────────────────────────────────────
@login_required(login_url="/login/")
def dashboard(request):
    context = {
        "faculty_count":    Faculty.objects.filter(is_active=True).count(),
        "phd_count":        PhDScholar.objects.filter(is_active=True).count(),
        "classroom_count":  Classroom.objects.filter(is_available=True).count(),
        "exam_count":       ExamSchedule.objects.count(),
        "allocation_count": DutyAllocation.objects.count(),
        "ufm_count":        UFMRecord.objects.count(),
    }
    return render(request, "allocation/dashboard.html", context)


# ─────────────────────────────────────
# Redirect after login based on role
# ─────────────────────────────────────
@login_required(login_url="/login/")
def redirect_dashboard(request):
    if request.user.is_superuser:
        return redirect("allocation:dashboard")
    if Faculty.objects.filter(user=request.user).exists():
        return redirect("allocation:faculty_timetable")
    if PhDScholar.objects.filter(user=request.user).exists():
        return redirect("allocation:phd_timetable")
    return redirect("allocation:login")


# ─────────────────────────────────────
# Faculty List & Create
# ─────────────────────────────────────
@login_required(login_url="/login/")
def faculty_list_create(request):
    if request.method == "POST":
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty added successfully.")
            return redirect("allocation:faculty_list")
    else:
        form = FacultyForm()

    faculty = Faculty.objects.select_related("user").order_by("user__first_name")
    return render(request, "allocation/faculty_list.html", {
        "form":         form,
        "faculty_list": faculty,
    })


@login_required(login_url="/login/")
def faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == "POST":
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty updated successfully.")
            return redirect("allocation:faculty_list")
    else:
        form = FacultyForm(instance=faculty)

    return render(request, "allocation/faculty_form.html", {
        "form":  form,
        "title": "Edit Faculty",
    })


@login_required(login_url="/login/")
def faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == "POST":
        faculty.user.delete()
        messages.success(request, "Faculty deleted successfully.")
        return redirect("allocation:faculty_list")

    return render(request, "allocation/confirm_delete.html", {
        "object": faculty,
        "title":  "Delete Faculty",
    })


# ─────────────────────────────────────
# PhD Scholar List & Create
# ─────────────────────────────────────
@login_required(login_url="/login/")
def phd_list_create(request):
    if request.method == "POST":
        form = PhDScholarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "PhD Scholar added successfully.")
            return redirect("allocation:phd_list")
    else:
        form = PhDScholarForm()

    phd_list = PhDScholar.objects.select_related("user").order_by("user__first_name")
    return render(request, "allocation/phd_list.html", {
        "form":     form,
        "phd_list": phd_list,
    })


@login_required(login_url="/login/")
def phd_edit(request, pk):
    scholar = get_object_or_404(PhDScholar, pk=pk)
    if request.method == "POST":
        form = PhDScholarForm(request.POST, instance=scholar)
        if form.is_valid():
            form.save()
            messages.success(request, "PhD Scholar updated successfully.")
            return redirect("allocation:phd_list")
    else:
        form = PhDScholarForm(instance=scholar)

    return render(request, "allocation/phd_form.html", {
        "form":  form,
        "title": "Edit PhD Scholar",
    })


@login_required(login_url="/login/")
def phd_delete(request, pk):
    scholar = get_object_or_404(PhDScholar, pk=pk)
    if request.method == "POST":
        scholar.user.delete()
        messages.success(request, "PhD Scholar deleted successfully.")
        return redirect("allocation:phd_list")

    return render(request, "allocation/confirm_delete.html", {
        "object": scholar,
        "title":  "Delete PhD Scholar",
    })


# ─────────────────────────────────────
# Classroom List & Create
# ─────────────────────────────────────
@login_required(login_url="/login/")
def classroom_list_create(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Classroom added successfully.")
            return redirect("allocation:classroom_list")
    else:
        form = ClassroomForm()

    classrooms = Classroom.objects.all().order_by("name")
    return render(request, "allocation/classroom_list.html", {
        "form":           form,
        "classroom_list": classrooms,
    })


@login_required(login_url="/login/")
def classroom_edit(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, "Classroom updated successfully.")
            return redirect("allocation:classroom_list")
    else:
        form = ClassroomForm(instance=classroom)

    return render(request, "allocation/classroom_form.html", {
        "form":  form,
        "title": "Edit Classroom",
    })


@login_required(login_url="/login/")
def classroom_delete(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        classroom.delete()
        messages.success(request, "Classroom deleted successfully.")
        return redirect("allocation:classroom_list")

    return render(request, "allocation/confirm_delete.html", {
        "object": classroom,
        "title":  "Delete Classroom",
    })


# ─────────────────────────────────────
# Exam Schedule List & Create
# ─────────────────────────────────────
@login_required(login_url="/login/")
def exam_list_create(request):
    if request.method == "POST":
        form = ExamScheduleForm(request.POST)
        if form.is_valid():
            exam = form.save()
            if exam.expected_students and exam.total_classroom_capacity < exam.expected_students:
                messages.warning(
                    request,
                    "Question paper shortage alert: expected students exceed total classroom capacity.",
                )
            else:
                messages.info(request, "Doubt round: capacity looks sufficient.")
            messages.success(request, "Exam schedule added successfully.")
            return redirect("allocation:exam_list")
    else:
        form = ExamScheduleForm()

    exams = ExamSchedule.objects.all().order_by("date", "time_slot")
    return render(request, "allocation/exam_list.html", {
        "form":      form,
        "exam_list": exams,
    })


@login_required(login_url="/login/")
def exam_edit(request, pk):
    exam = get_object_or_404(ExamSchedule, pk=pk)
    if request.method == "POST":
        form = ExamScheduleForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam schedule updated successfully.")
            return redirect("allocation:exam_list")
    else:
        form = ExamScheduleForm(instance=exam)

    return render(request, "allocation/exam_form.html", {
        "form":  form,
        "title": "Edit Exam Schedule",
    })


@login_required(login_url="/login/")
def exam_delete(request, pk):
    exam = get_object_or_404(ExamSchedule, pk=pk)
    if request.method == "POST":
        exam.delete()
        messages.success(request, "Exam schedule deleted successfully.")
        return redirect("allocation:exam_list")

    return render(request, "allocation/confirm_delete.html", {
        "object": exam,
        "title":  "Delete Exam Schedule",
    })

@login_required(login_url="/login/")
def run_allocation(request):
    if request.method == "POST":
        form = AllocationRunForm(request.POST)
        if form.is_valid():
            exam = form.cleaned_data["exam"]
            try:
                result = allocate_duties_for_exam(exam)
            except ValidationError as exc:
                messages.error(request, str(exc))
                return redirect("allocation:run_allocation")

            if result.created_allocations:
                messages.success(
                    request,
                    f"Created {len(result.created_allocations)} duty records for {exam}.",
                )
            for warning in result.capacity_warnings:
                messages.warning(request, warning)
            for alert in result.detained_alerts:
                messages.info(request, alert)

            return redirect(
                reverse("allocation:allocation_table") + f"?exam_id={exam.id}"
            )
    else:
        form = AllocationRunForm()
    
    recent_exams = ExamSchedule.objects.filter(
        duty_allocations__isnull=False
    ).distinct().order_by("-date")[:5]

    return render(request, "allocation/run_allocation.html", {
        "form":         form,
        "recent_exams": recent_exams,  
    })




   

# ─────────────────────────────────────
# Allocation Table
# ─────────────────────────────────────
@login_required(login_url="/login/")
def allocation_table(request):
    exam_id = request.GET.get("exam_id")

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "assigned_to"
    )

    exam = None
    if exam_id:
        allocations = allocations.filter(exam_id=exam_id)
        exam = ExamSchedule.objects.filter(pk=exam_id).first()

    allocations = allocations.order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "assigned_to__first_name",
    )

    return render(request, "allocation/allocation_table.html", {
        "allocations": allocations,
        "exam":        exam,
    })


# ─────────────────────────────────────
# Seating Plan
# ─────────────────────────────────────
@login_required(login_url="/login/")
def seating_plan(request):
    exam_id = request.GET.get("exam_id")

    seating = SeatingAllocation.objects.select_related(
        "exam", "classroom"
    ).order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "start_roll",
    )

    exam = None
    if exam_id:
        seating = seating.filter(exam_id=exam_id)
        exam = ExamSchedule.objects.filter(pk=exam_id).first()

    return render(request, "allocation/seating_plan.html", {
        "seating_allocations": seating,
        "exam":                exam,
    })


# ─────────────────────────────────────
# UFM History
# ─────────────────────────────────────
@login_required(login_url="/login/")
def ufm_history(request):
    records = UFMRecord.objects.select_related(
        "exam", "user"
    ).order_by("-exam__date", "-last_updated")

    return render(request, "allocation/ufm_history.html", {"records": records})


# ─────────────────────────────────────
# Export CSV
# ─────────────────────────────────────
@login_required(login_url="/login/")
def export_allocations_csv(request):
    exam_id = request.GET.get("exam_id")

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "assigned_to"
    )

    if exam_id:
        allocations = allocations.filter(exam_id=exam_id)

    allocations = allocations.order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "assigned_to__first_name",
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="duty_allocations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Serial Number",
        "Name",
        "Role",
        "Designation",
        "Date",
        "Time Slot",
        "Room Number",
    ])

    for idx, alloc in enumerate(allocations, start=1):
        full_name  = alloc.assigned_to.get_full_name() or alloc.assigned_to.username
        role_label = alloc.get_role_display()

        if alloc.role == Role.FACULTY:
            try:
                designation = alloc.assigned_to.faculty.get_designation_display()
            except AttributeError:
                designation = "Faculty"
        else:
            designation = "PhD Scholar"

        writer.writerow([
            idx,
            full_name,
            role_label,
            designation,
            alloc.exam.date,
            alloc.exam.get_time_slot_display(),
            alloc.classroom.name,
        ])

    return response


# ─────────────────────────────────────
# Faculty Personal Dashboard          
# ─────────────────────────────────────
@login_required(login_url="/login/")
def faculty_timetable(request):
    try:
        faculty = Faculty.objects.select_related("user").get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect("allocation:login")

    today = timezone.now().date()

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom"
    ).filter(
        assigned_to=request.user,
        role=Role.FACULTY,
    ).order_by("exam__date", "exam__time_slot")

    ufm_records = UFMRecord.objects.select_related(
        "exam"
    ).filter(
        user=request.user
    ).order_by("-exam__date")

    total_duties    = allocations.count()
    upcoming_duties = allocations.filter(exam__date__gte=today).count()
    past_duties     = allocations.filter(exam__date__lt=today).count()
    total_ufm       = sum(r.count for r in ufm_records)

    return render(request, "allocation/faculty_timetable.html", {
        # object
        "faculty":          faculty,
        # personal info
        "full_name":        faculty.user.get_full_name() or faculty.user.username,
        "email":            faculty.user.email,
        "username":         faculty.user.username,
        "designation":      faculty.get_designation_display(),
        "department":       faculty.department,
        "duty_quota":       faculty.duty_quota,
        "is_active":        faculty.is_active,
        "joined":           faculty.user.date_joined,
        # data
        "allocations":      allocations,
        "ufm_records":      ufm_records,
        # stats
        "today":            today,
        "total_duties":     total_duties,
        "upcoming_duties":  upcoming_duties,
        "past_duties":      past_duties,
        "total_ufm":        total_ufm,
    })


# ─────────────────────────────────────
# PhD Personal Dashboard             
# ─────────────────────────────────────
@login_required(login_url="/login/")
def phd_timetable(request):
    try:
        phd = PhDScholar.objects.select_related("user").get(user=request.user)
    except PhDScholar.DoesNotExist:
        messages.error(request, "PhD Scholar profile not found.")
        return redirect("allocation:login")

    today = timezone.now().date()

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom"
    ).filter(
        assigned_to=request.user,
        role=Role.PHD,
    ).order_by("exam__date", "exam__time_slot")

    ufm_records = UFMRecord.objects.select_related(
        "exam"
    ).filter(
        user=request.user
    ).order_by("-exam__date")

    total_duties    = allocations.count()
    upcoming_duties = allocations.filter(exam__date__gte=today).count()
    past_duties     = allocations.filter(exam__date__lt=today).count()
    duties_left     = max(0, phd.max_duties - total_duties)
    total_ufm       = sum(r.count for r in ufm_records)

    return render(request, "allocation/phd_timetable.html", {
        # object
        "phd":              phd,
        # personal info
        "full_name":        phd.user.get_full_name() or phd.user.username,
        "email":            phd.user.email,
        "username":         phd.user.username,
        "max_duties":       phd.max_duties,
        "is_active":        phd.is_active,
        "joined":           phd.user.date_joined,
        # data
        "allocations":      allocations,
        "ufm_records":      ufm_records,
        # stats
        "today":            today,
        "total_duties":     total_duties,
        "upcoming_duties":  upcoming_duties,
        "past_duties":      past_duties,
        "duties_left":      duties_left,
        "total_ufm":        total_ufm,
    })


    
@login_required(login_url="/login/")
def resend_allocation_emails(request, exam_id):
    exam = get_object_or_404(ExamSchedule, pk=exam_id)

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "assigned_to"
    ).filter(exam=exam)

    if not allocations.exists():
        messages.error(request, "No allocations found for this exam.")
        return redirect("allocation:allocation_table")

    from collections import defaultdict
    from .emails import send_duty_allocation_email

    user_allocations = defaultdict(list)
    for alloc in allocations:
        user_allocations[alloc.assigned_to].append(alloc)

    count = 0
    for user, user_allocs in user_allocations.items():
        send_duty_allocation_email(user, user_allocs)
        count += 1

    messages.success(
        request,
        f"✅ Emails resent to {count} people for {exam.course_name}."
    )
    return redirect(
        reverse("allocation:allocation_table") + f"?exam_id={exam.id}"
    )