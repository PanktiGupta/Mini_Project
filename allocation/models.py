
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    class Meta:
        abstract = True


class Designation(models.TextChoices):
    PROFESSOR = "PROF", "Professor"
    ASSOCIATE_PROFESSOR = "ASSOC", "Associate Professor"
    ASSISTANT_PROFESSOR = "ASST", "Assistant Professor"


class TimeSlot(models.TextChoices):
    MORNING = "MORNING", "Morning"
    EVENING = "EVENING", "Evening"
 

class Role(models.TextChoices):
    FACULTY = "FACULTY", "Faculty"
    PHD = "PHD", "PhD Scholar"

class Faculty(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="faculty")

    designation = models.CharField(
        max_length=50,
        choices=Designation.choices,
        default=Designation.ASSISTANT_PROFESSOR
    )
    department = models.CharField(max_length=100)
    duty_quota = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculty Members"
        ordering = ["user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        return self.user.email
    

        
class PhDScholar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="phdscholar")


    max_duties = models.IntegerField(default=3, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)
    class Meta:
        verbose_name = "PhD Scholar"
        verbose_name_plural = "PhD Scholars"
        ordering = ["user__first_name"]

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        return self.user.email
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username




class Classroom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField(    
        validators=[MinValueValidator(1)]                  
    )
    is_available = models.BooleanField(default=True)        

    class Meta:
        verbose_name = "Classroom"
        verbose_name_plural = "Classrooms"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} (Cap: {self.capacity})"




class ExamSchedule(models.Model):
    course_name       = models.CharField(max_length=255)
    course_code       = models.CharField(max_length=20, blank=True)  
    date              = models.DateField()
    time_slot         = models.CharField(max_length=10, choices=TimeSlot.choices)
    start_time        = models.TimeField()
    end_time          = models.TimeField()
    expected_students = models.PositiveIntegerField(default=0)
    classrooms        = models.ManyToManyField(
        Classroom,
        related_name="exam_schedules",
        blank=True
    )
    notes = models.TextField(blank=True)        

    class Meta:
        verbose_name = "Exam Schedule"
        verbose_name_plural = "Exam Schedules"
        ordering = ["date", "start_time"]                  
        unique_together = ("course_name", "date", "time_slot") 
    def __str__(self) -> str:
        return f"{self.course_name} - {self.date} ({self.time_slot})"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

        
        if self.date and self.date < timezone.now().date():
            raise ValidationError("Exam date cannot be in the past.")

    @property
    def total_classroom_capacity(self):
        return sum(room.capacity for room in self.classrooms.all())

    @property
    def is_capacity_sufficient(self):                       
        return self.total_classroom_capacity >= self.expected_students

class SeatingAllocation(TimeStampedModel):
    exam = models.ForeignKey(
        ExamSchedule,
        on_delete=models.CASCADE,
        related_name="seating_allocations"
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="seating_allocations"
    )
    start_roll = models.PositiveIntegerField()
    end_roll = models.PositiveIntegerField()
    capacity_used = models.PositiveIntegerField()
    

    class Meta:
        verbose_name = "Seating Allocation"
        verbose_name_plural = "Seating Allocations"
        ordering = ["exam", "classroom"]
        unique_together = ("exam", "classroom")
    def clean(self):
  
        if self.start_roll and self.end_roll and self.start_roll > self.end_roll:
            raise ValidationError("Start roll cannot be greater than end roll.")

    
        if self.capacity_used and self.classroom_id and self.capacity_used > self.classroom.capacity:
            raise ValidationError("Capacity used exceeds classroom capacity.")

def __str__(self):
    return f"{self.exam} | {self.classroom} | Roll {self.start_roll}-{self.end_roll}"





class DutyAllocation(TimeStampedModel):
    exam = models.ForeignKey(
        ExamSchedule,
        on_delete=models.CASCADE,
        related_name="duty_allocations"
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="duty_allocations"
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="duties",
        null = True
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,                              
        default=Role.FACULTY
    )
    is_confirmed = models.BooleanField(default=False)   

    class Meta:
        verbose_name = "Duty Allocation"
        verbose_name_plural = "Duty Allocations"
        ordering = ["exam", "classroom"]
        unique_together = ("exam", "classroom", "assigned_to")  
    
    def clean(self):
    
        if self.role == Role.FACULTY and not hasattr(self.assigned_to, "faculty"):
            raise ValidationError("Assigned user is not a Faculty member.")

        if self.role == Role.PHD and not hasattr(self.assigned_to, "phdscholar"):
            raise ValidationError("Assigned user is not a PhD Scholar.")
    def __str__(self):
        return f"{self.assigned_to} | {self.role} | {self.exam} | {self.classroom}"


class UFMRecord(models.Model):
    exam = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name="ufm_records")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ufm_records"
    )

    count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "UFM Record"
        verbose_name_plural = "UFM Records"
        unique_together = ("exam", "user")
        ordering = ["-last_updated"]

    def __str__(self):
        return f"UFM: {self.user} - {self.exam} (Count: {self.count})"



class Slot(models.Model):
    time_slot = models.CharField(
        max_length=20,
        choices=TimeSlot.choices
    )

    def __str__(self):
        return self.time_slot