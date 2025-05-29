import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(user, otp_code, purpose='purchase_confirmation'):
    """Send OTP via email"""
    subject = 'KoraQuest - Verification Code'
    
    if purpose == 'purchase_confirmation':
        message = f"""
        Dear {user.username},
        
        Your verification code for purchase confirmation is: {otp_code}
        
        This code will expire in 5 minutes.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        KoraQuest Team
        """
    else:
        message = f"""
        Dear {user.username},
        
        Your verification code is: {otp_code}
        
        This code will expire in 5 minutes.
        
        Best regards,
        KoraQuest Team
        """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False

def create_otp(user, purpose='purchase_confirmation'):
    """Create and send OTP to user"""
    # Invalidate any existing unused OTPs for this user and purpose
    OTPVerification.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).update(is_used=True)
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Create OTP record
    otp = OTPVerification.objects.create(
        user=user,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    
    # Send OTP via email
    email_sent = send_otp_email(user, otp_code, purpose)
    
    return {
        'otp_id': otp.id,
        'email_sent': email_sent,
        'expires_at': otp.expires_at
    }

def verify_otp(user, otp_code, purpose='purchase_confirmation'):
    """Verify OTP code"""
    try:
        otp = OTPVerification.objects.get(
            user=user,
            otp_code=otp_code,
            purpose=purpose,
            is_used=False
        )
        
        if otp.is_expired():
            return {'valid': False, 'error': 'OTP has expired'}
        
        # Mark OTP as used
        otp.is_used = True
        otp.save()
        
        return {'valid': True, 'otp_id': otp.id}
    
    except OTPVerification.DoesNotExist:
        return {'valid': False, 'error': 'Invalid OTP code'}

def cleanup_expired_otps():
    """Clean up expired OTPs (can be run as a cron job)"""
    expired_otps = OTPVerification.objects.filter(
        expires_at__lt=timezone.now()
    )
    count = expired_otps.count()
    expired_otps.delete()
    return count
