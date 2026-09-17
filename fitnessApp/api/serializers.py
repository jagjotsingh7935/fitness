from rest_framework import serializers
from accounts.models import *
from fitnessApp.models import *
from accounts.api.serializers import *



# ------------------- Exercise Serializers -------------------

class ExerciseSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ['id', 'title', 'description', 'video', 'video_url', 'thumbnail', 'thumbnail_url',
                  'categories', 'category_ids', 'duration_seconds', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_video_url(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def to_internal_value(self, data):
        """Handle FormData conversion: convert '1,5' to [1,5]."""
        # Print raw data for debugging
        print("Raw received data:", data)
        
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        
        if 'category_ids' in mutable_data:
            category_ids_value = mutable_data.get('category_ids')
            
            if isinstance(category_ids_value, str):
                if ',' in category_ids_value:
                    # Convert "1,5" to [1,5]
                    category_ids_list = [int(id.strip()) for id in category_ids_value.split(',') if id.strip()]
                    mutable_data.setlist('category_ids', category_ids_list)
                elif category_ids_value:
                    # Convert "1" to [1]
                    category_ids_list = [int(category_ids_value)]
                    mutable_data.setlist('category_ids', category_ids_list)
        
        return super().to_internal_value(mutable_data)

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        exercise = Exercise.objects.create(**validated_data)
        if categories:
            exercise.categories.set(categories)
        return exercise

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance


class ExerciseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing exercises."""
    category_names = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ['id', 'title', 'thumbnail_url', 'duration_seconds', 'category_names', 'video_url','is_active']

    def get_category_names(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_video_url(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None


# ------------------- Workout Plan Serializers -------------------
class ClientWorkoutPlanSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    trainer_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = ClientWorkoutPlan
        fields = ['id', 'trainer', 'trainer_name', 'client', 'client_name',
                  'exercise', 'exercise_detail', 'master_plan', 'day_of_week', 'day_display',
                  'sets', 'reps', 'time_per_rep_seconds', 'order', 'notes',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_trainer_name(self, obj):
        return obj.trainer.user.get_full_name() or obj.trainer.user.email

    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.email

    def validate(self, data):
        # Ensure the trainer is authorized to assign this exercise to this client
        trainer = data.get('trainer')
        client = data.get('client')

        if trainer and client:
            # Check if client is linked to trainer with active subscription
            if not TrainerClientLink.objects.filter(trainer=trainer, client=client, is_active=True).exists():
                raise serializers.ValidationError("This client is not linked to this trainer with an active subscription.")

        return data


class ClientWorkoutPlanCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientWorkoutPlan
        fields = ['id', 'trainer', 'client', 'exercise', 'day_of_week',
                  'sets', 'reps', 'time_per_rep_seconds', 'order', 'notes', 'is_active', 'master_plan']
        read_only_fields = ['trainer']  # Trainer is set automatically from the logged-in user

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        # Support both 'client_id' and 'client'
        if 'client_id' in data and 'client' not in data:
            data['client'] = data['client_id']
        # Support both 'exercise_id' and 'exercise'
        if 'exercise_id' in data and 'exercise' not in data:
            data['exercise'] = data['exercise_id']
        return super().to_internal_value(data)

    def validate(self, data):
        # Get trainer from context (passed via view) or from data (if someone tries to send it)
        trainer = data.get('trainer')
        if not trainer:
            # Fallback to request user from context
            request = self.context.get('request')
            if request and hasattr(request.user, 'trainer_profile'):
                trainer = request.user.trainer_profile
        
        client = data.get('client')

        # Validate trainer-client link (if trainer is known and user is not admin)
        request = self.context.get('request')
        is_admin = request and (getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superuser', False))
        if trainer and client and not is_admin:
            if not TrainerClientLink.objects.filter(trainer=trainer, client=client, is_active=True).exists():
                raise serializers.ValidationError(
                    "This client is not linked to this trainer with an active subscription."
                )
        
        return data

    def create(self, validated_data):
        # Ensure trainer is set from context if not already present
        if 'trainer' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request.user, 'trainer_profile'):
                validated_data['trainer'] = request.user.trainer_profile
        
        # Ensure order doesn't collide with unique constraint:
        # unique_together = ['trainer', 'client', 'day_of_week', 'exercise', 'order']
        trainer = validated_data.get('trainer')
        client = validated_data.get('client')
        day_of_week = validated_data.get('day_of_week')
        order = validated_data.get('order', 0)

        existing_orders = ClientWorkoutPlan.objects.filter(
            trainer=trainer,
            client=client,
            day_of_week=day_of_week
        ).values_list('order', flat=True)

        if order in existing_orders:
            validated_data['order'] = (max(existing_orders) if existing_orders else 0) + 1

        return super().create(validated_data)

# ------------------- Master Workout Plan Serializers -------------------
class MasterWorkoutPlanItemSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = MasterWorkoutPlanItem
        fields = ['id', 'master_plan', 'exercise', 'exercise_detail',
                  'day_of_week', 'day_display', 'sets', 'reps',
                  'time_per_rep_seconds', 'order', 'notes', 'created_at']
        read_only_fields = ['created_at', 'master_plan']


class MasterWorkoutPlanSerializer(serializers.ModelSerializer):
    items = MasterWorkoutPlanItemSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    trainer_name = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = MasterWorkoutPlan
        fields = ['id', 'trainer', 'trainer_name', 'title', 'description',
                  'categories', 'category_ids', 'items', 'items_count',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_trainer_name(self, obj):
        if obj.trainer and obj.trainer.user:
            return obj.trainer.user.get_full_name() or obj.trainer.user.email
        return "System Admin"

    def get_items_count(self, obj):
        return obj.items.count()

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        request = self.context.get('request')
        if request and hasattr(request.user, 'trainer_profile'):
            validated_data['trainer'] = request.user.trainer_profile
        master_plan = MasterWorkoutPlan.objects.create(**validated_data)
        if categories:
            master_plan.categories.set(categories)
        return master_plan

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance


class AssignMasterWorkoutPlanSerializer(serializers.Serializer):
    client_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of ClientProfile IDs to assign the master workout plan to"
    )
    clear_existing = serializers.BooleanField(
        default=False,
        required=False,
        help_text="If true, removes existing active workout plans for these clients before assigning"
    )


# ------------------- Kcal Target Serializers -------------------
class DailyKcalTargetSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = DailyKcalTarget
        fields = ['id', 'client', 'client_email', 'day_of_week', 'day_display',
                  'target_kcal', 'created_by', 'created_by_email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'created_by']




class DailyKcalTargetCreateUpdateSerializer(serializers.ModelSerializer):
    # Accept a list of client IDs under the key 'client'
    client = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.filter(is_active=True)),
        write_only=True,
        required=True
    )
    day_of_week = serializers.IntegerField(required=True)
    target_kcal = serializers.IntegerField(required=True)

    class Meta:
        model = DailyKcalTarget
        fields = ['client', 'day_of_week', 'target_kcal']

    def validate(self, data):
        clients = data.get('client')
        if not clients:
            raise serializers.ValidationError("At least one client must be provided.")
        
        day_of_week = data['day_of_week']
        target_kcal = data['target_kcal']
        
        # Optional: Prevent duplicates if a target already exists for any of these clients on the same day
        existing = DailyKcalTarget.objects.filter(
            client__in=clients,
            day_of_week=day_of_week
        ).values_list('client_id', flat=True)
        
        if existing:
            conflicting_ids = [c.id for c in clients if c.id in existing]
            raise serializers.ValidationError(
                f"Daily kcal target already exists for day {day_of_week} for client(s): {conflicting_ids}"
            )
        
        # Store the client list under a different key to avoid conflict with the model's 'client' FK
        data['_clients'] = clients
        # Remove the original 'client' key so the model's create doesn't see it
        data.pop('client')
        return data

    def create(self, validated_data):
        clients = validated_data.pop('_clients')
        day_of_week = validated_data['day_of_week']
        target_kcal = validated_data['target_kcal']
        created_by = self.context['request'].user
        
        targets = [
            DailyKcalTarget(
                client=client,
                day_of_week=day_of_week,
                target_kcal=target_kcal,
                created_by=created_by
            )
            for client in clients
        ]
        DailyKcalTarget.objects.bulk_create(targets)
        return targets  
    


# ------------------- Kcal Log Serializers -------------------
class ClientKcalLogSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.user.email', read_only=True)

    class Meta:
        model = ClientKcalLog
        fields = ['id', 'client', 'client_email', 'date', 'actual_kcal', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ClientKcalLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientKcalLog
        fields = ['date', 'actual_kcal', 'notes']





# ---------- Hydration Serializers ----------
class DailyHydrationTargetSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = DailyHydrationTarget
        fields = ['id', 'client', 'client_email', 'day_of_week', 'day_display',
                  'target_cups', 'created_by', 'created_by_email', 'created_at', 'updated_at']


class DailyHydrationTargetCreateUpdateSerializer(serializers.ModelSerializer):
    client = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.filter(is_active=True)),
        write_only=True, required=True
    )
    day_of_week = serializers.IntegerField(required=True)
    target_cups = serializers.IntegerField(required=True)

    class Meta:
        model = DailyHydrationTarget
        fields = ['client', 'day_of_week', 'target_cups', 'created_by']
        read_only_fields = ['created_by']

    def validate(self, data):
        clients = data.get('client')
        day = data['day_of_week']
        if not clients:
            raise serializers.ValidationError("At least one client required.")
        if self.context['request'].method == 'POST':
            existing = DailyHydrationTarget.objects.filter(
                client__in=clients, day_of_week=day
            ).values_list('client_id', flat=True)
            if existing:
                raise serializers.ValidationError(f"Target already exists for day {day} for client(s): {list(existing)}")
        data['_clients'] = clients
        data.pop('client')
        return data

    def create(self, validated_data):
        clients = validated_data.pop('_clients')
        day = validated_data['day_of_week']
        target = validated_data['target_cups']
        created_by = self.context['request'].user
        targets = [DailyHydrationTarget(
            client=c, day_of_week=day, target_cups=target, created_by=created_by
        ) for c in clients]
        DailyHydrationTarget.objects.bulk_create(targets)
        return targets


class ClientHydrationLogSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.user.email', read_only=True)

    class Meta:
        model = ClientHydrationLog
        fields = ['id', 'client', 'client_email', 'date', 'actual_cups', 'notes', 'created_at', 'updated_at']


class ClientHydrationLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientHydrationLog
        fields = ['date', 'actual_cups', 'notes']


# ---------- Sleep Serializers ----------
class DailySleepTargetSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = DailySleepTarget
        fields = ['id', 'client', 'client_email', 'day_of_week', 'day_display',
                  'target_hours', 'created_by', 'created_by_email', 'created_at', 'updated_at']


class DailySleepTargetCreateUpdateSerializer(serializers.ModelSerializer):
    client = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.filter(is_active=True)),
        write_only=True, required=True
    )
    day_of_week = serializers.IntegerField(required=True)
    target_hours = serializers.DecimalField(max_digits=3, decimal_places=1, required=True)

    class Meta:
        model = DailySleepTarget
        fields = ['client', 'day_of_week', 'target_hours', 'created_by']
        read_only_fields = ['created_by']

    def validate(self, data):
        clients = data.get('client')
        day = data['day_of_week']
        if not clients:
            raise serializers.ValidationError("At least one client required.")
        if self.context['request'].method == 'POST':
            existing = DailySleepTarget.objects.filter(
                client__in=clients, day_of_week=day
            ).values_list('client_id', flat=True)
            if existing:
                raise serializers.ValidationError(f"Target already exists for day {day} for client(s): {list(existing)}")
        data['_clients'] = clients
        data.pop('client')
        return data

    def create(self, validated_data):
        clients = validated_data.pop('_clients')
        day = validated_data['day_of_week']
        target = validated_data['target_hours']
        created_by = self.context['request'].user
        targets = [DailySleepTarget(
            client=c, day_of_week=day, target_hours=target, created_by=created_by
        ) for c in clients]
        DailySleepTarget.objects.bulk_create(targets)
        return targets


class ClientSleepLogSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.user.email', read_only=True)

    class Meta:
        model = ClientSleepLog
        fields = ['id', 'client', 'client_email', 'date', 'actual_hours', 'notes', 'created_at', 'updated_at']


class ClientSleepLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientSleepLog
        fields = ['date', 'actual_hours', 'notes']


# ------------------- Diet & Nutrition Serializers -------------------

class ClientDietMealItemSerializer(serializers.ModelSerializer):
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)
    emoji = serializers.CharField(read_only=True)
    done = serializers.SerializerMethodField()

    class Meta:
        model = ClientDietMealItem
        fields = [
            'id', 'diet_plan', 'meal_type', 'meal_type_display', 'name',
            'time_label', 'calories', 'protein_grams', 'carbs_grams', 'fat_grams',
            'custom_emoji', 'emoji', 'order', 'done', 'created_at'
        ]
        read_only_fields = ['id', 'diet_plan', 'created_at']

    def get_done(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'client_profile'):
            return False
        from django.utils import timezone
        today = timezone.localdate()
        return ClientMealLog.objects.filter(
            client=request.user.client_profile,
            meal_item=obj,
            date=today,
            is_completed=True
        ).exists()


class ClientDietPlanSerializer(serializers.ModelSerializer):
    meals = ClientDietMealItemSerializer(many=True, read_only=True)
    client_name = serializers.SerializerMethodField()
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    trainer_name = serializers.SerializerMethodField()
    meals_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientDietPlan
        fields = [
            'id', 'client', 'client_name', 'client_email', 'trainer',
            'trainer_name', 'title', 'daily_calorie_target', 'protein_grams',
            'carbs_grams', 'fat_grams', 'notes', 'is_active', 'meals',
            'meals_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.email

    def get_trainer_name(self, obj):
        if obj.trainer and obj.trainer.user:
            return obj.trainer.user.get_full_name() or obj.trainer.user.email
        return "Admin"

    def get_meals_count(self, obj):
        return obj.meals.count()


class ClientDietPlanCreateUpdateSerializer(serializers.ModelSerializer):
    meals_data = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = ClientDietPlan
        fields = [
            'id', 'client', 'title', 'daily_calorie_target',
            'protein_grams', 'carbs_grams', 'fat_grams', 'notes',
            'is_active', 'meals_data'
        ]

    def create(self, validated_data):
        meals_data = validated_data.pop('meals_data', [])
        request = self.context.get('request')
        if request and hasattr(request.user, 'trainer_profile'):
            validated_data['trainer'] = request.user.trainer_profile
        if request:
            validated_data['created_by'] = request.user

        # Mark other diet plans for this client as inactive if this new one is active
        if validated_data.get('is_active', True):
            ClientDietPlan.objects.filter(client=validated_data['client']).update(is_active=False)

        diet_plan = ClientDietPlan.objects.create(**validated_data)

        for i, m in enumerate(meals_data):
            ClientDietMealItem.objects.create(
                diet_plan=diet_plan,
                meal_type=m.get('meal_type', 'BREAKFAST'),
                name=m.get('name', ''),
                time_label=m.get('time_label', ''),
                calories=int(m.get('calories') or 350),
                protein_grams=int(m.get('protein_grams') or 0),
                carbs_grams=int(m.get('carbs_grams') or 0),
                fat_grams=int(m.get('fat_grams') or 0),
                custom_emoji=m.get('custom_emoji', ''),
                order=int(m.get('order') or i),
            )
        return diet_plan

    def update(self, instance, validated_data):
        meals_data = validated_data.pop('meals_data', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if meals_data is not None:
            instance.meals.all().delete()
            for i, m in enumerate(meals_data):
                ClientDietMealItem.objects.create(
                    diet_plan=instance,
                    meal_type=m.get('meal_type', 'BREAKFAST'),
                    name=m.get('name', ''),
                    time_label=m.get('time_label', ''),
                    calories=int(m.get('calories') or 350),
                    protein_grams=int(m.get('protein_grams') or 0),
                    carbs_grams=int(m.get('carbs_grams') or 0),
                    fat_grams=int(m.get('fat_grams') or 0),
                    custom_emoji=m.get('custom_emoji', ''),
                    order=int(m.get('order') or i),
                )
        return instance