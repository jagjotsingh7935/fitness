import os
from django.core.management.base import BaseCommand
from accounts.models import Category
from fitnessApp.models import Exercise

CATEGORIES_DATA = [
    # Muscle Groups
    {
        "name": "Chest",
        "icon": "category_icons/chest.svg",
        "description": "Chest, pectorals, and upper push development."
    },
    {
        "name": "Back & Lats",
        "icon": "category_icons/back.svg",
        "description": "Upper back, lats, rhomboids, and pull strength."
    },
    {
        "name": "Biceps & Arms",
        "icon": "category_icons/biceps.svg",
        "description": "Biceps, triceps, and forearm arm definition."
    },
    {
        "name": "Shoulders & Delts",
        "icon": "category_icons/shoulders.svg",
        "description": "Anterior, lateral, and rear deltoid sculpting."
    },
    {
        "name": "Legs & Glutes",
        "icon": "category_icons/legs.svg",
        "description": "Quads, hamstrings, glutes, and lower body power."
    },
    {
        "name": "Core & Abs",
        "icon": "category_icons/core.svg",
        "description": "Abdominals, obliques, and core stability."
    },
    {
        "name": "Cardio & HIIT",
        "icon": "category_icons/cardio.svg",
        "description": "High-intensity cardio, endurance, and fat burning."
    },
    {
        "name": "Full Body",
        "icon": "category_icons/full_body.svg",
        "description": "Compound full body and functional movement exercises."
    },
    # Fitness Goals
    {
        "name": "Muscle Building",
        "icon": "category_icons/muscle_building.svg",
        "description": "Hypertrophy, progressive overload, and muscle mass building."
    },
    {
        "name": "Weight Loss",
        "icon": "category_icons/weight_loss.svg",
        "description": "Calorie burn, fat loss, and metabolic reset conditioning."
    },
    {
        "name": "Endurance",
        "icon": "category_icons/endurance.svg",
        "description": "Stamina building, conditioning, and cardiovascular health."
    },
    {
        "name": "Flexibility",
        "icon": "category_icons/flexibility.svg",
        "description": "Mobility, joint recovery, yoga, and dynamic stretching."
    },
]


class Command(BaseCommand):
    help = "Seed or update fitness categories with clean icons and descriptions"

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")

        # 1. Clean up duplicate lower-case categories if any
        lower_weight_loss = Category.objects.filter(name="weight loss").first()
        proper_weight_loss = Category.objects.filter(name="Weight Loss").first()
        if lower_weight_loss and proper_weight_loss and lower_weight_loss.id != proper_weight_loss.id:
            for ex in Exercise.objects.filter(categories=lower_weight_loss):
                ex.categories.remove(lower_weight_loss)
                ex.categories.add(proper_weight_loss)
            lower_weight_loss.delete()
            self.stdout.write(self.style.WARNING("Cleaned up duplicate 'weight loss' category."))

        # 2. Seed / update categories
        created_count = 0
        updated_count = 0

        for item in CATEGORIES_DATA:
            cat, created = Category.objects.get_or_create(
                name=item["name"],
                defaults={
                    "icon": item["icon"],
                    "description": item["description"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created category: {cat.name}"))
            else:
                cat.icon = item["icon"]
                cat.description = item["description"]
                cat.is_active = True
                cat.save()
                updated_count += 1
                self.stdout.write(f"Updated category: {cat.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created_count}, updated {updated_count} categories (Total: {Category.objects.count()})."
            )
        )