from django.db import models
from django.utils import timezone


class Designation(models.TextChoices):
    PROFESSOR = "PROF", "Professor"
    ASSOCIATE_PROFESSOR = "ASSOC", "Associate Professor"
    ASSISTANT_PROFESSOR = "ASST", "Assistant Professor"
from django.contrib.auth.models import User

# class PhD_Scholar(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     max_duties = models.IntegerField(default=0)

#     def __str__(self):
#         return self.name
from django.contrib.auth.models import User

class Faculty(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    email = models.EmailField()

    designation = models.CharField(
        max_length=50,
        choices=Designation.choices,
        default=Designation.ASSISTANT_PROFESSOR
    )

    duty_quota = models.IntegerField(default=5)

    department = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    # class Meta():

        
class PhD_Scholar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    max_duties = models.IntegerField(default=3)

    def __str__(self):
        return self.name

# class Faculty(models.Model):
#     name = models.CharField(max_length=255)
#     email = models.EmailField(blank=True)
#     designation = models.CharField(
#         max_length=5,
#         choices=Designation.choices,
#         default=Designation.ASSISTANT_PROFESSOR,
#     )
#     duty_quota = models.PositiveIntegerField(default=0)

#     def __str__(self) -> str:
#         designation_label = dict(Designation.choices).get(self.designation, self.designation)
#         return f"{self.name} ({designation_label})"


# class PhDScholar(models.Model):
#     name = models.CharField(max_length=255)
#     email = models.EmailField(blank=True)
#     max_duties = models.PositiveIntegerField(default=0)

#     def __str__(self) -> str:
#         return self.name


class Classroom(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.name} (Cap: {self.capacity})"


class TimeSlot(models.TextChoices):
    MORNING = "MORNING", "Morning"
    EVENING = "EVENING", "Evening"


class ExamSchedule(models.Model):
    course_name = models.CharField(max_length=255)
    date = models.DateField()
    time_slot = models.CharField(max_length=10, choices=TimeSlot.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_students = models.PositiveIntegerField(default=0)
    classrooms = models.ManyToManyField(Classroom, related_name="exam_schedules")

    def __str__(self) -> str:
        return f"{self.course_name} - {self.date} ({self.time_slot})"

    @property
    def total_classroom_capacity(self) -> int:
        return sum(room.capacity for room in self.classrooms.all())


class SeatingAllocation(models.Model):
    exam = models.ForeignKey(
        ExamSchedule,
        on_delete=models.CASCADE,
        related_name="seating_allocations",
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="seating_allocations",
    )
    start_roll = models.PositiveIntegerField()
    end_roll = models.PositiveIntegerField()
    capacity_used = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return (
            f"{self.exam} - {self.classroom}: "
            f"{self.start_roll} to {self.end_roll}"
        )


class DutyAllocation(models.Model):
    exam = models.ForeignKey(
        ExamSchedule, on_delete=models.CASCADE, related_name="allocations"
    )
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="allocations"
    )
    faculty = models.ForeignKey(
        Faculty, null=True, blank=True, on_delete=models.SET_NULL, related_name="duties"
    )
    phd_scholar = models.ForeignKey(
        PhD_Scholar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="duties",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        person = self.faculty or self.phd_scholar
        return f"{person} - {self.exam} - {self.classroom}"


class UFMRecord(models.Model):
    exam = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE)
    faculty = models.ForeignKey(
        Faculty, null=True, blank=True, on_delete=models.SET_NULL
    )
    phd_scholar = models.ForeignKey(
        PhD_Scholar, null=True, blank=True, on_delete=models.SET_NULL
    )
    count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("exam", "faculty", "phd_scholar")

    def __str__(self) -> str:
        person = self.faculty or self.phd_scholar
        return f"UFM for {person} - {self.count}"

class Slot(models.Model):
    time_slot = models.CharField(
        max_length=20,
        choices=TimeSlot.choices
    )


    