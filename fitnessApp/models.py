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
    master_plan = models.ForeignKey(
        'fitnessApp.MasterWorkoutPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_workout_plans',
        help_text="Master workout plan this entry was assigned from, if any"
    )
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


class MasterWorkoutPlan(models.Model):
    """Master workout program template created by trainer or admin."""
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='master_workout_plans',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name='master_workout_plans', blank=True)
    assigned_clients = models.ManyToManyField(
        ClientProfile,
        related_name='assigned_master_plans',
        blank=True,
        help_text="Clients currently assigned to this master program"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Master Workout Plan"
        verbose_name_plural = "Master Workout Plans"

    def __str__(self):
        return self.title


class MasterWorkoutPlanItem(models.Model):
    """Scheduled exercise item within a Master Workout Plan."""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    master_plan = models.ForeignKey(MasterWorkoutPlan, on_delete=models.CASCADE, related_name='items')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='master_plan_items')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    sets = models.PositiveSmallIntegerField(default=3)
    reps = models.PositiveSmallIntegerField(default=12)
    time_per_rep_seconds = models.PositiveSmallIntegerField(default=15, help_text="Seconds per repetition")
    order = models.PositiveSmallIntegerField(default=0, help_text="Order within the day")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'order']
        verbose_name = "Master Plan Item"
        verbose_name_plural = "Master Plan Items"

    def __str__(self):
        return f"{self.master_plan.title} - {self.get_day_of_week_display()} - {self.exercise.title}"





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


# ---------- Client Streak & Gamification ----------
class ClientStreak(models.Model):
    """Tracks consecutive active days and check-in streak for a client."""
    client = models.OneToOneField(ClientProfile, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=1)
    longest_streak = models.PositiveIntegerField(default=1)
    last_activity_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Streak"
        verbose_name_plural = "Client Streaks"

    def __str__(self):
        return f"{self.client.user.email} - Streak: {self.current_streak} (Best: {self.longest_streak})"


class ClientAchievement(models.Model):
    """Unlocked badges and milestones earned by a client."""
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='achievements')
    badge_key = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ['client', 'badge_key']
        ordering = ['-unlocked_at']
        verbose_name = "Client Achievement"
        verbose_name_plural = "Client Achievements"

    def __str__(self):
        return f"{self.client.user.email} - {self.emoji} {self.name}"


# ---------- Client Diet & Nutrition Models ----------
class ClientDietPlan(models.Model):
    """Diet plan assigned to a client by Admin or Trainer."""
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='diet_plans')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_diet_plans')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_diet_plans')
    title = models.CharField(max_length=200, default="Personalized Nutrition Plan")
    daily_calorie_target = models.PositiveIntegerField(default=2000)
    protein_grams = models.PositiveIntegerField(default=140)
    carbs_grams = models.PositiveIntegerField(default=220)
    fat_grams = models.PositiveIntegerField(default=65)
    notes = models.TextField(blank=True, help_text="Special coach instructions, hydration guidelines, foods to avoid")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Client Diet Plan"
        verbose_name_plural = "Client Diet Plans"

    def __str__(self):
        return f"{self.client.user.email} - {self.title} ({self.daily_calorie_target} kcal)"


class ClientDietMealItem(models.Model):
    """Scheduled meals within a diet plan."""
    MEAL_TYPES = [
        ('BREAKFAST', 'Breakfast'),
        ('MID_MORNING', 'Mid-Morning Snack'),
        ('LUNCH', 'Lunch'),
        ('EVENING_SNACK', 'Evening Snack'),
        ('DINNER', 'Dinner'),
        ('POST_WORKOUT', 'Post-Workout Fuel'),
    ]

    diet_plan = models.ForeignKey(ClientDietPlan, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='BREAKFAST')
    name = models.CharField(max_length=255, help_text="Meal description, e.g. Oatmeal with Whey & Banana")
    time_label = models.CharField(max_length=50, blank=True, help_text="e.g. 7:30 AM")
    calories = models.PositiveIntegerField(default=350)
    protein_grams = models.PositiveIntegerField(default=0, blank=True, null=True)
    carbs_grams = models.PositiveIntegerField(default=0, blank=True, null=True)
    fat_grams = models.PositiveIntegerField(default=0, blank=True, null=True)
    custom_emoji = models.CharField(max_length=10, blank=True, help_text="Optional custom emoji")
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    @property
    def emoji(self):
        if self.custom_emoji:
            return self.custom_emoji
        defaults = {
            'BREAKFAST': '🌅',
            'MID_MORNING': '🍎',
            'LUNCH': '🥗',
            'EVENING_SNACK': '🥜',
            'DINNER': '🍽️',
            'POST_WORKOUT': '⚡',
        }
        return defaults.get(self.meal_type, '🍽️')

    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.name}"


class ClientMealLog(models.Model):
    """Tracks if client ate/checked off the meal on a given date."""
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='meal_logs')
    meal_item = models.ForeignKey(ClientDietMealItem, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    is_completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['client', 'meal_item', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.client.user.email} - {self.meal_item.name} on {self.date}: {self.is_completed}"




# ---------- Auto-generate Exercise Thumbnail & Duration Signal ----------
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import os

@receiver(post_save, sender=Exercise)
def auto_generate_exercise_thumbnail(sender, instance, created, **kwargs):
    """Automatically extracts frame and calculates duration for newly uploaded exercise videos."""
    if instance.video and not instance.thumbnail:
        try:
            import cv2
            video_path = instance.video.path if hasattr(instance.video, 'path') else os.path.join(settings.MEDIA_ROOT, str(instance.video))
            if os.path.exists(video_path):
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                    duration = int(total_frames / fps) if fps > 0 else 0

                    target_frame = min(int(fps * 1.0), max(0, total_frames // 4))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                    cap.release()

                    if ret and frame is not None:
                        thumb_dir = os.path.join(settings.MEDIA_ROOT, 'exercise_thumbnails')
                        os.makedirs(thumb_dir, exist_ok=True)
                        thumb_filename = f'exercise_{instance.id}.jpg'
                        thumb_path = os.path.join(thumb_dir, thumb_filename)
                        cv2.imwrite(thumb_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])

                        rel_path = f'exercise_thumbnails/{thumb_filename}'
                        update_fields = {'thumbnail': rel_path}
                        if duration > 0 and instance.duration_seconds == 0:
                            update_fields['duration_seconds'] = duration
                        Exercise.objects.filter(pk=instance.pk).update(**update_fields)
        except Exception as e:
            print(f"[WARN] Error auto-generating thumbnail for Exercise #{instance.id}: {e}")