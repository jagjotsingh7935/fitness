from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from password_generator import PasswordGenerator
from accounts.models import User, Category, TrainerProfile, ClientProfile, TrainerClientLink, Role, EmailOTP, BMI, FatPercent

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
    category_ids = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = TrainerProfile
        fields = [
            'id',
            'user_email',
            'user_full_name',
            'admin_email',
            'specialization',
            'bio',
            'avatar_url',
            'phone',
            'is_active',
            'category_names',
            'category_ids',
            'created_at',
            'updated_at'
        ]

    def get_user_full_name(self, obj):
        print("\n========== GET USER FULL NAME ==========")
        print(f"Trainer ID: {obj.id}")
        print(f"First Name: {obj.user.first_name}")
        print(f"Last Name: {obj.user.last_name}")
        print(f"Email: {obj.user.email}")

        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()

        print(f"Generated Full Name: {full_name}")

        return full_name or obj.user.email

    def get_category_names(self, obj):
        print("\n========== GET CATEGORY NAMES ==========")
        print(f"Trainer ID: {obj.id}")

        categories = obj.categories.all()

        print(f"Total Categories: {categories.count()}")

        category_names = [cat.name for cat in categories]

        print(f"Category Names: {category_names}")

        return category_names

    def get_category_ids(self, obj):
        print("\n========== GET CATEGORY IDS ==========")
        print(f"Trainer ID: {obj.id}")

        category_ids = list(
            obj.categories.all().values_list('id', flat=True)
        )

        print(f"Category IDs: {category_ids}")

        return category_ids

    def get_avatar_url(self, obj):
        print("\n========== GET AVATAR URL ==========")
        print(f"Trainer ID: {obj.id}")

        if obj.avatar:
            print(f"Avatar Exists: {obj.avatar.url}")

            request = self.context.get('request')

            if request:
                full_url = request.build_absolute_uri(obj.avatar.url)

                print(f"Full Avatar URL: {full_url}")

                return full_url

            print(f"Relative Avatar URL: {obj.avatar.url}")

            return obj.avatar.url

        print("No avatar found")

        return None

    def to_representation(self, instance):
        print("\n========== SERIALIZING TRAINER ==========")
        print(f"Trainer ID: {instance.id}")
        print(f"User Email: {instance.user.email}")
        print(f"Specialization: {instance.specialization}")
        print(f"Is Active: {instance.is_active}")

        representation = super().to_representation(instance)

        print(f"Serialized Data: {representation}")

        return representation
# Optional: Trainer Detail Serializer (for viewing single trainer)
class TrainerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single trainer with full CRUD support."""
    
    user = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    # Write-only fields for updates
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Array of category IDs to assign to the trainer"
    )
    email = serializers.EmailField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = TrainerProfile
        fields = [
            'id', 'user', 'admin', 'specialization', 'bio', 'avatar_url',
            'phone', 'is_active', 'categories', 'category_ids', 'email',
            'first_name', 'last_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_user(self, obj):
        print("\n========== GET USER ==========")
        print(f"User ID: {obj.user.id}")
        print(f"Email: {obj.user.email}")
        print(f"Name: {obj.user.first_name} {obj.user.last_name}")

        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
        }

    def get_admin(self, obj):
        print("\n========== GET ADMIN ==========")
        print(f"Admin ID: {obj.admin.id}")
        print(f"Admin Email: {obj.admin.email}")

        return {
            'id': obj.admin.id,
            'email': obj.admin.email,
            'first_name': obj.admin.first_name,
            'last_name': obj.admin.last_name
        }

    def get_avatar_url(self, obj):
        print("\n========== GET AVATAR URL ==========")

        if obj.avatar:
            print(f"Avatar exists: {obj.avatar.url}")

            request = self.context.get('request')
            if request:
                full_url = request.build_absolute_uri(obj.avatar.url)
                print(f"Full Avatar URL: {full_url}")
                return full_url

            print(f"Relative Avatar URL: {obj.avatar.url}")
            return obj.avatar.url

        print("No avatar found")
        return None

    def update(self, instance, validated_data):
        """Handle PATCH/PUT updates including user fields and categories."""

        print("\n\n========== UPDATE TRAINER START ==========")
        print(f"Trainer ID: {instance.id}")
        print(f"Validated Data: {validated_data}")

        # Extract category IDs array
        category_ids = validated_data.pop('category_ids', None)
        print(f"Category IDs: {category_ids}")

        # Extract user-related fields
        email = validated_data.pop('email', None)
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)

        print(f"Email: {email}")
        print(f"First Name: {first_name}")
        print(f"Last Name: {last_name}")

        # Update TrainerProfile fields
        print("\n----- Updating TrainerProfile Fields -----")

        for attr, value in validated_data.items():
            print(f"Updating {attr} => {value}")

            if value is not None:
                setattr(instance, attr, value)

        instance.save()
        print("TrainerProfile saved successfully")

        # Update User fields
        user_updated = False

        print("\n----- Updating User Fields -----")

        if email is not None and email != instance.user.email:
            print(f"Checking if email exists: {email}")

            # Check if email is already taken
            if User.objects.filter(email=email).exclude(id=instance.user.id).exists():
                print("ERROR: Email already exists")
                raise serializers.ValidationError({
                    'email': 'Email already exists'
                })

            print(f"Updating email from {instance.user.email} to {email}")

            instance.user.email = email
            instance.user.username = email
            user_updated = True

        if first_name is not None:
            print(f"Updating first_name => {first_name}")

            instance.user.first_name = first_name
            user_updated = True

        if last_name is not None:
            print(f"Updating last_name => {last_name}")

            instance.user.last_name = last_name
            user_updated = True

        if user_updated:
            instance.user.save()
            print("User updated successfully")
        else:
            print("No user fields updated")

        # Update categories using the array of IDs
        print("\n----- Updating Categories -----")

        if category_ids is not None:
            print(f"Fetching categories for IDs: {category_ids}")

            categories = Category.objects.filter(
                id__in=category_ids,
                is_active=True
            )

            print(f"Found categories count: {categories.count()}")

            # Check if all provided IDs exist
            if len(categories) != len(category_ids):
                found_ids = set(categories.values_list('id', flat=True))
                missing_ids = set(category_ids) - found_ids

                print(f"ERROR: Missing category IDs: {missing_ids}")

                raise serializers.ValidationError({
                    'category_ids': f'Invalid category IDs: {list(missing_ids)}'
                })

            print("Setting categories...")

            instance.categories.set(categories)

            print("Categories updated successfully")
            print(f"Assigned Categories: {[cat.name for cat in categories]}")
        else:
            print("No category updates provided")

        print("========== UPDATE TRAINER END ==========\n\n")

        return instance

    def to_representation(self, instance):
        """Customize the output representation."""

        print("\n========== TO REPRESENTATION ==========")
        print(f"Serializing Trainer ID: {instance.id}")

        representation = super().to_representation(instance)

        # Add convenience fields for frontend
        representation['user_email'] = instance.user.email
        representation['user_full_name'] = (
            f"{instance.user.first_name} {instance.user.last_name}".strip()
        )
        representation['category_names'] = [
            cat.name for cat in instance.categories.all()
        ]
        representation['category_ids'] = [
            cat.id for cat in instance.categories.all()
        ]

        print(f"Representation Generated: {representation}")

        return representation

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

    # Optional body metrics & preferences
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    age = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    weight = serializers.JSONField(required=False, allow_null=True)
    height = serializers.JSONField(required=False, allow_null=True)
    neck_circumference = serializers.JSONField(required=False, allow_null=True)
    waist = serializers.JSONField(required=False, allow_null=True)
    bmi = serializers.JSONField(required=False, allow_null=True)
    fat_percent = serializers.JSONField(required=False, allow_null=True)
    preferred_bmi = serializers.JSONField(required=False, allow_null=True)
    preferred_weight = serializers.JSONField(required=False, allow_null=True)
    preferred_waist = serializers.JSONField(required=False, allow_null=True)
    preferred_fat_percent = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name', 'password',
            'date_of_birth', 'phone', 'address', 'is_active',
            'category_ids',
            'gender', 'age', 'weight', 'height',
            'neck_circumference', 'waist',
            'bmi', 'fat_percent',
            'preferred_bmi', 'preferred_weight', 'preferred_waist', 'preferred_fat_percent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists. Please login instead.")
        return value

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
        
        # Handle BMI and FatPercent foreign objects if passed
        bmi_data = validated_data.pop('bmi', None)
        fat_percent_data = validated_data.pop('fat_percent', None)
        
        bmi_obj = None
        if bmi_data is not None and str(bmi_data).strip() != '':
            bmi_obj = BMI.objects.create(bmi=bmi_data)
            
        fat_obj = None
        if fat_percent_data is not None and str(fat_percent_data).strip() != '':
            fat_obj = FatPercent.objects.create(fat_percent=fat_percent_data)

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
            bmi=bmi_obj,
            fat_percent=fat_obj,
            **validated_data
        )
        
        # Add categories
        if category_ids:
            client.categories.set(category_ids)
        
        return client

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['email'] = instance.user.email
        ret['first_name'] = instance.user.first_name
        ret['last_name'] = instance.user.last_name
        ret['bmi'] = instance.bmi.bmi if instance.bmi else None
        ret['fat_percent'] = instance.fat_percent.fat_percent if instance.fat_percent else None
        return ret
    
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
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    active_trainers = serializers.SerializerMethodField()

    # Body metrics & preferences
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    age = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    weight = serializers.JSONField(required=False, allow_null=True)
    height = serializers.JSONField(required=False, allow_null=True)
    neck_circumference = serializers.JSONField(required=False, allow_null=True)
    waist = serializers.JSONField(required=False, allow_null=True)
    bmi = serializers.JSONField(required=False, allow_null=True)
    fat_percent = serializers.JSONField(required=False, allow_null=True)
    preferred_bmi = serializers.JSONField(required=False, allow_null=True)
    preferred_weight = serializers.JSONField(required=False, allow_null=True)
    preferred_waist = serializers.JSONField(required=False, allow_null=True)
    preferred_fat_percent = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'phone', 'address', 'is_active',
            'categories', 'category_ids', 'active_trainers',
            'gender', 'age', 'weight', 'height',
            'neck_circumference', 'waist',
            'bmi', 'fat_percent',
            'preferred_bmi', 'preferred_weight', 'preferred_waist', 'preferred_fat_percent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['first_name'] = instance.user.first_name
        ret['last_name'] = instance.user.last_name
        ret['bmi'] = instance.bmi.bmi if instance.bmi else None
        ret['fat_percent'] = instance.fat_percent.fat_percent if instance.fat_percent else None
        return ret

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

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update user fields
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        user_updated = False
        if first_name is not None:
            instance.user.first_name = first_name
            user_updated = True
        if last_name is not None:
            instance.user.last_name = last_name
            user_updated = True
        if user_updated:
            instance.user.save()

        # Update categories if passed
        if 'category_ids' in validated_data:
            categories = validated_data.pop('category_ids')
            instance.categories.set(categories)

        # Update BMI if passed
        if 'bmi' in validated_data:
            bmi_val = validated_data.pop('bmi')
            if bmi_val is not None and str(bmi_val).strip() != '':
                if instance.bmi:
                    instance.bmi.bmi = bmi_val
                    instance.bmi.save()
                else:
                    instance.bmi = BMI.objects.create(bmi=bmi_val)

        # Update FatPercent if passed
        if 'fat_percent' in validated_data:
            fat_val = validated_data.pop('fat_percent')
            if fat_val is not None and str(fat_val).strip() != '':
                if instance.fat_percent:
                    instance.fat_percent.fat_percent = fat_val
                    instance.fat_percent.save()
                else:
                    instance.fat_percent = FatPercent.objects.create(fat_percent=fat_val)

        # Update remaining ClientProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class ClientListSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source='id')
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')
    categories = serializers.SerializerMethodField()
    trainer_count = serializers.SerializerMethodField()
    active_trainers = serializers.SerializerMethodField()
    
    # Body metrics & preferences
    gender = serializers.CharField(allow_blank=True, allow_null=True)
    age = serializers.CharField(allow_blank=True, allow_null=True)
    weight = serializers.JSONField(allow_null=True)
    height = serializers.JSONField(allow_null=True)
    neck_circumference = serializers.JSONField(allow_null=True)
    waist = serializers.JSONField(allow_null=True)
    bmi = serializers.SerializerMethodField()
    fat_percent = serializers.SerializerMethodField()
    preferred_bmi = serializers.JSONField(allow_null=True)
    preferred_weight = serializers.JSONField(allow_null=True)
    preferred_waist = serializers.JSONField(allow_null=True)
    preferred_fat_percent = serializers.JSONField(allow_null=True)

    class Meta:
        model = ClientProfile
        fields = [
            'client_id', 'name', 'email', 'phone', 'is_active', 
            'categories', 'trainer_count', 'active_trainers', 'created_at',
            'gender', 'age', 'weight', 'height', 
            'neck_circumference', 'waist',
            'bmi', 'fat_percent',
            'preferred_bmi', 'preferred_weight', 'preferred_waist', 'preferred_fat_percent'
        ]
        read_only_fields = ['created_at']

    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_bmi(self, obj):
        return obj.bmi.bmi if obj.bmi else None

    def get_fat_percent(self, obj):
        return obj.fat_percent.fat_percent if obj.fat_percent else None
    
    def get_categories(self, obj):
        return [{'id': cat.id, 'name': cat.name} for cat in obj.categories.all()]
    
    def get_trainer_count(self, obj):
        return obj.trainer_links.filter(is_active=True).count()

    def get_active_trainers(self, obj):
        active_links = obj.trainer_links.filter(is_active=True).select_related('trainer', 'trainer__user')
        return [
            {
                'id': link.trainer.id,
                'name': f"{link.trainer.user.first_name} {link.trainer.user.last_name}".strip() or link.trainer.user.email,
                'specialization': link.trainer.specialization
            }
            for link in active_links
        ]

    

# Trainer-Client Link Serializer
class TrainerClientLinkSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source='client.id', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    trainer_email = serializers.EmailField(source='trainer.user.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    gender = serializers.CharField(source='client.gender', read_only=True)
    client_name = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = TrainerClientLink
        fields = [
            'id',
            'client',
            'client_id',
            'trainer',
            'client_email',
            'client_name',
            'client_phone',
            'gender',
            'categories',
            'target',
            'trainer_email',
            'trainer_name',
            'is_active',
            'is_subscribed',
            'assigned_at',
            'updated_at'
        ]
        read_only_fields = ['assigned_at', 'updated_at']

    def get_client_name(self, obj):
        client_name = (
            f"{obj.client.user.first_name} {obj.client.user.last_name}".strip()
            or obj.client.user.email
        )
        return client_name

    def get_trainer_name(self, obj):
        trainer_name = (
            f"{obj.trainer.user.first_name} {obj.trainer.user.last_name}".strip()
            or obj.trainer.user.email
        )
        return trainer_name

    def get_categories(self, obj):
        return [c.name for c in obj.client.categories.all()]

    def get_target(self, obj):
        cats = [c.name for c in obj.client.categories.all()]
        return cats[0] if cats else 'Strength & Fitness'



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



class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username']




class TrainerProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', many=True, read_only=True
    )

    class Meta:
        model = TrainerProfile
        fields = [
            'id', 'user', 'categories', 'category_ids',
            'specialization', 'bio', 'avatar', 'phone',
            'is_active', 'created_at'
        ]

class ClientProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', many=True, read_only=True
    )

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'user', 'categories', 'category_ids',
            'date_of_birth', 'phone', 'address',
            'is_active', 'created_at'
        ]

