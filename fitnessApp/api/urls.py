from django.urls import path
from fitnessApp.api.views import *


urlpatterns = [
        # Exercise endpoints
    path('exercises/', ExerciseListView.as_view(), name='exercise-list'),
    path('exercises/<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),
    path('exercises/create/', ExerciseCreateView.as_view(), name='exercise-create'),
    path('exercises/<int:pk>/update/', ExerciseUpdateView.as_view(), name='exercise-update'),
    path('exercises/<int:pk>/delete/', ExerciseDeleteView.as_view(), name='exercise-delete'),

    # Workout Plan endpoints
    path('workout-plans/', WorkoutPlanListView.as_view(), name='workoutplan-list'),
    path('workout-plans/create/', WorkoutPlanCreateView.as_view(), name='workoutplan-create'),
    path('workout-plans/<int:pk>/', WorkoutPlanDetailView.as_view(), name='workoutplan-detail'),
    path('my-workout-plans/', ClientWorkoutPlanByDayView.as_view(), name='my-workout-plans'),

        # Kcal target endpoints
    path('kcal-targets/', DailyKcalTargetListView.as_view(), name='kcaltarget-list'),
    path('kcal-targets/<int:pk>/', DailyKcalTargetDetailView.as_view(), name='kcaltarget-detail'),

    # Kcal log endpoints
    path('kcal-logs/', ClientKcalLogListView.as_view(), name='kcallog-list'),
    path('kcal-logs/<int:pk>/', ClientKcalLogDetailView.as_view(), name='kcallog-detail'),

    # Kcal summary for client
    path('kcal-summary/', ClientKcalSummaryView.as_view(), name='kcal-summary'),


        # Hydration targets & logs
    path('hydration-targets/', HydrationTargetListView.as_view(), name='hydration-target-list'),
    path('hydration-targets/<int:pk>/', HydrationTargetDetailView.as_view(), name='hydration-target-detail'),
    path('hydration-logs/', HydrationLogListView.as_view(), name='hydration-log-list'),
    path('hydration-logs/<int:pk>/', HydrationLogDetailView.as_view(), name='hydration-log-detail'),

    # Sleep targets & logs
    path('sleep-targets/', SleepTargetListView.as_view(), name='sleep-target-list'),
    path('sleep-targets/<int:pk>/', SleepTargetDetailView.as_view(), name='sleep-target-detail'),
    path('sleep-logs/', SleepLogListView.as_view(), name='sleep-log-list'),
    path('sleep-logs/<int:pk>/', SleepLogDetailView.as_view(), name='sleep-log-detail'),

    
]