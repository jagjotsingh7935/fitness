import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Category, TrainerProfile, ClientProfile, TrainerClientLink, BMI, FatPercent
from fitnessApp.models import (
    Exercise, ClientWorkoutPlan, DailyKcalTarget, ClientKcalLog,
    DailyHydrationTarget, ClientHydrationLog, DailySleepTarget, ClientSleepLog
)

User = get_user_model()

print("--- Starting Demo Data Seeding ---")

# 1. Create or ensure Categories exist
cat_data = [
    ("Weight Loss", "Focus on burning fat, increasing metabolism and cardio conditioning."),
    ("Muscle Building", "Hypertrophy, strength lifting, and progressive resistance training."),
    ("Endurance", "Stamina building, HIIT, high-volume conditioning."),
    ("Flexibility", "Mobility, joint recovery, yoga, and dynamic stretching."),
]

categories = []
for name, desc in cat_data:
    cat, created = Category.objects.get_or_create(
        name=name,
        defaults={'description': desc, 'is_active': True}
    )
    categories.append(cat)
    print(f"Category: {cat.name} (Created: {created})")

# 2. Create Admin Account
admin_email = "admin@fitness.com"
admin_pass = "Admin@123456"
admin_user, created = User.objects.get_or_create(
    email=admin_email,
    defaults={
        'username': admin_email,
        'first_name': 'Admin',
        'last_name': 'Director',
        'is_admin': True,
        'is_staff': True,
        'is_superuser': True,
    }
)
admin_user.set_password(admin_pass)
admin_user.is_admin = True
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.save()
print(f"Admin User: {admin_user.email} (Password: {admin_pass})")

# 3. Create Trainer Account
trainer_email = "trainer@fitness.com"
trainer_pass = "Trainer@123456"
trainer_user, created = User.objects.get_or_create(
    email=trainer_email,
    defaults={
        'username': trainer_email,
        'first_name': 'Marcus',
        'last_name': 'Vance',
        'is_trainer': True,
    }
)
trainer_user.set_password(trainer_pass)
trainer_user.is_trainer = True
trainer_user.first_name = 'Marcus'
trainer_user.last_name = 'Vance'
trainer_user.save()

trainer_profile, _ = TrainerProfile.objects.get_or_create(
    user=trainer_user,
    defaults={
        'admin': admin_user,
        'specialization': 'Strength & Conditioning Specialist',
        'bio': 'Certified Coach with 8+ years experience helping clients build muscle and burn fat.',
        'phone': '+1 (555) 234-5678',
        'is_active': True,
    }
)
trainer_profile.admin = admin_user
trainer_profile.categories.set([categories[0], categories[1], categories[2]])
trainer_profile.specialization = 'Strength & Conditioning Specialist'
trainer_profile.phone = '+1 (555) 234-5678'
trainer_profile.is_active = True
trainer_profile.save()
print(f"Trainer Profile: {trainer_user.email} (Password: {trainer_pass}) linked to {[c.name for c in trainer_profile.categories.all()]}")

# 4. Create Client Account
client_email = "client@fitness.com"
client_pass = "Client@123456"
client_user, created = User.objects.get_or_create(
    email=client_email,
    defaults={
        'username': client_email,
        'first_name': 'Alexander',
        'last_name': 'Hayes',
        'is_client': True,
    }
)
client_user.set_password(client_pass)
client_user.is_client = True
client_user.first_name = 'Alexander'
client_user.last_name = 'Hayes'
client_user.save()

client_profile, _ = ClientProfile.objects.get_or_create(
    user=client_user,
    defaults={
        'phone': '+1 (555) 890-1234',
        'address': 'Manhattan, New York 📍',
        'date_of_birth': date(1998, 5, 14),
        'gender': 'Male',
        'age': '28',
        'weight': 84.5,
        'height': 182.0,
        'neck_circumference': 38.0,
        'waist': 86.0,
        'preferred_weight': 78.0,
        'preferred_waist': 80.0,
        'preferred_bmi': 23.5,
        'preferred_fat_percent': 14.0,
        'is_active': True,
    }
)
client_profile.phone = '+1 (555) 890-1234'
client_profile.address = 'Manhattan, New York 📍'
client_profile.date_of_birth = date(1998, 5, 14)
client_profile.gender = 'Male'
client_profile.age = '28'
client_profile.weight = 84.5
client_profile.height = 182.0
client_profile.neck_circumference = 38.0
client_profile.waist = 86.0
client_profile.preferred_weight = 78.0
client_profile.preferred_waist = 80.0
client_profile.preferred_bmi = 23.5
client_profile.preferred_fat_percent = 14.0
client_profile.is_active = True

# Calculate BMI
h_m = 1.82
bmi_val = round(84.5 / (h_m * h_m), 1)
if client_profile.bmi:
    client_profile.bmi.bmi = bmi_val
    client_profile.bmi.save()
else:
    client_profile.bmi = BMI.objects.create(bmi=bmi_val)

if client_profile.fat_percent:
    client_profile.fat_percent.fat_percent = 18.5
    client_profile.fat_percent.save()
else:
    client_profile.fat_percent = FatPercent.objects.create(fat_percent=18.5)

client_profile.categories.set([categories[0], categories[1]])
client_profile.save()
print(f"Client Profile: {client_user.email} (Password: {client_pass})")

# 5. Link Client to Trainer
link, link_created = TrainerClientLink.objects.get_or_create(
    trainer=trainer_profile,
    client=client_profile,
    defaults={'is_active': True, 'is_subscribed': True}
)
link.is_active = True
link.is_subscribed = True
link.save()
print(f"TrainerClientLink: Marcus Vance <-> Alexander Hayes (Active: {link.is_active})")

# 6. Create Master Video Exercises
exercises_data = [
    ("Dumbbell Goblet Squat", "Full range of motion squat engaging quads, glutes, and core.", 45, [categories[0], categories[1]]),
    ("Barbell Bench Press", "Compound upper body pressing exercise for chest, shoulders, and triceps.", 60, [categories[1]]),
    ("High-Intensity Interval Sprints", "Short explosive bursts of running to maximize calorie burn.", 30, [categories[0], categories[2]]),
    ("Lat Pulldown & Rows", "Targeting the latissimus dorsi, upper back, and posture muscles.", 50, [categories[1]]),
    ("Plank to Push-up Complex", "Core stabilization exercise combined with upper body endurance.", 40, [categories[0], categories[3]]),
    ("Romanian Deadlift (RDL)", "Hamstrings and posterior chain hip-hinge movement.", 55, [categories[1]]),
]

created_exercises = []
for title, desc, duration, cats in exercises_data:
    ex, _ = Exercise.objects.get_or_create(
        title=title,
        defaults={
            'description': desc,
            'duration_seconds': duration,
            'is_active': True,
        }
    )
    ex.categories.set(cats)
    ex.description = desc
    ex.duration_seconds = duration
    ex.is_active = True
    ex.save()
    created_exercises.append(ex)

print(f"Created/verified {len(created_exercises)} master exercises.")

# 7. Create Workout Plans for Client
# Assign for Monday (0), Wednesday (2), Friday (4), Saturday (5)
workout_plan_assignments = [
    (0, created_exercises[0], 4, 12, 45, 1, "Warmup with bodyweight first, focus on depth."),
    (0, created_exercises[1], 4, 10, 60, 2, "Controlled eccentric tempo 3-1-1."),
    (2, created_exercises[3], 4, 12, 45, 1, "Squeeze shoulder blades at the contraction."),
    (2, created_exercises[5], 4, 10, 50, 2, "Keep spine neutral, hinge from hips."),
    (4, created_exercises[2], 5, 1, 30, 1, "Max effort sprint intervals with 30s rest."),
    (4, created_exercises[4], 3, 15, 40, 2, "Maintain rigid core alignment throughout."),
    (5, created_exercises[0], 3, 15, 45, 1, "High volume endurance squats."),
]

for day, ex, sets, reps, rep_time, order, notes in workout_plan_assignments:
    plan, _ = ClientWorkoutPlan.objects.get_or_create(
        trainer=trainer_profile,
        client=client_profile,
        day_of_week=day,
        exercise=ex,
        order=order,
        defaults={
            'sets': sets,
            'reps': reps,
            'time_per_rep_seconds': rep_time,
            'notes': notes,
            'is_active': True,
        }
    )
    plan.sets = sets
    plan.reps = reps
    plan.time_per_rep_seconds = rep_time
    plan.notes = notes
    plan.is_active = True
    plan.save()

print("Created 7 client workout plan routines.")

# 8. Create Daily Kcal Targets & Kcal Logs
today = date.today()
for day_idx in range(7):
    DailyKcalTarget.objects.get_or_create(
        client=client_profile,
        day_of_week=day_idx,
        defaults={
            'target_kcal': 2200 if day_idx in [0, 2, 4, 5] else 1900,
            'created_by': trainer_user
        }
    )

# Log last 7 days of calorie burn
for i in range(7):
    d = today - timedelta(days=i)
    burned = 2150 - (i * 45) + (i % 2 * 90)
    ClientKcalLog.objects.update_or_create(
        client=client_profile,
        date=d,
        defaults={'actual_kcal': burned, 'notes': f'Logged workout session for {d}'}
    )

print("Created Kcal targets and last 7 days of calorie logs.")

# 9. Create Hydration Targets & Logs
for day_idx in range(7):
    DailyHydrationTarget.objects.get_or_create(
        client=client_profile,
        day_of_week=day_idx,
        defaults={'target_cups': 8, 'created_by': trainer_user}
    )

ClientHydrationLog.objects.update_or_create(
    client=client_profile,
    date=today,
    defaults={'actual_cups': 6, 'notes': '6 of 8 glasses completed'}
)

print("Created Hydration targets and logs.")

# 10. Create Sleep Targets & Logs
for day_idx in range(7):
    DailySleepTarget.objects.get_or_create(
        client=client_profile,
        day_of_week=day_idx,
        defaults={'target_hours': 8.0, 'created_by': trainer_user}
    )

ClientSleepLog.objects.update_or_create(
    client=client_profile,
    date=today,
    defaults={'actual_hours': 7.5, 'notes': 'Good REM sleep'}
)

print("--- Data Seeding Finished Successfully! ---")
