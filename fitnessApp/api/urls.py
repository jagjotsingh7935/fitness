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

    # Master Workout Plan (Templates) endpoints
    path('master-workout-plans/', MasterWorkoutPlanListCreateView.as_view(), name='master-workoutplan-list'),
    path('master-workout-plans/create/', MasterWorkoutPlanListCreateView.as_view(), name='master-workoutplan-create'),
    path('master-workout-plans/<int:pk>/', MasterWorkoutPlanDetailView.as_view(), name='master-workoutplan-detail'),
    path('master-workout-plans/<int:pk>/items/', MasterWorkoutPlanAddItemView.as_view(), name='master-workoutplan-add-item'),
    path('master-workout-plans/items/<int:pk>/', MasterWorkoutPlanDeleteItemView.as_view(), name='master-workoutplan-delete-item'),
    path('master-workout-plans/<int:pk>/assign/', AssignMasterWorkoutPlanView.as_view(), name='master-workoutplan-assign'),

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

    # Client Streak & Achievements
    path('client-checkin/', ClientCheckInView.as_view(), name='client-checkin'),
    path('client-achievements/mark-seen/', MarkAchievementSeenView.as_view(), name='client-achievements-mark-seen'),

    # Diet & Nutrition Plans
    path('diet-plans/', DietPlanListCreateView.as_view(), name='diet-plan-list'),
    path('diet-plans/<int:pk>/', DietPlanDetailView.as_view(), name='diet-plan-detail'),
    path('my-diet-plan/', ClientMyDietPlanView.as_view(), name='my-diet-plan'),
    path('my-diet-plan/meals/<int:pk>/toggle/', ClientToggleMealView.as_view(), name='my-diet-meal-toggle'),

    # Real-time Client Notifications
    path('client-notifications/', ClientNotificationsView.as_view(), name='client-notifications'),
]