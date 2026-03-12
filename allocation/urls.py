from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "allocation"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("faculty/", views.faculty_list_create, name="faculty_list"),
    path("phd/", views.phd_list_create, name="phd_list"),
    path("classrooms/", views.classroom_list_create, name="classroom_list"),
    path("exams/", views.exam_list_create, name="exam_list"),
    path("run-allocation/", views.run_allocation, name="run_allocation"),
    path("allocation-result/", views.allocation_result, name="allocation_result"),
    path("allocation-table/", views.allocation_table, name="allocation_table"),
    path("seating-plan/", views.seating_plan, name="seating_plan"),
    path("ufm-history/", views.ufm_history, name="ufm_history"),
    path("export-csv/", views.export_allocations_csv, name="export_allocations_csv"),
    path("phd-timetable/", views.phd_timetable, name="phd_timetable"),
    path(
    "login/",
    auth_views.LoginView.as_view(template_name="registration/login.html"),
    name="login",
),
]

