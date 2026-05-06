from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from accounts.models import Category, TrainerProfile, ClientProfile, TrainerClientLink, Role, EmailOTP
from accounts.api.serializers import (
    CustomTokenObtainPairSerializer, UserSerializer, 
    CategorySerializer, TrainerSerializer, TrainerCreateSerializer, 
    TrainerDetailSerializer, TrainerListSerializer,
    ClientSerializer, ClientCreateSerializer, ClientDetailSerializer, ClientListSerializer,
    TrainerClientLinkSerializer, RoleSerializer,
    AdminCreateSerializer, AdminDetailSerializer, AdminListSerializer
)
from .permissions import AdminOnlyPermission, CustomModelPermissions

User = get_user_model()


# Pagination Class
class UserListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    
    def get_page_size(self, request):
        page_size = request.query_params.get('page_size')
        return int(page_size) if page_size else self.page_size

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'results': data,
            'filters': self.request.query_params.dict(),
        })


# Authentication Views
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("Received POST request with data:", request.data)
        serializer = self.get_serializer(data=request.data)
        print("Serializer initialized with data")

        try:
            print("Validating serializer...")
            serializer.is_valid(raise_exception=True)
            print("Serializer validation successful")
        except TokenError as e:
            print(f"Token error occurred: {e}")
            raise InvalidToken(e.args[0])

        user = serializer.user
        print(f"User retrieved from serializer: {user}")

        user.last_login = now()
        user.save(update_fields=['last_login'])
        print(f"Updated last_login for user: {user}")

        user_serializer = UserSerializer(user, context={'request': request})
        print("User data serialized")

        response_data = {
            'accessToken': serializer.validated_data['access'],
            'refreshToken': serializer.validated_data['refresh'],
            'user': user_serializer.data
        }
        print("Response data prepared:", response_data)

        return Response(response_data, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)


# OTP Views
class RequestOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email required'}, status=400)
        EmailOTP.send_otp(email)
        return Response({'message': 'OTP sent to email'})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if EmailOTP.verify_otp(email, otp):
            user, created = User.objects.get_or_create(
                email=email, 
                defaults={'username': email, 'is_client': True}
            )
            if created:
                ClientProfile.objects.create(user=user)
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user, context={'request': request}).data
            })
        return Response({'error': 'Invalid or expired OTP'}, status=400)


# Admin Views
class AdminSignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = AdminCreateSerializer
    permission_classes = [AdminOnlyPermission]

    @transaction.atomic
    def perform_create(self, serializer):
        admin = serializer.save()
        print(f"New admin created: {admin.email}")
        return admin


class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.filter(is_admin=True)
    serializer_class = AdminDetailSerializer
    permission_classes = [AdminOnlyPermission]


class AdminListView(generics.ListAPIView):
    queryset = User.objects.filter(is_admin=True)
    serializer_class = AdminListSerializer
    permission_classes = [AdminOnlyPermission]
    pagination_class = UserListPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset


# Trainer Views
class TrainerSignUpView(generics.CreateAPIView):
    queryset = TrainerProfile.objects.all()
    serializer_class = TrainerCreateSerializer
    permission_classes = [AdminOnlyPermission]

    @transaction.atomic
    def perform_create(self, serializer):
        trainer = serializer.save(admin=self.request.user)
        print(f"New trainer created: {trainer.user.email} under admin {self.request.user.email}")
        return trainer


class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TrainerProfile.objects.all()
    serializer_class = TrainerDetailSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = TrainerProfile


class TrainerListView(generics.ListAPIView):
    queryset = TrainerProfile.objects.all()
    serializer_class = TrainerListSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = TrainerProfile
    pagination_class = UserListPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by admin if not superuser
        if not self.request.user.is_superuser and self.request.user.is_admin:
            queryset = queryset.filter(admin=self.request.user)
        
        # Apply filters
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        
        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        return queryset


# Client Views
class ClientSignUpView(generics.CreateAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientCreateSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        client = serializer.save()
        print(f"New client created: {client.user.email}")
        return client


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientDetailSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = ClientProfile


class ClientListView(generics.ListAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientListSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = ClientProfile
    pagination_class = UserListPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        
        trainer_id = self.request.query_params.get('trainer')
        if trainer_id:
            queryset = queryset.filter(trainer_links__trainer__id=trainer_id, trainer_links__is_active=True)
        
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        return queryset


# Role Views
class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AdminOnlyPermission]

    def perform_create(self, serializer):
        role = serializer.save()
        print(f"Role created: {role.name} by {self.request.user.email}")
        return role


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AdminOnlyPermission]


# ViewSets for additional functionality
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [CustomModelPermissions]
    permission_model = Category

    @action(detail=False, methods=['get'])
    def all_categories(self, request):
        if request.user.is_admin or request.user.is_superuser:
            categories = Category.objects.all()
        else:
            categories = Category.objects.filter(is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class TrainerProfileViewSet(viewsets.ModelViewSet):
    queryset = TrainerProfile.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = TrainerProfile

    @action(detail=True, methods=['post'])
    def add_categories(self, request, pk=None):
        trainer = self.get_object()
        category_ids = request.data.get('category_ids', [])
        categories = Category.objects.filter(id__in=category_ids, is_active=True)
        trainer.categories.add(*categories)
        serializer = self.get_serializer(trainer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_categories(self, request, pk=None):
        trainer = self.get_object()
        category_ids = request.data.get('category_ids', [])
        categories = Category.objects.filter(id__in=category_ids)
        trainer.categories.remove(*categories)
        serializer = self.get_serializer(trainer)
        return Response(serializer.data)


class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = ClientProfile

    @action(detail=True, methods=['post'])
    def add_categories(self, request, pk=None):
        client = self.get_object()
        category_ids = request.data.get('category_ids', [])
        categories = Category.objects.filter(id__in=category_ids, is_active=True)
        client.categories.add(*categories)
        serializer = self.get_serializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_categories(self, request, pk=None):
        client = self.get_object()
        category_ids = request.data.get('category_ids', [])
        categories = Category.objects.filter(id__in=category_ids)
        client.categories.remove(*categories)
        serializer = self.get_serializer(client)
        return Response(serializer.data)


class TrainerClientLinkViewSet(viewsets.ModelViewSet):
    queryset = TrainerClientLink.objects.all()
    serializer_class = TrainerClientLinkSerializer
    permission_classes = [CustomModelPermissions]
    permission_model = TrainerClientLink

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        link = self.get_object()
        link.is_active = not link.is_active
        link.save()
        return Response({'status': 'updated', 'is_active': link.is_active})

    @action(detail=True, methods=['post'])
    def toggle_subscribed(self, request, pk=None):
        link = self.get_object()
        link.is_subscribed = not link.is_subscribed
        link.save()
        return Response({'status': 'updated', 'is_subscribed': link.is_subscribed})