from rest_framework.permissions import IsAuthenticated
from accounts.models import *
from accounts.api.serializers import *
from accounts.api.permissions import AdminOnlyPermission
from rest_framework import generics, filters
from fitnessApp.models import *
from fitnessApp.api.serializers import *
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status



class ExerciseListView(generics.ListAPIView):
    """List exercises (trainers see only those matching their categories; admin sees all)."""
    serializer_class = ExerciseListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'duration_seconds', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return Exercise.objects.filter(is_active=True)
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            trainer_categories = trainer.categories.all()
            # Exercises that have at least one category in common with trainer's categories
            return Exercise.objects.filter(
                is_active=True,
                categories__in=trainer_categories
            ).distinct()
        else:
            # Clients cannot list exercises directly (they see through workout plans)
            return Exercise.objects.none()


class ExerciseDetailView(generics.RetrieveAPIView):
    """Get single exercise detail (trainer can only view if category matches)."""
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return Exercise.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            trainer_categories = trainer.categories.all()
            return Exercise.objects.filter(categories__in=trainer_categories).distinct()
        return Exercise.objects.none()


class ExerciseCreateView(generics.CreateAPIView):
    """Admin only: create a new exercise."""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [AdminOnlyPermission]
    permission_model = Exercise


class ExerciseUpdateView(generics.UpdateAPIView):
    """Admin only: update exercise."""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [AdminOnlyPermission]
    permission_model = Exercise


class ExerciseDeleteView(generics.DestroyAPIView):
    """Admin only: soft delete (set is_active=False)."""
    queryset = Exercise.objects.all()
    permission_classes = [AdminOnlyPermission]
    permission_model = Exercise

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ------------------- Workout Plan Views -------------------
class WorkoutPlanListView(generics.ListAPIView):
    """List workout plans – trainers see plans they created; clients see plans for themselves."""
    serializer_class = ClientWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['day_of_week', 'order']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientWorkoutPlan.objects.filter(is_active=True)
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientWorkoutPlan.objects.filter(trainer=trainer, is_active=True)
        elif hasattr(user, 'client_profile'):
            client = user.client_profile
            return ClientWorkoutPlan.objects.filter(client=client, is_active=True)
        return ClientWorkoutPlan.objects.none()


class WorkoutPlanCreateView(generics.CreateAPIView):
    """Trainer only: create a workout plan for his linked client."""
    serializer_class = ClientWorkoutPlanCreateUpdateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure the trainer is the logged-in trainer
        user = self.request.user
        if not hasattr(user, 'trainer_profile'):
            raise PermissionDenied("Only trainers can create workout plans.")
        serializer.save(trainer=user.trainer_profile)


class WorkoutPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Trainer can update/delete his own plans; admin can also."""
    serializer_class = ClientWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientWorkoutPlan.objects.all()
        elif hasattr(user, 'trainer_profile'):
            return ClientWorkoutPlan.objects.filter(trainer=user.trainer_profile)
        else:
            return ClientWorkoutPlan.objects.none()


class ClientWorkoutPlanByDayView(generics.ListAPIView):
    """Client view: get his workout plan grouped by day of week."""
    serializer_class = ClientWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'client_profile'):
            client = user.client_profile
            qs = ClientWorkoutPlan.objects.filter(client=client, is_active=True)
            day_of_week = self.request.query_params.get('day_of_week')
            if day_of_week is not None and day_of_week != '':
                try:
                    qs = qs.filter(day_of_week=int(day_of_week))
                except (ValueError, TypeError):
                    pass
            return qs.order_by('day_of_week', 'order')
        return ClientWorkoutPlan.objects.none()


# ------------------- Master Workout Plan Views -------------------
class MasterWorkoutPlanListCreateView(generics.ListCreateAPIView):
    """List or create Master Workout Plans (templates)."""
    serializer_class = MasterWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return MasterWorkoutPlan.objects.filter(is_active=True)
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            # Trainers see master plans they created or global system master plans (trainer=None)
            return MasterWorkoutPlan.objects.filter(
                models.Q(trainer=trainer) | models.Q(trainer__isnull=True),
                is_active=True
            ).distinct()
        return MasterWorkoutPlan.objects.none()


class MasterWorkoutPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a master workout plan."""
    serializer_class = MasterWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return MasterWorkoutPlan.objects.all()
        elif hasattr(user, 'trainer_profile'):
            return MasterWorkoutPlan.objects.filter(
                models.Q(trainer=user.trainer_profile) | models.Q(trainer__isnull=True)
            )
        return MasterWorkoutPlan.objects.none()


class MasterWorkoutPlanAddItemView(generics.CreateAPIView):
    """Add a scheduled exercise routine item to a master workout plan and sync to assigned clients."""
    serializer_class = MasterWorkoutPlanItemSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        master_plan_id = self.kwargs.get('pk')
        master_plan = generics.get_object_or_404(MasterWorkoutPlan, id=master_plan_id)
        user = self.request.user
        if hasattr(user, 'trainer_profile') and master_plan.trainer and master_plan.trainer != user.trainer_profile:
            raise PermissionDenied("You do not have permission to modify this master plan.")
        master_item = serializer.save(master_plan=master_plan)

        # Sync this new exercise item to all clients assigned / linked to this Master Program
        assigned_clients = set(master_plan.assigned_clients.filter(is_active=True))
        additional_clients = ClientProfile.objects.filter(
            workout_plans__master_plan=master_plan,
            workout_plans__is_active=True
        ).distinct()
        assigned_clients.update(additional_clients)

        for client in assigned_clients:
            client_trainer = master_plan.trainer
            if not client_trainer:
                link = TrainerClientLink.objects.filter(client=client, is_active=True).first()
                if link:
                    client_trainer = link.trainer

            if not client_trainer:
                continue

            # Ensure client is actively linked with trainer
            if not TrainerClientLink.objects.filter(trainer=client_trainer, client=client, is_active=True).exists():
                continue

            existing_orders = list(ClientWorkoutPlan.objects.filter(
                client=client,
                day_of_week=master_item.day_of_week
            ).values_list('order', flat=True))

            target_order = master_item.order
            if target_order in existing_orders:
                target_order = (max(existing_orders) if existing_orders else 0) + 1

            ClientWorkoutPlan.objects.get_or_create(
                trainer=client_trainer,
                client=client,
                exercise=master_item.exercise,
                day_of_week=master_item.day_of_week,
                defaults={
                    'sets': master_item.sets,
                    'reps': master_item.reps,
                    'time_per_rep_seconds': master_item.time_per_rep_seconds,
                    'order': target_order,
                    'notes': master_item.notes,
                    'master_plan': master_plan,
                    'is_active': True,
                }
            )


class MasterWorkoutPlanDeleteItemView(generics.DestroyAPIView):
    """Delete a routine item from a master workout plan."""
    queryset = MasterWorkoutPlanItem.objects.all()
    serializer_class = MasterWorkoutPlanItemSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        user = self.request.user
        if hasattr(user, 'trainer_profile') and instance.master_plan.trainer and instance.master_plan.trainer != user.trainer_profile:
            raise PermissionDenied("You do not have permission to modify this master plan.")
        instance.delete()


class AssignMasterWorkoutPlanView(generics.GenericAPIView):
    """Assign a master workout plan (with all its weekly exercises) to one or more clients."""
    serializer_class = AssignMasterWorkoutPlanSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        master_plan = generics.get_object_or_404(MasterWorkoutPlan, id=pk)
        user = request.user
        if not hasattr(user, 'trainer_profile') and not user.is_admin and not user.is_superuser:
            return Response({'error': 'Only trainers or admins can assign workout plans.'}, status=status.HTTP_403_FORBIDDEN)

        trainer = getattr(user, 'trainer_profile', None)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_ids = serializer.validated_data['client_ids']
        clear_existing = serializer.validated_data.get('clear_existing', False)

        assigned_clients = []
        master_items = list(master_plan.items.all())

        if not master_items:
            return Response(
                {'error': 'This master workout plan has no exercises added to it yet. Add exercises before assigning.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for client_id in client_ids:
            try:
                client = ClientProfile.objects.get(id=client_id)
            except ClientProfile.DoesNotExist:
                continue

            # Check trainer client link
            if trainer and not TrainerClientLink.objects.filter(trainer=trainer, client=client, is_active=True).exists():
                continue

            # Clear existing plans for this client if requested
            if clear_existing:
                if trainer:
                    ClientWorkoutPlan.objects.filter(trainer=trainer, client=client).delete()
                else:
                    ClientWorkoutPlan.objects.filter(client=client).delete()
                # Remove client from other master plans
                for other_mp in client.assigned_master_plans.exclude(id=master_plan.id):
                    other_mp.assigned_clients.remove(client)

            # Create workout plan entries for each item in the master plan
            for item in master_items:
                ClientWorkoutPlan.objects.create(
                    trainer=trainer or master_plan.trainer,
                    client=client,
                    exercise=item.exercise,
                    day_of_week=item.day_of_week,
                    sets=item.sets,
                    reps=item.reps,
                    time_per_rep_seconds=item.time_per_rep_seconds,
                    order=item.order,
                    notes=item.notes,
                    master_plan=master_plan,
                    is_active=True
                )

            master_plan.assigned_clients.add(client)
            assigned_clients.append(client.id)

        return Response({
            'success': True,
            'message': f"Master program '{master_plan.title}' successfully assigned to {len(assigned_clients)} client(s).",
            'master_plan_id': master_plan.id,
            'master_plan_title': master_plan.title,
            'assigned_clients': assigned_clients,
            'total_exercises_per_client': len(master_items)
        }, status=status.HTTP_200_OK)


# ------------------- Kcal Target Views -------------------


class DailyKcalTargetListView(generics.ListCreateAPIView):
    """Admin/Trainer can list and create kcal targets for clients."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['day_of_week', 'target_kcal']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return DailyKcalTarget.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return DailyKcalTarget.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        return DailyKcalTarget.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyKcalTargetCreateUpdateSerializer
        return DailyKcalTargetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instances = self.perform_create(serializer)  # Now returns list
        # Custom response
        output_serializer = DailyKcalTargetSerializer(instances, many=True, context={'request': request})
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Returns the list of created instances
        return serializer.save()


class DailyKcalTargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return DailyKcalTarget.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return DailyKcalTarget.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        return DailyKcalTarget.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DailyKcalTargetCreateUpdateSerializer
        return DailyKcalTargetSerializer


# ------------------- Kcal Log Views -------------------
class ClientKcalLogListView(generics.ListCreateAPIView):
    """Client can post his actual kcal; Admin/Trainer can view logs."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientKcalLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientKcalLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientKcalLog.objects.filter(client=user.client_profile)
        return ClientKcalLog.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClientKcalLogCreateSerializer
        return ClientKcalLogSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'client_profile'):
            raise PermissionDenied("Only clients can log kcal burned.")
        client = user.client_profile
        date = serializer.validated_data.get('date')
        existing_log = ClientKcalLog.objects.filter(client=client, date=date).first()
        if existing_log:
            existing_log.actual_kcal = serializer.validated_data.get('actual_kcal', existing_log.actual_kcal)
            if 'notes' in serializer.validated_data:
                existing_log.notes = serializer.validated_data['notes']
            existing_log.save()
            serializer.instance = existing_log
            return
        serializer.save(client=client)


class ClientKcalLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientKcalLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientKcalLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientKcalLog.objects.filter(client=user.client_profile)
        return ClientKcalLog.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClientKcalLogCreateSerializer
        return ClientKcalLogSerializer


class ClientKcalSummaryView(generics.GenericAPIView):
    """Client sees target vs actual for date range (default current week)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"error": "Only clients can access summary."}, status=403)
        client = user.client_profile

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        from datetime import date, timedelta
        today = date.today()
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        else:
            start = today - timedelta(days=today.weekday())  # Monday of current week
            end = start + timedelta(days=6)

        # Get targets
        targets = {t.day_of_week: t.target_kcal for t in DailyKcalTarget.objects.filter(client=client)}
        # Get logs
        logs = {log.date: log.actual_kcal for log in ClientKcalLog.objects.filter(client=client, date__gte=start, date__lte=end)}

        result = []
        current = start
        while current <= end:
            day_of_week = current.weekday()
            target = targets.get(day_of_week, 0)
            actual = logs.get(current)
            result.append({
                "date": current.isoformat(),
                "day": current.strftime("%A"),
                "target_kcal": target,
                "actual_kcal": actual,
                "achieved": actual is not None and actual >= target if target else None,
            })
            current += timedelta(days=1)

        return Response(result)
    





# ---------- Generic Mixin for Target Views ----------
class BaseTargetListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['day_of_week']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return self.model.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return self.model.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        return self.model.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return self.create_serializer
        return self.list_serializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instances = serializer.save()
        output_serializer = self.list_serializer(instances, many=True, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class BaseTargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return self.model.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return self.model.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        return self.model.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return self.update_serializer
        return self.detail_serializer


# ---------- Hydration Targets ----------
class HydrationTargetListView(BaseTargetListView):
    model = DailyHydrationTarget
    list_serializer = DailyHydrationTargetSerializer
    create_serializer = DailyHydrationTargetCreateUpdateSerializer


class HydrationTargetDetailView(BaseTargetDetailView):
    model = DailyHydrationTarget
    detail_serializer = DailyHydrationTargetSerializer
    update_serializer = DailyHydrationTargetCreateUpdateSerializer


# ---------- Hydration Logs ----------
class HydrationLogListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientHydrationLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientHydrationLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientHydrationLog.objects.filter(client=user.client_profile)
        return ClientHydrationLog.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClientHydrationLogCreateSerializer
        return ClientHydrationLogSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'client_profile'):
            raise PermissionDenied("Only clients can log hydration.")
        client = user.client_profile
        date = serializer.validated_data.get('date')
        existing_log = ClientHydrationLog.objects.filter(client=client, date=date).first()
        if existing_log:
            existing_log.actual_cups = serializer.validated_data.get('actual_cups', existing_log.actual_cups)
            if 'notes' in serializer.validated_data:
                existing_log.notes = serializer.validated_data['notes']
            existing_log.save()
            serializer.instance = existing_log
            return
        serializer.save(client=client)


class HydrationLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientHydrationLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientHydrationLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientHydrationLog.objects.filter(client=user.client_profile)
        return ClientHydrationLog.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClientHydrationLogCreateSerializer
        return ClientHydrationLogSerializer


# ---------- Sleep Targets ----------
class SleepTargetListView(BaseTargetListView):
    model = DailySleepTarget
    list_serializer = DailySleepTargetSerializer
    create_serializer = DailySleepTargetCreateUpdateSerializer


class SleepTargetDetailView(BaseTargetDetailView):
    model = DailySleepTarget
    detail_serializer = DailySleepTargetSerializer
    update_serializer = DailySleepTargetCreateUpdateSerializer


# ---------- Sleep Logs ----------
class SleepLogListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientSleepLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientSleepLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientSleepLog.objects.filter(client=user.client_profile)
        return ClientSleepLog.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClientSleepLogCreateSerializer
        return ClientSleepLogSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'client_profile'):
            raise PermissionDenied("Only clients can log sleep.")
        client = user.client_profile
        date = serializer.validated_data.get('date')
        if ClientSleepLog.objects.filter(client=client, date=date).exists():
            raise serializers.ValidationError({"date": "Log for this date already exists."})
        serializer.save(client=client)


class SleepLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_superuser:
            return ClientSleepLog.objects.all()
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return ClientSleepLog.objects.filter(
                client__trainer_links__trainer=trainer
            ).distinct()
        elif hasattr(user, 'client_profile'):
            return ClientSleepLog.objects.filter(client=user.client_profile)
        return ClientSleepLog.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClientSleepLogCreateSerializer
        return ClientSleepLogSerializer


# ---------- Streak & Achievement Views ----------
from fitnessApp.models import ClientStreak, ClientAchievement
from django.utils import timezone
from datetime import timedelta

class ClientCheckInView(generics.GenericAPIView):
    """
    Client daily check-in:
    - Increments streak if opened on consecutive days.
    - Tracks if this is the first open today (to display celebration popup & notification).
    - Evaluates weekly activity dots.
    - Evaluates and auto-unlocks achievement milestones.
    """
    permission_classes = [IsAuthenticated]

    def get_or_post(self, request):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"error": "Only clients can check in."}, status=403)
        client = user.client_profile

        today = timezone.localdate()
        streak_obj, created = ClientStreak.objects.get_or_create(
            client=client,
            defaults={
                'current_streak': 1,
                'longest_streak': 1,
                'last_activity_date': today,
            }
        )

        is_first_open_today = False

        if created:
            is_first_open_today = True
        else:
            last_date = streak_obj.last_activity_date
            if last_date is None:
                streak_obj.current_streak = 1
                streak_obj.last_activity_date = today
                is_first_open_today = True
                streak_obj.save()
            elif last_date == today:
                # Already checked in today
                is_first_open_today = False
            elif last_date == today - timedelta(days=1):
                # Consecutive day check-in!
                streak_obj.current_streak += 1
                if streak_obj.current_streak > streak_obj.longest_streak:
                    streak_obj.longest_streak = streak_obj.current_streak
                streak_obj.last_activity_date = today
                streak_obj.save()
                is_first_open_today = True
            else:
                # Gap of 2+ days: reset streak to 1
                streak_obj.current_streak = 1
                streak_obj.last_activity_date = today
                streak_obj.save()
                is_first_open_today = True

        # Compute activity dots for current week (Monday to Sunday)
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        # Days with check-in, kcal log, or hydration log
        kcal_dates = set(ClientKcalLog.objects.filter(client=client, date__gte=monday, date__lte=sunday).values_list('date', flat=True))
        hydration_dates = set(ClientHydrationLog.objects.filter(client=client, date__gte=monday, date__lte=sunday).values_list('date', flat=True))

        active_dates = kcal_dates | hydration_dates
        if streak_obj.last_activity_date and monday <= streak_obj.last_activity_date <= sunday:
            active_dates.add(streak_obj.last_activity_date)

        week_dots = []
        cur = monday
        lit_dots_count = 0
        while cur <= sunday:
            is_active = cur in active_dates
            if is_active:
                lit_dots_count += 1
            week_dots.append({
                "day_index": cur.weekday(),
                "day_name": cur.strftime("%a"),
                "date": cur.isoformat(),
                "is_active": is_active,
                "is_today": cur == today,
            })
            cur += timedelta(days=1)

        today_weekday = today.weekday()

        # 1. Evaluate full day hydration goal completion for today
        hyd_target = DailyHydrationTarget.objects.filter(client=client, day_of_week=today_weekday).first()
        target_cups = hyd_target.target_cups if hyd_target else 8
        today_hyd = ClientHydrationLog.objects.filter(client=client, date=today).first()
        actual_cups = today_hyd.actual_cups if today_hyd else 0
        hydration_goal_completed = (target_cups > 0 and actual_cups >= target_cups)

        # 2. Evaluate Goal Crusher: BOTH Diet Plan part and Kcal logs part must be completed
        # 2a. Diet Plan part: must have active diet plan, scheduled meals, and all meals completed today
        active_diet = ClientDietPlan.objects.filter(client=client, is_active=True).first()
        diet_completed = False
        if active_diet:
            diet_meals = active_diet.meals.all()
            total_meals = diet_meals.count()
            if total_meals > 0:
                completed_meals = ClientMealLog.objects.filter(
                    client=client,
                    meal_item__in=diet_meals,
                    date=today,
                    is_completed=True
                ).count()
                diet_completed = (completed_meals >= total_meals)

        # 2b. Kcal log part: must have logged kcal for today meeting or exceeding target
        kcal_target_obj = DailyKcalTarget.objects.filter(client=client, day_of_week=today_weekday).first()
        if kcal_target_obj and kcal_target_obj.target_kcal > 0:
            target_kcal = kcal_target_obj.target_kcal
        elif active_diet and active_diet.daily_calorie_target > 0:
            target_kcal = active_diet.daily_calorie_target
        else:
            target_kcal = 2000

        today_kcal = ClientKcalLog.objects.filter(client=client, date=today).first()
        actual_kcal = today_kcal.actual_kcal if today_kcal else 0
        kcal_completed = (actual_kcal >= target_kcal and target_kcal > 0)

        # Goal Crusher completed ONLY if both diet plan and kcal logs are completed
        goal_crusher_completed = (diet_completed and kcal_completed)

        # Evaluate achievement milestones
        milestone_definitions = [
            {
                "key": "first_step",
                "name": "First Step",
                "emoji": "🏆",
                "description": "Welcome! You started your daily fitness journey.",
                "condition": True,
            },
            {
                "key": "streak_3",
                "name": "3-Day Streak",
                "emoji": "🔥",
                "description": "Consistent warrior! 3 consecutive active days.",
                "condition": streak_obj.current_streak >= 3 or streak_obj.longest_streak >= 3,
            },
            {
                "key": "streak_7",
                "name": "7-Day Warrior",
                "emoji": "⚡",
                "description": "7 consecutive days strong! Building real discipline.",
                "condition": streak_obj.current_streak >= 7 or streak_obj.longest_streak >= 7,
            },
            {
                "key": "hydration_hero",
                "name": "Hydration Hero",
                "emoji": "💧",
                "description": "Reached your daily target water intake!",
                "condition": hydration_goal_completed,
            },
            {
                "key": "goal_crusher",
                "name": "Goal Crusher",
                "emoji": "🎯",
                "description": "Completed daily diet plan & hit calorie target!",
                "condition": goal_crusher_completed,
            },
            {
                "key": "workout_ready",
                "name": "Workout Ready",
                "emoji": "💪",
                "description": "Equipped with personalized training routine.",
                "condition": ClientWorkoutPlan.objects.filter(client=client, is_active=True).exists(),
            },
            {
                "key": "streak_14",
                "name": "14-Day Legend",
                "emoji": "🥇",
                "description": "Two full weeks of unstoppable momentum!",
                "condition": streak_obj.longest_streak >= 14,
            },
        ]

        newly_unlocked = []
        for m in milestone_definitions:
            if m["condition"]:
                ach, created_ach = ClientAchievement.objects.get_or_create(
                    client=client,
                    badge_key=m["key"],
                    defaults={
                        "name": m["name"],
                        "emoji": m["emoji"],
                        "description": m["description"],
                        "is_seen": False,
                    }
                )
                if created_ach or not ach.is_seen:
                    newly_unlocked.append({
                        "badge_key": m["key"],
                        "name": m["name"],
                        "emoji": m["emoji"],
                        "description": m["description"],
                    })
            else:
                # If daily goal badge is not completed today, remove any stale achievement record
                if m["key"] in ("hydration_hero", "goal_crusher"):
                    ClientAchievement.objects.filter(client=client, badge_key=m["key"]).delete()

        # All badges list
        earned_keys = set(ClientAchievement.objects.filter(client=client).values_list('badge_key', flat=True))
        all_badges = []
        for m in milestone_definitions:
            all_badges.append({
                "badge_key": m["key"],
                "name": m["name"],
                "emoji": m["emoji"],
                "description": m["description"],
                "earned": m["key"] in earned_keys,
            })

        return Response({
            "streak": {
                "current_streak": streak_obj.current_streak,
                "longest_streak": streak_obj.longest_streak,
                "last_activity_date": streak_obj.last_activity_date.isoformat() if streak_obj.last_activity_date else None,
                "is_first_open_today": is_first_open_today,
                "lit_dots": lit_dots_count,
                "week_dots": week_dots,
            },
            "badges": all_badges,
            "newly_unlocked": newly_unlocked,
        })

    def get(self, request):
        return self.get_or_post(request)

    def post(self, request):
        return self.get_or_post(request)


class MarkAchievementSeenView(generics.GenericAPIView):
    """Marks client achievements as seen so celebration pop-ups only appear once."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"error": "Only clients can update achievements."}, status=403)
        client = user.client_profile

        badge_keys = request.data.get('badge_keys', [])
        if badge_keys:
            ClientAchievement.objects.filter(client=client, badge_key__in=badge_keys).update(is_seen=True)
        else:
            ClientAchievement.objects.filter(client=client).update(is_seen=True)

        return Response({"status": "success", "message": "Achievements marked as seen."})


# ---------- Diet & Nutrition Views ----------
from fitnessApp.models import ClientDietPlan, ClientDietMealItem, ClientMealLog
from fitnessApp.api.serializers import (
    ClientDietPlanSerializer,
    ClientDietPlanCreateUpdateSerializer,
    ClientDietMealItemSerializer,
)

class DietPlanListCreateView(generics.ListCreateAPIView):
    """
    List & create diet plans:
    - Admin: can see all plans, create for any client.
    - Trainer: can see/create plans for their assigned clients.
    - Client: can see their own diet plans.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ClientDietPlan.objects.all().select_related('client__user', 'trainer__user').prefetch_related('meals')

        client_id = self.request.query_params.get('client_id')
        if client_id:
            qs = qs.filter(client_id=client_id)

        if user.is_admin or user.is_superuser:
            return qs
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return qs.filter(client__trainer_links__trainer=trainer, client__trainer_links__is_active=True).distinct()
        elif hasattr(user, 'client_profile'):
            return qs.filter(client=user.client_profile)
        return ClientDietPlan.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClientDietPlanCreateUpdateSerializer
        return ClientDietPlanSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_admin and not user.is_superuser and not hasattr(user, 'trainer_profile'):
            raise PermissionDenied("Only trainers and admins can create diet plans.")
        serializer.save()


class DietPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a diet plan."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ClientDietPlan.objects.all().select_related('client__user', 'trainer__user').prefetch_related('meals')
        if user.is_admin or user.is_superuser:
            return qs
        elif hasattr(user, 'trainer_profile'):
            trainer = user.trainer_profile
            return qs.filter(client__trainer_links__trainer=trainer, client__trainer_links__is_active=True).distinct()
        elif hasattr(user, 'client_profile'):
            return qs.filter(client=user.client_profile)
        return ClientDietPlan.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClientDietPlanCreateUpdateSerializer
        return ClientDietPlanSerializer


class ClientMyDietPlanView(generics.GenericAPIView):
    """Returns currently active diet plan for authenticated client."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"error": "Only clients can access this."}, status=403)
        client = user.client_profile

        active_plan = ClientDietPlan.objects.filter(client=client, is_active=True).prefetch_related('meals').first()
        if not active_plan:
            active_plan = ClientDietPlan.objects.filter(client=client).prefetch_related('meals').first()

        if not active_plan:
            return Response({"plan": None, "message": "No diet plan assigned yet."})

        serializer = ClientDietPlanSerializer(active_plan, context={'request': request})
        return Response({"plan": serializer.data})


class ClientToggleMealView(generics.GenericAPIView):
    """Toggles today's completion status for a specific meal."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"error": "Only clients can toggle meals."}, status=403)
        client = user.client_profile

        try:
            meal = ClientDietMealItem.objects.get(pk=pk, diet_plan__client=client)
        except ClientDietMealItem.DoesNotExist:
            return Response({"error": "Meal item not found for this client."}, status=404)

        from django.utils import timezone
        today = timezone.localdate()

        log = ClientMealLog.objects.filter(client=client, meal_item=meal, date=today).first()
        if log:
            log.is_completed = not log.is_completed
            log.save()
            new_state = log.is_completed
        else:
            ClientMealLog.objects.create(client=client, meal_item=meal, date=today, is_completed=True)
            new_state = True

        return Response({
            "status": "success",
            "meal_id": meal.id,
            "done": new_state,
            "date": today.isoformat(),
        })


class ClientNotificationsView(generics.GenericAPIView):
    """
    Returns real, live notifications for authenticated client:
    - Today's workout routine (or rest day)
    - Nutrition & Diet plan (next pending meal or diet plan completed)
    - Hydration status (today's cups vs target)
    - Streak milestone / consistency status
    - Assigned coach information
    - Recently unlocked badges
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'client_profile'):
            return Response({"notifications": []})

        client = user.client_profile
        today = timezone.localdate()
        today_weekday = today.weekday()
        notifications = []

        # 1. Today's Workout Routine
        today_workouts = list(ClientWorkoutPlan.objects.filter(
            client=client,
            day_of_week=today_weekday,
            is_active=True
        ).select_related('exercise', 'master_plan'))

        if today_workouts:
            ex_names = [w.exercise.title for w in today_workouts[:2]]
            more_count = len(today_workouts) - len(ex_names)
            ex_summary = ", ".join(ex_names)
            if more_count > 0:
                ex_summary += f" +{more_count} more"
            plan_name = today_workouts[0].master_plan.title if today_workouts[0].master_plan else "Daily Training"
            notifications.append({
                "id": "workout_today",
                "icon": "💪",
                "title": f"Today's Routine: {plan_name}",
                "body": f"{len(today_workouts)} exercise{'s' if len(today_workouts) > 1 else ''} scheduled ({ex_summary}). Let's get moving!",
                "time": "Today",
                "color": "0xFF2C4BFF",
            })
        else:
            has_any_workout = ClientWorkoutPlan.objects.filter(client=client, is_active=True).exists()
            if has_any_workout:
                notifications.append({
                    "id": "workout_rest",
                    "icon": "🧘",
                    "title": "Rest & Recovery Day",
                    "body": "No workout exercises scheduled for today. Rest up, stretch, and hydrate!",
                    "time": "Today",
                    "color": "0xFF00C9FF",
                })
            else:
                notifications.append({
                    "id": "workout_none",
                    "icon": "💪",
                    "title": "Workout Routine",
                    "body": "Your trainer has not assigned an active workout plan yet. Check back soon!",
                    "time": "Today",
                    "color": "0xFF2C4BFF",
                })

        # 2. Nutrition & Diet Plan
        active_diet = ClientDietPlan.objects.filter(client=client, is_active=True).first()
        if active_diet:
            diet_meals = list(active_diet.meals.all())
            if diet_meals:
                completed_ids = set(ClientMealLog.objects.filter(
                    client=client,
                    meal_item__in=diet_meals,
                    date=today,
                    is_completed=True
                ).values_list('meal_item_id', flat=True))
                pending_meals = [m for m in diet_meals if m.id not in completed_ids]

                if pending_meals:
                    next_meal = pending_meals[0]
                    notifications.append({
                        "id": f"meal_{next_meal.id}",
                        "icon": next_meal.emoji or "🥗",
                        "title": f"Meal Reminder: {next_meal.name}",
                        "body": f"{next_meal.get_meal_type_display()} · {next_meal.calories} kcal ({len(pending_meals)} pending meal{'s' if len(pending_meals) > 1 else ''} today).",
                        "time": next_meal.time_label or "Upcoming",
                        "color": "0xFF00E5A0",
                    })
                else:
                    notifications.append({
                        "id": "diet_complete",
                        "icon": "🥗",
                        "title": "Diet Plan Completed! 🌟",
                        "body": f"All {len(diet_meals)} meals logged today. Total: {active_diet.daily_calorie_target} kcal. Keep it up!",
                        "time": "Today",
                        "color": "0xFF00E5A0",
                    })
            else:
                notifications.append({
                    "id": "diet_plan_active",
                    "icon": "🥗",
                    "title": f"Diet Plan: {active_diet.title}",
                    "body": f"Daily target: {active_diet.daily_calorie_target} kcal, {active_diet.protein_grams}g protein.",
                    "time": "Active",
                    "color": "0xFF00E5A0",
                })
        else:
            notifications.append({
                "id": "diet_none",
                "icon": "🥗",
                "title": "Nutrition Tracker",
                "body": "No active diet plan assigned yet. Ask your coach to create a personalized meal plan.",
                "time": "Today",
                "color": "0xFF00E5A0",
            })

        # Daily 12:00 PM Diet Goals Reminder
        notifications.append({
            "id": "daily_diet_reminder_12pm",
            "icon": "🥗",
            "title": "Daily Diet Reminder",
            "body": "Do not forget to complete your daily fitness diet goals!",
            "time": "12:00 PM Daily",
            "color": "0xFF00E5A0",
        })

        # 3. Hydration Progress
        hyd_target_obj = DailyHydrationTarget.objects.filter(client=client, day_of_week=today_weekday).first()
        target_cups = hyd_target_obj.target_cups if hyd_target_obj else 8
        today_hyd = ClientHydrationLog.objects.filter(client=client, date=today).first()
        actual_cups = today_hyd.actual_cups if today_hyd else 0

        if actual_cups >= target_cups and target_cups > 0:
            notifications.append({
                "id": "hyd_complete",
                "icon": "💧",
                "title": "Hydration Goal Completed! 💧",
                "body": f"Great job! You reached {actual_cups}/{target_cups} cups today. Hydration Hero unlocked!",
                "time": "Goal Met",
                "color": "0xFF00C9FF",
            })
        else:
            pct = int((actual_cups / target_cups * 100)) if target_cups > 0 else 0
            notifications.append({
                "id": "hyd_progress",
                "icon": "💧",
                "title": "Daily Water Intake 💧",
                "body": f"{actual_cups} / {target_cups} cups logged today ({pct}%). Drink water throughout the day!",
                "time": "Today",
                "color": "0xFF00C9FF",
            })

        # 4. Streak & Consistency
        streak = ClientStreak.objects.filter(client=client).first()
        if streak:
            notifications.append({
                "id": "streak_status",
                "icon": "🔥",
                "title": f"Day {streak.current_streak} Active Streak!",
                "body": f"Keep going strong! Your personal best is {streak.longest_streak} consecutive active days.",
                "time": "Active",
                "color": "0xFFFF6B35",
            })

        # 5. Coach / Assigned Trainer
        active_link = client.trainer_links.filter(is_active=True).select_related('trainer__user').first()
        if active_link and active_link.trainer:
            coach_user = active_link.trainer.user
            coach_name = coach_user.get_full_name() or coach_user.username or coach_user.email
            notifications.append({
                "id": "coach_info",
                "icon": "👨‍🏫",
                "title": f"Coach: {coach_name}",
                "body": f"{coach_name} is actively monitoring your workouts and nutrition routines.",
                "time": "Connected",
                "color": "0xFF9C7BFF",
            })

        # 6. Unlocked Achievements
        recent_achs = list(ClientAchievement.objects.filter(client=client).order_by('-unlocked_at')[:2])
        for ach in recent_achs:
            notifications.append({
                "id": f"ach_{ach.id}",
                "icon": ach.emoji,
                "title": f"Badge: {ach.name}",
                "body": ach.description,
                "time": ach.unlocked_at.strftime("%b %d") if ach.unlocked_at else "Earned",
                "color": "0xFFFFD700",
            })

        return Response({"notifications": notifications})
