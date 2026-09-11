import os
import cv2
from django.core.management.base import BaseCommand
from django.conf import settings
from fitnessApp.models import Exercise

class Command(BaseCommand):
    help = 'Automatically generate thumbnails and durations for all exercise videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Ensure target thumbnail directory exists
        thumb_dir = os.path.join(settings.MEDIA_ROOT, 'exercise_thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)

        exercises = Exercise.objects.exclude(video='')
        if not force:
            exercises = exercises.filter(thumbnail__isnull=True) | exercises.filter(thumbnail='')

        total = exercises.count()
        self.stdout.write(f'Found {total} exercises needing thumbnail generation...')

        success_count = 0
        skip_count = 0
        error_count = 0

        for ex in exercises:
            if not ex.video:
                skip_count += 1
                continue

            video_path = ex.video.path if hasattr(ex.video, 'path') else os.path.join(settings.MEDIA_ROOT, str(ex.video))
            
            if not os.path.exists(video_path):
                self.stdout.write(f'[WARN] Video file not found for #{ex.id} ({ex.title}): {video_path}')
                error_count += 1
                continue

            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.stdout.write(f'[WARN] Could not open video #{ex.id}: {video_path}')
                    error_count += 1
                    continue

                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                duration = int(total_frames / fps) if fps > 0 else 0

                # Sample frame at ~1.0 second or 25% in to avoid start screen/black frame
                target_frame = min(int(fps * 1.0), max(0, total_frames // 4))
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()

                if not ret or frame is None:
                    # Fallback to frame 0
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()

                cap.release()

                if not ret or frame is None:
                    self.stdout.write(f'[WARN] Could not extract frame from #{ex.id}')
                    error_count += 1
                    continue

                # Save thumbnail as optimized JPEG
                thumb_filename = f'exercise_{ex.id}.jpg'
                thumb_path = os.path.join(thumb_dir, thumb_filename)
                
                # Write image with quality 88
                cv2.imwrite(thumb_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])

                # Relative path for Django ImageField
                rel_path = f'exercise_thumbnails/{thumb_filename}'
                ex.thumbnail = rel_path

                if duration > 0 and ex.duration_seconds == 0:
                    ex.duration_seconds = duration

                ex.save(update_fields=['thumbnail', 'duration_seconds'] if ex.duration_seconds else ['thumbnail'])
                success_count += 1

                if success_count % 25 == 0 or success_count == total:
                    self.stdout.write(f'Progress: {success_count}/{total} thumbnails generated...')

            except Exception as e:
                self.stdout.write(f'[ERROR] Failed processing #{ex.id} ({ex.title}): {e}')
                error_count += 1

        self.stdout.write(
            f'Completed thumbnail generation! Total: {total}, '
            f'Generated: {success_count}, Errors: {error_count}, Skipped: {skip_count}'
        )
