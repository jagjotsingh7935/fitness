import os
import re
import shutil
import tempfile
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from accounts.models import Category
from fitnessApp.models import Exercise

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# Automated categorization taxonomy rules
CATEGORY_RULES = {
    "Chest": [
        "chest", "bench", "incline", "decline", "fly", "flye", "pec", "pushup", "push-up", "dip", "dips"
    ],
    "Back & Lats": [
        "back", "lat", "pulldown", "pull-up", "pullup", "row", "rowing", "deadlift", "rdl", "shrug", "hyperextension"
    ],
    "Biceps & Arms": [
        "bicep", "biceps", "curl", "hammer", "tricep", "triceps", "extension", "skull crusher", "kickback", "preacher", "arm", "arms"
    ],
    "Shoulders & Delts": [
        "shoulder", "shoulders", "overhead", "military", "lateral", "delt", "delts", "front raise", "rear delt", "face pull", "arnold", "upright row"
    ],
    "Legs & Glutes": [
        "squat", "lunge", "lunges", "leg press", "quad", "hamstring", "glute", "glutes", "calf", "calves", "hip thrust", "step up", "hack squat", "femoral", "adduction", "abduction"
    ],
    "Core & Abs": [
        "abs", "core", "plank", "crunch", "crunches", "russian twist", "leg raise", "ab wheel", "hollow", "bicycle", "side bend", "sit-up", "situp"
    ],
    "Cardio & HIIT": [
        "cardio", "hiit", "sprint", "burpee", "burpees", "jumping jack", "jump rope", "skipping", "mountain climber", "battle rope"
    ],
    "Full Body": [
        "kettlebell", "clean", "snatch", "thruster", "compound", "man maker"
    ],
}

# Goal category mapping rules
GOAL_RULES = {
    "Muscle Building": [
        "press", "curl", "row", "squat", "deadlift", "extension", "pulldown", "thrust", "barbell", "dumbbell", "lever", "band", "smith", "cable"
    ],
    "Weight Loss": [
        "hiit", "cardio", "burpee", "jump", "sprint", "climber", "plank", "lunge"
    ],
    "Endurance": [
        "running", "sprint", "conditioning", "skipping", "jump rope", "hiit"
    ],
    "Flexibility": [
        "stretch", "stretching", "yoga", "mobility", "warmup", "cooldown", "foam roll"
    ]
}


def clean_exercise_title(filename):
    """Converts filename e.g. '01_incline_dumbbell_press_1080p.mp4' into 'Incline Dumbbell Press'"""
    name = Path(filename).stem
    # Remove leading numbering like '01_', '1 - '
    name = re.sub(r'^[0-9]+[\s_.-]*', '', name)
    # Remove resolution / quality tags
    name = re.sub(r'[\s_.-]*(?:1080p|720p|480p|4k|2k|h264|hevc|x264|hd|video)[\s_.-]*', '', name, flags=re.IGNORECASE)
    # Replace underscores and hyphens with spaces
    name = re.sub(r'[_.-]+', ' ', name).strip()
    return name.title()


def determine_categories(title, filename, file_path=""):
    """Matches title, filename, and subfolder path against category rules to return list of Category names"""
    combined_text = f"{title.lower()} {filename.lower()} {file_path.lower()}"
    matched_cats = set()

    # Match primary muscle group
    for cat_name, keywords in CATEGORY_RULES.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in keywords):
            matched_cats.add(cat_name)

    # If no muscle group matched, default to Full Body
    if not matched_cats:
        matched_cats.add("Full Body")

    # Match fitness goal
    for goal_name, keywords in GOAL_RULES.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in keywords):
            matched_cats.add(goal_name)
    
    # Ensure Muscle Building by default for resistance workouts
    if not any(g in matched_cats for g in ["Muscle Building", "Weight Loss", "Endurance", "Flexibility"]):
        matched_cats.add("Muscle Building")

    return list(matched_cats)


class Command(BaseCommand):
    help = "Bulk import workout videos into Exercise model with automated categorization"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default=None,
            help="Path to local folder containing workout video files",
        )
        parser.add_argument(
            "--default-duration",
            type=int,
            default=45,
            help="Default duration in seconds (default: 45)",
        )

    def handle(self, *args, **options):
        source_dir = options.get("source")
        default_duration = options.get("default_duration", 45)

        if not source_dir or not os.path.exists(source_dir):
            self.stdout.write(self.style.ERROR(f"Source folder does not exist: {source_dir}"))
            return

        media_videos_dir = os.path.join(settings.MEDIA_ROOT, "exercise_videos")
        media_thumbs_dir = os.path.join(settings.MEDIA_ROOT, "exercise_thumbnails")
        os.makedirs(media_videos_dir, exist_ok=True)
        os.makedirs(media_thumbs_dir, exist_ok=True)

        # Cache category models for fast lookup
        category_cache = {c.name: c for c in Category.objects.all()}

        # Collect all video files
        self.stdout.write(f"Scanning folder: {source_dir}...")
        video_files = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if Path(file).suffix.lower() in VIDEO_EXTENSIONS:
                    video_files.append(os.path.join(root, file))

        total_files = len(video_files)
        if total_files == 0:
            self.stdout.write(self.style.WARNING(f"No video files found in {source_dir}."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {total_files} video files to process."))

        imported_count = 0
        updated_count = 0
        skipped_copy_count = 0

        # Process in batch
        for idx, file_path in enumerate(video_files, 1):
            filename = os.path.basename(file_path)
            clean_title = clean_exercise_title(filename)
            dest_video_rel = f"exercise_videos/{filename}"
            dest_video_abs = os.path.join(settings.MEDIA_ROOT, dest_video_rel)

            # Copy file to media directory only if needed
            if os.path.abspath(file_path) != os.path.abspath(dest_video_abs):
                if not os.path.exists(dest_video_abs) or os.path.getsize(dest_video_abs) != os.path.getsize(file_path):
                    shutil.copy2(file_path, dest_video_abs)
                else:
                    skipped_copy_count += 1

            # Determine categories
            cat_names = determine_categories(clean_title, filename, file_path)

            # Check if exercise with this title exists
            exercise = Exercise.objects.filter(title=clean_title).first()
            if not exercise:
                exercise = Exercise.objects.create(
                    title=clean_title,
                    video=dest_video_rel,
                    duration_seconds=default_duration,
                    description=f"{clean_title} exercise tutorial.",
                    is_active=True,
                )
                imported_count += 1
            else:
                exercise.video = dest_video_rel
                exercise.is_active = True
                exercise.save()
                updated_count += 1

            # Attach categories
            cats_to_add = [category_cache[cn] for cn in cat_names if cn in category_cache]
            if cats_to_add:
                exercise.categories.add(*cats_to_add)

            if idx % 100 == 0 or idx == total_files:
                self.stdout.write(f"Processed {idx}/{total_files} exercises ({imported_count} new, {updated_count} updated)...")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] Done processing {source_dir}!\n"
                f"   - Imported New: {imported_count}\n"
                f"   - Updated: {updated_count}\n"
                f"   - Total in Database: {Exercise.objects.count()}"
            )
        )