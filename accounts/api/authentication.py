import random
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.utils import timezone

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    @classmethod
    def send_otp(cls, email):
        # Delete old OTPs for this email
        cls.objects.filter(email=email).delete()
        otp_obj = cls.objects.create(email=email)
        send_mail(
            subject="Your Login OTP",
            message=f"Your OTP is {otp_obj.otp}. It is valid for 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return otp_obj

    @classmethod
    def verify_otp(cls, email, otp_code):
        try:
            otp_obj = cls.objects.get(email=email, otp=otp_code, is_verified=False)
            # Optional: check creation time (10 min expiry)
            if (timezone.now() - otp_obj.created_at).seconds > 600:
                otp_obj.delete()
                return False
            otp_obj.is_verified = True
            otp_obj.save()
            return True
        except cls.DoesNotExist:
            return False