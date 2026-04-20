from django import forms
from django.contrib.auth.models import User
from .models import Classroom, ExamSchedule, Faculty, PhDScholar
from django.utils import timezone



class UserFieldsMixin:
    """
       Reusable mixin to avoid repeating user field logic
       in both FacultyForm and PhDScholarForm
    """
    def get_user_fields(self):
        return {
            "first_name": forms.CharField(
                max_length=150,
                widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"})
            ),
            "last_name": forms.CharField(
                max_length=150,
                required=False,
                widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"})
            ),
            "email": forms.EmailField(
                widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
            ),
        }

    def clean_email(self):
        """✅ Validate email is unique per user (skip current user on edit)"""
        email = self.cleaned_data.get("email")
        instance = getattr(self, "instance", None)

        # get current user_id if editing
        user_id = getattr(instance, "user_id", None)

        qs = User.objects.filter(email=email)
        if user_id:
            qs = qs.exclude(pk=user_id)     # ✅ exclude self on update

        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def _save_user(self, obj):
        """ Create or update user from cleaned data"""
        if not obj.user_id:
            
            user = User.objects.create_user(    
                username=self.cleaned_data["email"],
                email=self.cleaned_data["email"],
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data.get("last_name", ""),
            )
            obj.user = user
        else:
            self._update_user(obj)

        return obj

    def _update_user(self, obj):
        user = obj.user
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data.get("last_name", "")
        user.save()
class FacultyForm(UserFieldsMixin, forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )

    class Meta:
        model  = Faculty
        fields = ["designation", "department", "duty_quota", "is_active"]
        widgets = {
            "designation": forms.Select(attrs={"class": "form-select"}),
            "department":  forms.TextInput(attrs={"class": "form-control", "placeholder": "Department"}),
            "duty_quota":  forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active":   forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial  = self.instance.user.last_name
            self.fields["email"].initial      = self.instance.user.email

    def save(self, commit=True):
        faculty = super().save(commit=False)
        faculty = self._save_user(faculty)  
        if commit:
            faculty.save()
        return faculty

class PhDScholarForm(UserFieldsMixin, forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )

    class Meta:
        model  = PhDScholar
        fields = ["max_duties", "is_active"]
        widgets = {
            "max_duties": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active":  forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial  = self.instance.user.last_name
            self.fields["email"].initial      = self.instance.user.email

    def save(self, commit=True):
        scholar = super().save(commit=False)
        scholar = self._save_user(scholar) 
        if commit:
            scholar.save()
        return scholar

class ClassroomForm(forms.ModelForm):
    class Meta:
        model  = Classroom
        fields = ["name", "capacity", "is_available"]
        widgets = {
            "name":         forms.TextInput(attrs={"class": "form-control", "placeholder": "Room Name e.g. Room 101"}),
            "capacity":     forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
class ExamScheduleForm(forms.ModelForm):
    class Meta:
            model  = ExamSchedule
            fields = [
                "course_name",
                "course_code",
                "date",
                "time_slot",
                "start_time",
                "end_time",
                "expected_students",
                "classrooms",
                "notes",
            ]
            widgets = {
                "course_name":       forms.TextInput(attrs={"class": "form-control", "placeholder": "Course Name"}),
                "course_code":       forms.TextInput(attrs={"class": "form-control", "placeholder": "Course Code e.g. CS101"}),
                "date":              forms.DateInput(attrs={"class": "form-control", "type": "date"}),
                "time_slot":         forms.Select(attrs={"class": "form-select"}),
                "start_time":        forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
                "end_time":          forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
                "expected_students": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
                "classrooms":        forms.CheckboxSelectMultiple(),
                "notes":             forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes"}),
            }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end   = cleaned_data.get("end_time")
        date  = cleaned_data.get("date")

        if start and end and end <= start:
            self.add_error("end_time", "End time must be after start time.")

        if date and not self.instance.pk and date < timezone.now().date():
            self.add_error("date", "Exam date cannot be in the past.")

        return cleaned_data


class AllocationRunForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=ExamSchedule.objects.all().order_by("date", "time_slot"),
        label="Select Exam",
        empty_label="-- Select Exam --",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

