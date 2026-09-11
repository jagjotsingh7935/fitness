from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from accounts.models import Category, TrainerProfile, ClientProfile, TrainerClientLink, Role, EmailOTP
from accounts.api.serializers import *
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
        if request.user.is_client and hasattr(request.user, 'client_profile'):
            serializer = ClientDetailSerializer(request.user.client_profile, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.user.is_trainer and hasattr(request.user, 'trainer_profile'):
            serializer = TrainerDetailSerializer(request.user.trainer_profile, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        if request.user.is_client and hasattr(request.user, 'client_profile'):
            serializer = ClientDetailSerializer(
                request.user.client_profile,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.user.is_trainer and hasattr(request.user, 'trainer_profile'):
            serializer = TrainerDetailSerializer(
                request.user.trainer_profile,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = UserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
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
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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
        print(f"[toggle_active] Request received for TrainerClientLink ID: {pk}")

        link = self.get_object()
        print(f"[toggle_active] Current is_active value: {link.is_active}")

        link.is_active = not link.is_active
        link.save()

        print(f"[toggle_active] Updated is_active value: {link.is_active}")

        return Response({
            'status': 'updated',
            'is_active': link.is_active
        })

    @action(detail=True, methods=['post'])
    def toggle_subscribed(self, request, pk=None):
        print(f"[toggle_subscribed] Request received for TrainerClientLink ID: {pk}")

        link = self.get_object()
        print(f"[toggle_subscribed] Current is_subscribed value: {link.is_subscribed}")

        link.is_subscribed = not link.is_subscribed
        link.save()

        print(f"[toggle_subscribed] Updated is_subscribed value: {link.is_subscribed}")

        return Response({
            'status': 'updated',
            'is_subscribed': link.is_subscribed
        })





# ViewSets for additional functionality
class CategoryListForProfile(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def all_categories(self, request):
        
        categories = Category.objects.all()
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)



class TrainersByCategoriesView(APIView):
    """
    Post /api/accounts/trainers-by-categories/
    
    Returns list of trainers that have at least one of the given categories.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.data.get('category_ids')
        if raw is None:
            return Response(
                {"error": "Please provide 'category_ids' parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize to a flat list of strings
        if isinstance(raw, int):
            raw = [str(raw)]
        elif isinstance(raw, str):
            raw = [raw]
        elif isinstance(raw, list):
            # Convert every element to string (handles ints inside the list)
            raw = [str(item) for item in raw]
        else:
            return Response(
                {"error": "Invalid format for category_ids."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Now split comma-separated values and collect valid integer IDs
        cat_ids = []
        for item in raw:
            for part in item.split(','):
                part = part.strip()
                if part.isdigit():
                    cat_ids.append(int(part))

        if not cat_ids:
            return Response(
                {"error": "No valid category IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Query trainers
        trainers = TrainerProfile.objects.filter(
            categories__id__in=cat_ids,
            is_active=True
        ).distinct()

        serializer = TrainerProfileSerializer(trainers, many=True)
        return Response(serializer.data)

class TrainerClientsView(APIView):
    """
    GET /accounts/api/trainers-client-list/
    Returns list of active clients linked to the authenticated trainer.
    Includes client details with their category IDs.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if the user has a trainer profile
        if not hasattr(user, 'trainer_profile'):
            return Response(
                {"error": "User is not a trainer."},
                status=status.HTTP_403_FORBIDDEN
            )

        trainer_profile = user.trainer_profile

        # Get active links (is_active=True)
        links = TrainerClientLink.objects.filter(
            trainer=trainer_profile,
            is_active=True
        ).select_related('client', 'client__user')

        # Serialize the links; each link includes client with categories
        serializer = TrainerClientLinkSerializer(links, many=True)
        return Response(serializer.data)


class AssignTrainerToClientView(APIView):
    """
    POST /accounts/api/assign-trainer/
    Assigns or updates TrainerProfile links for a ClientProfile.
    Accepts:
      - {"client_id": 1, "trainer_ids": [2, 3, 5]} (syncs/unlinks coaches)
      - {"client_id": 1, "trainer_id": 2} (single coach assign)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        raw_client_id = request.data.get('client_id')
        raw_trainer_ids = request.data.get('trainer_ids')
        raw_trainer_id = request.data.get('trainer_id')

        if raw_client_id is None:
            return Response(
                {"error": "'client_id' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client_id = int(str(raw_client_id).strip())
        except (ValueError, TypeError):
            return Response(
                {"error": "client_id must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find client profile by id or user_id
            client_profile = ClientProfile.objects.filter(id=client_id).first()
            if not client_profile:
                client_profile = ClientProfile.objects.filter(user_id=client_id).first()

            if not client_profile:
                return Response(
                    {"error": f"Client with ID {client_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 1. Multi-trainer sync & unlinking
            if raw_trainer_ids is not None and isinstance(raw_trainer_ids, list):
                target_trainer_ids = []
                for tid in raw_trainer_ids:
                    try:
                        target_trainer_ids.append(int(str(tid).strip()))
                    except (ValueError, TypeError):
                        pass

                # Deactivate links not in target list (unlink unselected coaches)
                TrainerClientLink.objects.filter(
                    client=client_profile,
                    is_active=True
                ).exclude(trainer__id__in=target_trainer_ids).update(is_active=False)

                # Activate or create links in target list
                for t_id in target_trainer_ids:
                    trainer_profile = TrainerProfile.objects.filter(id=t_id).first() or TrainerProfile.objects.filter(user_id=t_id).first()
                    if trainer_profile:
                        link, created = TrainerClientLink.objects.get_or_create(
                            client=client_profile,
                            trainer=trainer_profile,
                            defaults={'is_active': True, 'is_subscribed': True}
                        )
                        link.is_active = True
                        link.is_subscribed = True
                        link.save()

                active_coaches = [
                    {
                        'id': l.trainer.id,
                        'name': l.trainer.user.get_full_name() or l.trainer.user.email,
                        'specialization': l.trainer.specialization
                    }
                    for l in TrainerClientLink.objects.filter(client=client_profile, is_active=True).select_related('trainer__user')
                ]

                return Response({
                    "message": "Coach assignments updated successfully.",
                    "client_id": client_profile.id,
                    "active_trainers": active_coaches,
                }, status=status.HTTP_200_OK)

            # 2. Single trainer assignment fallback
            if raw_trainer_id is not None:
                trainer_id = int(str(raw_trainer_id).strip())
                trainer_profile = TrainerProfile.objects.filter(id=trainer_id).first() or TrainerProfile.objects.filter(user_id=trainer_id).first()
                if not trainer_profile:
                    return Response({"error": f"Trainer with ID {trainer_id} not found."}, status=status.HTTP_404_NOT_FOUND)

                link, created = TrainerClientLink.objects.get_or_create(
                    client=client_profile,
                    trainer=trainer_profile,
                    defaults={'is_active': True, 'is_subscribed': True}
                )
                link.is_active = True
                link.is_subscribed = True
                link.save()

                return Response({
                    "message": "Trainer assigned to client successfully.",
                    "client_id": client_profile.id,
                    "trainer_id": trainer_profile.id,
                    "client_name": client_profile.user.get_full_name() or client_profile.user.email,
                    "trainer_name": trainer_profile.user.get_full_name() or trainer_profile.user.email,
                    "is_active": link.is_active,
                }, status=status.HTTP_200_OK)

            return Response(
                {"error": "Please provide 'trainer_ids' list or 'trainer_id'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to update coach assignments: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

