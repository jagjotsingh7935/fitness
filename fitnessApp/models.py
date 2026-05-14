from django.db import models

# Create your models here.
from accounts.models import *

class Exercise(models.Model):
    """Master table of exercises (videos) created by Admin."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to='exercise_videos/', help_text="Upload MP4 video")
    categories = models.ManyToManyField(Category, related_name='exercises', blank=True)
    duration_seconds = models.PositiveIntegerField(help_text="Duration in seconds", default=0)
    thumbnail = models.ImageField(upload_to='exercise_thumbnails/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        permissions = [
            ("can_view_exercise", "Can view exercise"),
            ("create_exercise", "Can create exercise"),
            ("update_exercise", "Can update exercise"),
            ("can_delete_exercise", "Can delete exercise"),
        ]

    def __str__(self):
        return self.title


class ClientWorkoutPlan(models.Model):
    """Workout plan assigned by a trainer to a specific client, per day."""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='created_workouts')
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='workout_plans')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='workout_plans')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    sets = models.PositiveSmallIntegerField(default=1)
    reps = models.PositiveSmallIntegerField(default=1)
    time_per_rep_seconds = models.PositiveSmallIntegerField(default=15, help_text="Seconds per repetition")
    order = models.PositiveSmallIntegerField(default=0, help_text="Order of exercise within the same day")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['client', 'day_of_week', 'order']
        unique_together = ['trainer', 'client', 'day_of_week', 'exercise', 'order']
        permissions = [
            ("can_view_workout_plan", "Can view workout plan"),
            ("create_workout_plan", "Can create workout plan"),
            ("update_workout_plan", "Can update workout plan"),
            ("can_delete_workout_plan", "Can delete workout plan"),
        ]

    def __str__(self):
        return f"{self.client.user.email} - {self.get_day_of_week_display()} - {self.exercise.title}"




class DailyKcalTarget(models.Model):
    """Target kcal to burn per day of week for a client. Created by admin/trainer."""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='kcal_targets')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    target_kcal = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_kcal_targets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'day_of_week']
        verbose_name = "Daily Kcal Target"
        verbose_name_plural = "Daily Kcal Targets"
        permissions = [
            ("can_view_kcaltarget", "Can view kcal target"),
            ("create_kcaltarget", "Can create kcal target"),
            ("update_kcaltarget", "Can update kcal target"),
            ("can_delete_kcaltarget", "Can delete kcal target"),
        ]

    def __str__(self):
        return f"{self.client.user.email} - {self.get_day_of_week_display()}: {self.target_kcal} kcal"


class ClientKcalLog(models.Model):
    """Actual kcal burned by client on a specific date."""
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='kcal_logs')
    date = models.DateField()
    actual_kcal = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'date']
        ordering = ['-date']
        verbose_name = "Client Kcal Log"
        verbose_name_plural = "Client Kcal Logs"
        permissions = [
            ("can_view_kcallog", "Can view kcal log"),
            ("create_kcallog", "Can create kcal log"),
            ("update_kcallog", "Can update kcal log"),
            ("can_delete_kcallog", "Can delete kcal log"),
        ]

    def __str__(self):
        return f"{self.client.user.email} - {self.date}: {self.actual_kcal} kcal"






# ---------- Hydration ----------
class DailyHydrationTarget(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='hydration_targets')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    target_cups = models.PositiveSmallIntegerField(help_text="Number of cups (glass) of water")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_hydration_targets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'day_of_week']

    def __str__(self):
        return f"{self.client.user.email} - {self.get_day_of_week_display()}: {self.target_cups} cups"


class ClientHydrationLog(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='hydration_logs')
    date = models.DateField()
    actual_cups = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'date']
        ordering = ['-date']


# ---------- Sleep ----------
class DailySleepTarget(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='sleep_targets')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    target_hours = models.DecimalField(max_digits=3, decimal_places=1, help_text="Hours of sleep (e.g., 7.5)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sleep_targets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'day_of_week']

    def __str__(self):
        return f"{self.client.user.email} - {self.get_day_of_week_display()}: {self.target_hours} hrs"


class ClientSleepLog(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='sleep_logs')
    date = models.DateField()
    actual_hours = models.DecimalField(max_digits=3, decimal_places=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'date']
        ordering = ['-date']