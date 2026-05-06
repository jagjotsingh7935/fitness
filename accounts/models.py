from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_trainer = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email or self.username


class Category(models.Model):
    """Categories like weight loss, weight gain, flexibility, etc."""
    name = models.CharField(max_length=100, unique=True)
    icon = models.FileField(upload_to='category_icons/', null=True, blank=True, 
                           help_text="Upload SVG or PNG icon for the category")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        permissions = [
            ("can_view_category", "Can view category"),
            ("create_category", "Can create category"),
            ("update_category", "Can update category"),
            ("can_delete_category", "Can delete category"),
        ]

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_staff = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        permissions = [
            ("can_view_role", "Can view role"),
            ("create_role", "Can create role"),
            ("update_role", "Can update role"),
            ("can_delete_role", "Can delete role"),
        ]


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_admin': True}, related_name='trainers')
    categories = models.ManyToManyField(Category, related_name='trainers', blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='trainer_avatars/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trainer Profile"
        verbose_name_plural = "Trainer Profiles"
        permissions = [
            ("can_view_trainer", "Can view trainer"),
            ("create_trainer", "Can create trainer"),
            ("update_trainer", "Can update trainer"),
            ("can_delete_trainer", "Can delete trainer"),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} (Trainer for {self.admin.email})"


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    categories = models.ManyToManyField(Category, related_name='clients', blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Profile"
        verbose_name_plural = "Client Profiles"
        permissions = [
            ("can_view_client", "Can view client"),
            ("create_client", "Can create client"),
            ("update_client", "Can update client"),
            ("can_delete_client", "Can delete client"),
        ]

    def __str__(self):
        return self.user.email


class TrainerClientLink(models.Model):
    """Intermediate model to manage many-to-many between trainers and clients with active status."""
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='trainer_links')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='client_links')
    is_active = models.BooleanField(default=True)          # subscription currently active?
    is_subscribed = models.BooleanField(default=False)     # for future payment tracking
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'trainer')   # one link per pair
        verbose_name = "Trainer-Client Link"
        verbose_name_plural = "Trainer-Client Links"
        permissions = [
            ("can_activate_link", "Can activate/deactivate trainer-client link"),
        ]

    def __str__(self):
        return f"{self.client.user.email} → {self.trainer.user.email} (active={self.is_active})"


class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"

    def save(self, *args, **kwargs):
        import random
        if not self.otp:
            self.otp = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    @classmethod
    def send_otp(cls, email):
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Delete old OTPs for this email
        cls.objects.filter(email=email).delete()
        otp_obj = cls.objects.create(email=email)
        try:
            send_mail(
                subject="Your Login OTP",
                message=f"Your OTP is {otp_obj.otp}. It is valid for 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
        return otp_obj

    @classmethod
    def verify_otp(cls, email, otp_code):
        from django.utils import timezone
        
        try:
            otp_obj = cls.objects.get(email=email, otp=otp_code, is_verified=False)
            # Check creation time (10 min expiry)
            if (timezone.now() - otp_obj.created_at).seconds > 600:
                otp_obj.delete()
                return False
            otp_obj.is_verified = True
            otp_obj.save()
            return True
        except cls.DoesNotExist:
            return False

    def __str__(self):
        return f"{self.email} - {self.otp} - Verified: {self.is_verified}"