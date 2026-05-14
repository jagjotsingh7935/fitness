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
            return ClientWorkoutPlan.objects.filter(client=client, is_active=True).order_by('day_of_week', 'order')
        return ClientWorkoutPlan.objects.none()
    




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
        if ClientKcalLog.objects.filter(client=client, date=date).exists():
            raise serializers.ValidationError({"date": "Log for this date already exists. Use update."})
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
        if ClientHydrationLog.objects.filter(client=client, date=date).exists():
            raise serializers.ValidationError({"date": "Log for this date already exists."})
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