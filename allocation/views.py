# from __future__ import annotations
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.core.exceptions import ValidationError
# from django.http import HttpResponse
# from django.shortcuts import redirect, render
# from django.urls import reverse

# import csv

# from .forms import (
#     AllocationRunForm,
#     ClassroomForm,
#     ExamScheduleForm,
#     FacultyForm,
#     PhDScholarForm,
# )
# from .models import Classroom, DutyAllocation, ExamSchedule, Faculty, PhDScholar, SeatingAllocation, UFMRecord
# from .services import allocate_duties_for_exam

# @login_required(login_url = "/login/")
# def dashboard(request):
#     context = {
#         "faculty_count": Faculty.objects.count(),
#         "phd_count": PhDScholar.objects.count(),
#         "classroom_count": Classroom.objects.count(),
#         "exam_count": ExamSchedule.objects.count(),
#     }
#     return render(request, "allocation/dashboard.html", context)


# def faculty_list_create(request):
#     if request.method == "POST":
#         form = FacultyForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Faculty added successfully.")
#             return redirect("allocation:faculty_list")
#     else:
#         form = FacultyForm()

#     faculty = Faculty.objects.all().order_by("name")
#     return render(
#         request,
#         "allocation/faculty_list.html",
#         {"form": form, "faculty_list": faculty},
#     )


# def phd_list_create(request):
#     if request.method == "POST":
#         form = PhDScholarForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "PhD Scholar added successfully.")
#             return redirect("allocation:phd_list")
#     else:
#         form = PhDScholarForm()

#     phd_list = PhDScholar.objects.all().order_by("name")
#     return render(
#         request,
#         "allocation/phd_list.html",
#         {"form": form, "phd_list": phd_list},
#     )


# def classroom_list_create(request):
#     if request.method == "POST":
#         form = ClassroomForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Classroom added successfully.")
#             return redirect("allocation:classroom_list")
#     else:
#         form = ClassroomForm()

#     classrooms = Classroom.objects.all().order_by("name")
#     return render(
#         request,
#         "allocation/classroom_list.html",
#         {"form": form, "classroom_list": classrooms},
#     )




# def exam_list_create(request):
#     if request.method == "POST":
#         form = ExamScheduleForm(request.POST)
#         if form.is_valid():
#             exam = form.save()
#             # Simple alert logic based on capacity
#             if (
#                 exam.expected_students
#                 and exam.total_classroom_capacity < exam.expected_students
#             ):
#                 messages.warning(
#                     request,
#                     "Question paper shortage alert: expected students exceed total classroom capacity.",
#                 )
#             else:
#                 messages.info(request, "Doubt round: capacity looks sufficient.")

#             messages.success(request, "Exam schedule added successfully.")
#             return redirect("allocation:exam_list")
#     else:
#         form = ExamScheduleForm()

#     exams = ExamSchedule.objects.all().order_by("date", "time_slot")
#     return render(
#         request,
#         "allocation/exam_list.html",
#         {"form": form, "exam_list": exams},
#     )


# def run_allocation(request):
#     if request.method == "POST":
#         form = AllocationRunForm(request.POST)
#         if form.is_valid():
#             exam = form.cleaned_data["exam"]
#             try:
#                 result = allocate_duties_for_exam(exam)
#             except ValidationError as exc:
#                 messages.error(request, str(exc))
#                 return redirect("allocation:run_allocation")

#             if result.created_allocations:
#                 messages.success(
#                     request,
#                     f"Created {len(result.created_allocations)} duty records for exam {exam}.",
#                 )
#             for warning in result.capacity_warnings:
#                 messages.warning(request, warning)
#             for alert in result.detained_alerts:
#                 messages.info(request, alert)

#             return redirect(
#                 reverse("allocation:allocation_result") + f"?exam_id={exam.id}"
#             )
#     else:
#         form = AllocationRunForm()

#     return render(request, "allocation/run_allocation.html", {"form": form})


# def allocation_result(request):
#     exam_id = request.GET.get("exam_id")
#     allocations = DutyAllocation.objects.select_related(
#         "exam", "classroom", "faculty", "phd_scholar"
#     )
#     exam = None
#     seating = SeatingAllocation.objects.none()
#     if exam_id:
#         allocations = allocations.filter(exam_id=exam_id)
#         exam = ExamSchedule.objects.filter(id=exam_id).first()
#         seating = SeatingAllocation.objects.filter(exam_id=exam_id).order_by(
#             "classroom__name", "start_roll"
#         )

#     allocations = allocations.order_by(
#         "exam__date",
#         "exam__time_slot",
#         "classroom__name",
#         "faculty__name",
#         "phd_scholar__name",
#     )

#     return render(
#         request,
#         "allocation/allocation_result.html",
#         {"allocations": allocations, "exam": exam, "seating_allocations": seating},
#     )


# def allocation_table(request):
#     allocations = (
#         DutyAllocation.objects.select_related(
#             "exam", "classroom", "faculty", "phd_scholar"
#         )
#         .order_by(
#             "exam__date",
#             "exam__time_slot",
#             "classroom__name",
#             "faculty__name",
#             "phd_scholar__name",
#         )
#     )
#     return render(
#         request,
#         "allocation/allocation_table.html",
#         {"allocations": allocations},
#     )


# def seating_plan(request):
#     seating = SeatingAllocation.objects.select_related("exam", "classroom").order_by(
#         "exam__date",
#         "exam__time_slot",
#         "classroom__name",
#         "start_roll",
#     )
#     return render(
#         request,
#         "allocation/seating_plan.html",
#         {"seating_allocations": seating},
#     )


# def ufm_history(request):
#     records = (
#         UFMRecord.objects.select_related("exam", "faculty", "phd_scholar")
#         .order_by("-exam__date", "-last_updated")
#     )
#     return render(
#         request,
#         "allocation/ufm_history.html",
#         {"records": records},
#     )


# def export_allocations_csv(request):
#     exam_id = request.GET.get("exam_id")
#     allocations = DutyAllocation.objects.select_related(
#         "exam", "classroom", "faculty", "phd_scholar"
#     )
#     if exam_id:
#         allocations = allocations.filter(exam_id=exam_id)

#     allocations = allocations.order_by(
#         "exam__date",
#         "exam__time_slot",
#         "classroom__name",
#         "faculty__name",
#         "phd_scholar__name",
#     )

#     response = HttpResponse(content_type="text/csv")
#     filename = "duty_allocations.csv"
#     if exam_id:
#         filename = f"duty_allocations_exam_{exam_id}.csv"
#     response["Content-Disposition"] = f'attachment; filename="{filename}"'

#     writer = csv.writer(response)
#     writer.writerow(
#         [
#             "Serial Number",
#             "Faculty Name",
#             "Designation",
#             "Date",
#             "Time Slot",
#             "Room Number",
#         ]
#     )

#     for idx, alloc in enumerate(allocations, start=1):
#         person = alloc.faculty or alloc.phd_scholar
#         if alloc.faculty:
#             designation = alloc.faculty.get_designation_display()
#         else:
#             designation = "PhD Scholar"

#         writer.writerow(
#             [
#                 idx,
#                 getattr(person, "name", ""),
#                 designation,
#                 alloc.exam.date,
#                 alloc.exam.get_time_slot_display(),
#                 alloc.classroom.name,
#             ]
#         )

#     return response

from __future__ import annotations
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

import csv

from .forms import (
    AllocationRunForm,
    ClassroomForm,
    ExamScheduleForm,
    FacultyForm,
    PhD_ScholarForm,
)
from .models import Classroom, DutyAllocation, ExamSchedule, Faculty, PhD_Scholar, SeatingAllocation, UFMRecord
from .services import allocate_duties_for_exam


def dashboard(request):
    context = {
        "faculty_count": Faculty.objects.count(),
        "phd_count": PhD_Scholar.objects.count(),
        "classroom_count": Classroom.objects.count(),
        "exam_count": ExamSchedule.objects.count(),
    }
    return render(request, "allocation/dashboard.html", context)



from django.contrib.auth.decorators import login_required
from .models import DutyAllocation, PhD_Scholar


# @login_required(login_url="/login/")
# def phd_timetable(request):

#     try:
#         phd = PhD_Scholar.objects.get(user=request.user)
#     except PhD_Scholar.DoesNotExist:
#         return render(request, "allocation/phd_timetable.html", {"allocations": []})

#     allocations = DutyAllocation.objects.select_related(
#         "exam", "classroom"
#     ).filter(
#         phd_scholar=phd
#     ).order_by(
#         "exam__date", "exam__time_slot"
#     )

#     return render(
#         request,
#         "allocation/phd_timetable.html",
#         {"allocations": allocations}
#     )

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

    faculty = Faculty.objects.all().order_by("name")
    return render(request, "allocation/faculty_list.html", {"form": form, "faculty_list": faculty})






@login_required(login_url="/login/")
def phd_list_create(request):
    if request.method == "POST":
        form = PhD_ScholarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "PhD Scholar added successfully.")
            return redirect("allocation:phd_list")
    else:
        form = PhD_ScholarForm()

    phd_list = PhD_Scholar.objects.all().order_by("name")
    return render(request, "allocation/phd_list.html", {"form": form, "phd_list": phd_list})


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
    return render(request, "allocation/classroom_list.html", {"form": form, "classroom_list": classrooms})


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
    return render(request, "allocation/exam_list.html", {"form": form, "exam_list": exams})


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
                    f"Created {len(result.created_allocations)} duty records for exam {exam}.",
                )

            for warning in result.capacity_warnings:
                messages.warning(request, warning)

            for alert in result.detained_alerts:
                messages.info(request, alert)

            return redirect(reverse("allocation:allocation_result") + f"?exam_id={exam.id}")
    else:
        form = AllocationRunForm()

    return render(request, "allocation/run_allocation.html", {"form": form})


@login_required(login_url="/login/")
def allocation_result(request):
    exam_id = request.GET.get("exam_id")

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "faculty", "phd_scholar"
    )

    exam = None
    seating = SeatingAllocation.objects.none()

    if exam_id:
        allocations = allocations.filter(exam_id=exam_id)
        exam = ExamSchedule.objects.filter(id=exam_id).first()
        seating = SeatingAllocation.objects.filter(exam_id=exam_id).order_by(
            "classroom__name", "start_roll"
        )

    allocations = allocations.order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "faculty__name",
        "phd_scholar__name",
    )

    return render(
        request,
        "allocation/allocation_result.html",
        {"allocations": allocations, "exam": exam, "seating_allocations": seating},
    )


@login_required(login_url="/login/")
def allocation_table(request):
    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "faculty", "phd_scholar"
    ).order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "faculty__name",
        "phd_scholar__name",
    )

    return render(request, "allocation/allocation_table.html", {"allocations": allocations})


@login_required(login_url="/login/")
def seating_plan(request):
    seating = SeatingAllocation.objects.select_related("exam", "classroom").order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "start_roll",
    )

    return render(request, "allocation/seating_plan.html", {"seating_allocations": seating})


@login_required(login_url="/login/")
def ufm_history(request):
    records = UFMRecord.objects.select_related("exam", "faculty", "phd_scholar").order_by(
        "-exam__date", "-last_updated"
    )

    return render(request, "allocation/ufm_history.html", {"records": records})


@login_required(login_url="/login/")
def export_allocations_csv(request):
    exam_id = request.GET.get("exam_id")

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom", "faculty", "phd_scholar"
    )

    if exam_id:
        allocations = allocations.filter(exam_id=exam_id)

    allocations = allocations.order_by(
        "exam__date",
        "exam__time_slot",
        "classroom__name",
        "faculty__name",
        "phd_scholar__name",
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="duty_allocations.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Serial Number",
            "Faculty Name",
            "Designation",
            "Date",
            "Time Slot",
            "Room Number",
        ]
    )

    for idx, alloc in enumerate(allocations, start=1):
        person = alloc.faculty or alloc.phd_scholar

        if alloc.faculty:
            designation = alloc.faculty.get_designation_display()
        else:
            designation = "PhD Scholar"

        writer.writerow(
            [
                idx,
                getattr(person, "name", ""),
                designation,
                alloc.exam.date,
                alloc.exam.get_time_slot_display(),
                alloc.classroom.name,
            ]
        )

    return response




from django.shortcuts import redirect

@login_required
def redirect_dashboard(request):

    if request.user.is_superuser:
        return redirect("allocation:dashboard")

    if Faculty.objects.filter(user=request.user).exists():
        return redirect("allocation:faculty_timetable")

    if PhD_Scholar.objects.filter(user=request.user).exists():
        return redirect("allocation:phd_timetable")

    return redirect("login")

@login_required(login_url="/login/")
def phd_timetable(request):

    try:
        phd = PhD_Scholar.objects.get(user=request.user)
    except PhD_Scholar.DoesNotExist:
        return render(request, "allocation/phd_timetable.html", {"allocations": []})

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom"
    ).filter(
        phd_scholar=phd
    ).order_by(
        "exam__date", "exam__time_slot"
    )

    return render(
        request,
        "allocation/phd_timetable.html",
        {"allocations": allocations}
    )

from django.contrib.auth.decorators import login_required
from .models import Faculty, DutyAllocation

@login_required(login_url="/login/")
def faculty_timetable(request):

    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        return render(request, "allocation/faculty_timetable.html", {"allocations": []})

    allocations = DutyAllocation.objects.select_related(
        "exam", "classroom"
    ).filter(
        faculty=faculty
    ).order_by(
        "exam__date", "exam__time_slot"
    )

    return render(
        request,
        "allocation/faculty_timetable.html",
        {"allocations": allocations}
    )

from django.core.exceptions import ValidationError

def validate_before_5pm(value):
    if value.hour >= 17:
        raise ValidationError("Time must be before 5 PM")

# class Slot(models.Model):
#     time = models.TimeField(validators=[validate_before_5pm])




