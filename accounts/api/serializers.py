from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from password_generator import PasswordGenerator
from accounts.models import User, Category, TrainerProfile, ClientProfile, TrainerClientLink, Role, EmailOTP

pwo = PasswordGenerator()
pwo.maxlen = 8

User = get_user_model()


# Token Serializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            try:
                user = User.objects.get(username__iexact=username)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass
        
        data = super().validate(attrs)
        self.user = self.user
        return data


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'profile_id', 'username', 'full_name', 'email', 'is_admin', 'is_trainer', 'is_client', 'roles']

    def get_full_name(self, user):
        if user.is_admin:
            return user.email
        elif user.is_trainer and hasattr(user, 'trainer_profile'):
            return f"{user.first_name} {user.last_name}".strip() or user.email
        elif user.is_client and hasattr(user, 'client_profile'):
            return f"{user.first_name} {user.last_name}".strip() or user.email
        return user.email
            
    def get_profile_id(self, user):
        if user.is_admin:
            return user.id
        elif user.is_trainer and hasattr(user, 'trainer_profile'):
            return user.trainer_profile.id
        elif user.is_client and hasattr(user, 'client_profile'):
            return user.client_profile.id
        return None
            
    def get_roles(self, user):
        return [group.name for group in user.groups.all()]


# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'icon_url', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_icon_url(self, obj):
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None



# Trainer Serializers
class TrainerCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(write_only=True, required=False)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True), 
        many=True, 
        write_only=True,
        required=False
    )

    class Meta:
        model = TrainerProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'specialization', 'bio', 
                  'avatar', 'phone', 'is_active', 'category_ids', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def to_internal_value(self, data):
        """Handle FormData conversion for category_ids: convert '1,2,3' to [1,2,3]."""
        print("Raw data received:", data)
        
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        
        if 'category_ids' in mutable_data:
            category_ids_value = mutable_data.get('category_ids')
            
            if isinstance(category_ids_value, str):
                if ',' in category_ids_value:
                    category_ids_list = [int(id.strip()) for id in category_ids_value.split(',') if id.strip()]
                    mutable_data.setlist('category_ids', category_ids_list)
                    print(f"Converted category_ids: {category_ids_list}")
                elif category_ids_value:
                    category_ids_list = [int(category_ids_value)]
                    mutable_data.setlist('category_ids', category_ids_list)
                    print(f"Converted single category_id: {category_ids_list}")
        
        return super().to_internal_value(mutable_data)

    @transaction.atomic
    def create(self, validated_data):
        # Extract user-related fields
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password', None)
        category_ids = validated_data.pop('category_ids', [])
        
        # Remove 'admin' if present in validated_data (to avoid duplication)
        validated_data.pop('admin', None)
        
        # Get admin from context (passed via view)
        admin = self.context['request'].user
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        # Create user
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_trainer=True
        )
        
        # Set password or generate temporary one
        if password:
            user.set_password(password)
            user.save()
        else:
            temp_password = pwo.generate()
            user.set_password(temp_password)
            user.save()
            self.send_welcome_email(email, first_name, last_name, temp_password)
        
        # Create trainer profile (validated_data now only contains TrainerProfile fields)
        trainer = TrainerProfile.objects.create(
            user=user,
            admin=admin,
            **validated_data
        )
        
        # Add categories
        if category_ids:
            trainer.categories.set(category_ids)
        
        return trainer


    def send_welcome_email(self, email, first_name, last_name, password):
        """Send welcome email with temporary password."""
        try:
            subject = "Welcome as a Trainer - Fitness Platform"
            message = (
                f"Dear {first_name} {last_name},\n\n"
                f"Your trainer account has been created successfully. Below are your login details:\n"
                f"Email: {email}\n"
                f"Temporary Password: {password}\n\n"
                f"Please log in and change your password at your earliest convenience.\n\n"
                f"Best regards,\n"
                f"Fitness Platform Team"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print(f"Welcome email sent to {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")


# Optional: Trainer List Serializer (for viewing trainers)
class TrainerListSerializer(serializers.ModelSerializer):
    """Serializer for listing trainers with user details."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    category_names = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = TrainerProfile
        fields = ['id', 'user_email', 'user_full_name', 'admin_email', 'specialization', 
                  'bio', 'avatar_url', 'phone', 'is_active', 'category_names', 
                  'created_at', 'updated_at']

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_category_names(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


# Optional: Trainer Detail Serializer (for viewing single trainer)
class TrainerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single trainer."""
    user = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = TrainerProfile
        fields = ['id', 'user', 'admin', 'specialization', 'bio', 'avatar_url', 
                  'phone', 'is_active', 'categories', 'created_at', 'updated_at']

    def get_user(self, obj):
        return {
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
        }

    def get_admin(self, obj):
        return {
            'email': obj.admin.email,
            'first_name': obj.admin.first_name,
            'last_name': obj.admin.last_name
        }

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    


# Client Serializers
class ClientCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    password = serializers.CharField(write_only=True, required=False)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True), 
        many=True, 
        write_only=True,
        required=False
    )

    class Meta:
        model = ClientProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'date_of_birth', 
                  'phone', 'address', 'is_active', 'category_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        """Handle FormData conversion for category_ids: convert '1,2,3' to [1,2,3]."""
        print("Raw client signup data:", data)
        
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        
        if 'category_ids' in mutable_data:
            category_ids_value = mutable_data.get('category_ids')
            
            if isinstance(category_ids_value, str):
                if ',' in category_ids_value:
                    category_ids_list = [int(id.strip()) for id in category_ids_value.split(',') if id.strip()]
                    mutable_data.setlist('category_ids', category_ids_list)
                elif category_ids_value:
                    category_ids_list = [int(category_ids_value)]
                    mutable_data.setlist('category_ids', category_ids_list)
        
        return super().to_internal_value(mutable_data)

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name', '')
        password = validated_data.pop('password', None)
        category_ids = validated_data.pop('category_ids', [])
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        # Create user
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_client=True
        )
        
        # Set password or generate temporary one
        if password:
            user.set_password(password)
        else:
            temp_password = pwo.generate()
            user.set_password(temp_password)
            self.send_welcome_email(email, first_name, last_name, temp_password)
        
        user.save()
        
        # Create client profile
        client = ClientProfile.objects.create(
            user=user,
            **validated_data
        )
        
        # Add categories
        if category_ids:
            client.categories.set(category_ids)
        
        return client
    
    def send_welcome_email(self, email, first_name, last_name, password):
        try:
            subject = "Welcome to Fitness Platform"
            message = (
                f"Dear {first_name} {last_name},\n\n"
                f"Your account has been created successfully. Below are your login details:\n"
                f"Email: {email}\n"
                f"Temporary Password: {password}\n\n"
                f"Please log in and change your password at your earliest convenience.\n\n"
                f"Best regards,\n"
                f"Fitness Platform Team"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

            
class ClientDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    active_trainers = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'date_of_birth', 
                  'phone', 'address', 'is_active', 'categories', 'active_trainers', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_active_trainers(self, obj):
        active_links = obj.trainer_links.filter(is_active=True)
        return [
            {
                'id': link.trainer.id,
                'name': f"{link.trainer.user.first_name} {link.trainer.user.last_name}".strip() or link.trainer.user.email,
                'specialization': link.trainer.specialization
            }
            for link in active_links
        ]


class ClientListSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source='id')
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')
    categories = serializers.SerializerMethodField()
    trainer_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ['client_id', 'name', 'email', 'phone', 'is_active', 'categories', 
                  'trainer_count', 'created_at']

    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_categories(self, obj):
        return [{'id': cat.id, 'name': cat.name} for cat in obj.categories.all()]
    
    def get_trainer_count(self, obj):
        return obj.trainer_links.filter(is_active=True).count()


# Trainer-Client Link Serializer
class TrainerClientLinkSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    trainer_email = serializers.EmailField(source='trainer.user.email', read_only=True)
    client_name = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainerClientLink
        fields = ['id', 'client', 'trainer', 'client_email', 'client_name', 
                  'trainer_email', 'trainer_name', 'is_active', 'is_subscribed', 
                  'assigned_at', 'updated_at']
        read_only_fields = ['assigned_at', 'updated_at']

    def get_client_name(self, obj):
        return f"{obj.client.user.first_name} {obj.client.user.last_name}".strip() or obj.client.user.email

    def get_trainer_name(self, obj):
        return f"{obj.trainer.user.first_name} {obj.trainer.user.last_name}".strip() or obj.trainer.user.email


# Admin Serializers
class AdminCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_admin=True
        )
        
        temp_password = pwo.generate()
        user.set_password(temp_password)
        user.save()
        
        # Send email with password
        try:
            subject = "Welcome as Admin - Fitness Platform"
            message = (
                f"Dear {first_name} {last_name},\n\n"
                f"Your admin account has been created successfully. Below are your login details:\n"
                f"Email: {email}\n"
                f"Temporary Password: {temp_password}\n\n"
                f"Please log in and change your password at your earliest convenience.\n\n"
                f"Best regards,\n"
                f"Fitness Platform Team"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
        
        return user


class AdminDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'is_admin', 'date_joined', 'last_login', 'is_active']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class AdminListSerializer(serializers.ModelSerializer):
    admin_id = serializers.IntegerField(source='id')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['admin_id', 'email', 'full_name', 'date_joined', 'last_login', 'is_active']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


# Role Serializer
class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='codename',
        queryset=Permission.objects.all()
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions', 'is_staff', 'is_client', 'created_at', 'last_updated']
        read_only_fields = ['created_at', 'last_updated']

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        
        group, created = Group.objects.get_or_create(name=role.name)
        group.permissions.set(permissions)
        group.save()
        
        role.permissions.set(permissions)
        return role
    
    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)
        instance.name = validated_data.get('name', instance.name)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.is_client = validated_data.get('is_client', instance.is_client)
        instance.save()
        
        if permissions is not None:
            instance.permissions.set(permissions)
            group, created = Group.objects.get_or_create(name=instance.name)
            group.permissions.set(permissions)
            group.save()
        
        return instance
    



# Add this after the CategorySerializer and before AdminCreateSerializer

# Base Trainer Serializer (for ViewSet)
class TrainerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', 
        queryset=Category.objects.filter(is_active=True), 
        many=True, 
        write_only=True,
        required=False
    )
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    client_count = serializers.SerializerMethodField()

    class Meta:
        model = TrainerProfile
        fields = ['id', 'user', 'full_name', 'admin', 'admin_email', 'categories', 'category_ids',
                  'specialization', 'bio', 'avatar', 'phone', 'is_active', 'client_count',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_client_count(self, obj):
        return obj.client_links.filter(is_active=True).count()

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        trainer = TrainerProfile.objects.create(**validated_data)
        if categories:
            trainer.categories.set(categories)
        return trainer

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance


# Base Client Serializer (for ViewSet)
class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', 
        queryset=Category.objects.filter(is_active=True), 
        many=True, 
        write_only=True,
        required=False
    )
    full_name = serializers.SerializerMethodField()
    active_trainers = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'full_name', 'categories', 'category_ids', 'date_of_birth', 
                  'phone', 'address', 'is_active', 'active_trainers', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_active_trainers(self, obj):
        active_links = obj.trainer_links.filter(is_active=True)
        return [
            {
                'id': link.trainer.id,
                'name': f"{link.trainer.user.first_name} {link.trainer.user.last_name}".strip() or link.trainer.user.email,
                'specialization': link.trainer.specialization
            }
            for link in active_links
        ]

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        client = ClientProfile.objects.create(**validated_data)
        if categories:
            client.categories.set(categories)
        return client

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance