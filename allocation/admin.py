from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Classroom,
    DutyAllocation,
    ExamSchedule,
    Faculty,
    PhDScholar,
    SeatingAllocation,
    UFMRecord,
    Slot,
    Role,
)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display  = ("get_name", "get_email", "designation", "department", "duty_quota", "is_active")
    list_filter   = ("designation", "department", "is_active")
    search_fields = ("user__first_name", "user__last_name", "user__email", "department")
    list_editable = ("is_active",)                          
    ordering      = ("user__first_name",)

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = "Name"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"

    
@admin.register(PhDScholar)
class PhDScholarAdmin(admin.ModelAdmin):
    list_display = ("get_name", "get_email", "max_duties", "is_active")
    list_filter = ("max_duties", "is_active")
    search_fields = ("user__first_name", "user__last_name", "user__email")
    list_editable = ("is_active",)
    ordering = ("user__first_name",)

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = "Name"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"




@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name",)
    list_filter = ("is_available",)
    ordering = ("name",)


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ("course_name", "date", "time_slot", "start_time", "end_time", "expected_students", "get_capacity_status")
    list_filter = ("date", "time_slot")
    search_fields = ("course_name", "course_code")
    filter_horizontal = ("classrooms",)
    ordering = ("date", "start_time")
    date_hierarchy = "date"

    def get_capacity_status(self, obj):
        if obj.is_capacity_sufficient:
            return format_html('<span style="color: green;">Sufficient</span>')
        return format_html('<span style="color: red;">Insufficient</span>')
    get_capacity_status.short_description = "Capacity Status"


@admin.register(DutyAllocation)
class DutyAllocationAdmin(admin.ModelAdmin):
    list_display  = ("exam", "classroom", "get_assigned_to", "role", "is_confirmed", "created_at")
    list_filter   = ("exam__date", "exam__time_slot", "classroom", "role", "is_confirmed")
    search_fields = ("assigned_to__first_name", "assigned_to__last_name", "assigned_to__email")
    list_editable = ("is_confirmed",)                       
    ordering      = ("exam", "classroom")

    def get_assigned_to(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username
    get_assigned_to.short_description = "Assigned To"



@admin.register(UFMRecord)
class UFMRecordAdmin(admin.ModelAdmin):
    list_display  = ("exam", "get_user", "get_role", "count", "last_updated")
    list_filter   = ("exam__date",)
    search_fields = ("user__first_name", "user__last_name", "user__email")
    readonly_fields = ("last_updated",)                    
    ordering      = ("-last_updated",)

    def get_user(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_user.short_description = "User"

    def get_role(self, obj):
        if hasattr(obj.user, "faculty"):
            return "Faculty"
        return "PhD Scholar" if hasattr(obj.user, "phdscholar") else "Unknown"
    get_role.short_description = "Role"



@admin.register(SeatingAllocation)
class SeatingAllocationAdmin(admin.ModelAdmin):
    list_display  = ("exam", "classroom", "start_roll", "end_roll", "capacity_used", "created_at")
    list_filter   = ("exam__date", "classroom")
    search_fields = ("exam__course_name", "classroom__name")
    readonly_fields = ("created_at",)                       
    ordering      = ("exam", "classroom")



@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display  = ("time_slot",)
    list_filter   = ("time_slot",)