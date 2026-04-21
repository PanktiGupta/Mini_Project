from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "allocation"

urlpatterns =[
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",                                         
        auth_views.LogoutView.as_view(next_page="/login/"),
        name="logout",
    ),
    path("", views.dashboard, name="dashboard"),
    path("redirect/", views.redirect_dashboard, name="redirect_dashboard"),
    path("faculty/",                views.faculty_list_create, name="faculty_list"),
    path("faculty/<int:pk>/edit/",  views.faculty_edit,        name="faculty_edit"),    
    path("faculty/<int:pk>/delete/",views.faculty_delete,      name="faculty_delete"),  

    path("phd/",                views.phd_list_create, name="phd_list"),
    path("phd/<int:pk>/edit/",  views.phd_edit,        name="phd_edit"),        
    path("phd/<int:pk>/delete/",views.phd_delete,      name="phd_delete"),
    path("classrooms/",                views.classroom_list_create, name="classroom_list"),
    path("classrooms/<int:pk>/edit/",  views.classroom_edit,        name="classroom_edit"),  
    path("classrooms/<int:pk>/delete/",views.classroom_delete,      name="classroom_delete"), 

    path("exams/",                views.exam_list_create, name="exam_list"),
    path("exams/<int:pk>/edit/",  views.exam_edit,        name="exam_edit"),    
    path("exams/<int:pk>/delete/",views.exam_delete,      name="exam_delete"),  

    path("run-allocation/",  views.run_allocation,  name="run_allocation"),
    path("allocation-table/",views.allocation_table,name="allocation_table"),   
    
    path("seating/", views.seating_plan, name="seating_plan"),
    
    path("change-password/", views.change_password, name="change_password"), 

    path("export-csv/",      views.export_allocations_csv, name="export_allocations_csv"),

    

    path("ufm-history/", views.ufm_history, name="ufm_history"),
    
    path("my-timetable/faculty/", views.faculty_timetable, name="faculty_timetable"), 
    path("my-timetable/phd/",     views.phd_timetable,     name="phd_timetable"),
    
    path(
        "resend-emails/<int:exam_id>/",
        views.resend_allocation_emails,
        name="resend_allocation_emails"
    ),
]