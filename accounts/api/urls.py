from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

# Router for ViewSets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'trainers-viewset', views.TrainerProfileViewSet)
router.register(r'clients-viewset', views.ClientProfileViewSet)
router.register(r'trainer-client-links', views.TrainerClientLinkViewSet)
router.register(r'category-list', views.CategoryListForProfile, basename='category-list')


urlpatterns = [
    # Authentication endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', views.LogoutView.as_view(), name='logout-view'),
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # OTP Authentication
    path('request-otp/', views.RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    
    # Admin endpoints
    path('signup/admin/', views.AdminSignUpView.as_view(), name='admin-signup'),
    path('admin/<int:pk>/', views.AdminDetailView.as_view(), name='admin-detail'),
    path('admin/', views.AdminListView.as_view(), name='admin-list'),
    
    # Trainer endpoints
    path('signup/trainer/', views.TrainerSignUpView.as_view(), name='trainer-signup'),
    path('trainer/<int:pk>/', views.TrainerDetailView.as_view(), name='trainer-detail'),
    path('trainer/', views.TrainerListView.as_view(), name='trainer-list'),
    
    # Client endpoints
    path('signup/client/', views.ClientSignUpView.as_view(), name='client-signup'),
    path('client/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('client/', views.ClientListView.as_view(), name='client-list'),
    
    # Role endpoints
    path('roles/', views.RoleListCreateView.as_view(), name='role_list_create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),



    #Trainer By Categories
    path('trainers-by-categories/', views.TrainersByCategoriesView.as_view(), name='trainers-by-categories'),


    #Trainer Clients List
    path('trainers-client-list/', views.TrainerClientsView.as_view(), name='trainers-client-list'),

    # Assign Trainer to Client
    path('assign-trainer/', views.AssignTrainerToClientView.as_view(), name='assign-trainer'),


    

    
    # Include router URLs
    path('', include(router.urls)),
]