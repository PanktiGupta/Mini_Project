from django.contrib import admin

from .models import (
    Classroom,
    DutyAllocation,
    ExamSchedule,
    Faculty,
    PhD_Scholar,
    SeatingAllocation,
    UFMRecord,
)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "designation", "duty_quota")
    list_filter = ("designation",)
    search_fields = ("name",)


# @admin.register(PhD_Scholar)
# class PhD_ScholarAdmin(admin.ModelAdmin):

#     list_display = ("name", "get_email", "max_duties")
#     search_fields = ("name",)

#     def get_email(self, obj):
#         return obj.user.email 

@admin.register(PhD_Scholar)
class PhD_ScholarAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "max_duties")
    search_fields = ("name", "email")




@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ("course_name", "date", "time_slot", "start_time", "end_time", "expected_students")
    list_filter = ("date", "time_slot")
    search_fields = ("course_name",)
    filter_horizontal = ("classrooms",)


@admin.register(DutyAllocation)
class DutyAllocationAdmin(admin.ModelAdmin):
    list_display = ("exam", "classroom", "faculty", "phd_scholar", "created_at")
    list_filter = ("exam__date", "exam__time_slot", "classroom")
    search_fields = ("faculty__name", "phd_scholar__name")


@admin.register(UFMRecord)
class UFMRecordAdmin(admin.ModelAdmin):
    list_display = ("exam", "faculty", "phd_scholar", "count", "last_updated")
    list_filter = ("exam__date",)
    search_fields = ("faculty__name", "phd_scholar__name")


@admin.register(SeatingAllocation)
class SeatingAllocationAdmin(admin.ModelAdmin):
    list_display = ("exam", "classroom", "start_roll", "end_roll", "capacity_used")
    list_filter = ("exam__date", "classroom")

