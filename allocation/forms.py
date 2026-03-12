from django import forms

from .models import Classroom, ExamSchedule, Faculty, PhD_Scholar, TimeSlot
from django import forms
from .models import Faculty

class FacultyForm(forms.ModelForm):

    class Meta:
        model = Faculty
        fields = [
            "name",
            "email",
            "designation",
            "department",
            "duty_quota"
        ]

# class FacultyForm(forms.ModelForm):
#     class Meta:
#         model = Faculty
#         fields = ["name", "email", "designation", "duty_quota"]


class PhD_ScholarForm(forms.ModelForm):
    class Meta:
        model = PhD_Scholar
        fields = ["name", "email", "max_duties"]


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "capacity"]


class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = [
            "course_name",
            "date",
            "time_slot",
            "start_time",
            "end_time",
            "expected_students",
            "classrooms",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "classrooms": forms.CheckboxSelectMultiple(),
        }


class AllocationRunForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=ExamSchedule.objects.all().order_by("date", "time_slot"),
        label="Select exam",
    )

