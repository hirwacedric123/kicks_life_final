from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Purchase, User
from .qr_utils import decode_qr_data, get_user_purchases_from_qr
from .otp_utils import create_otp, verify_otp as verify_otp_util
import json

@login_required
@require_POST
def get_purchases_by_qr(request):
    """API endpoint to get purchases from a QR code"""
    if not request.user.is_koraquest():
        return JsonResponse({'error': 'Access denied. KoraQuest role required.', 'purchases': []}, status=403)
    
    try:
        data = json.loads(request.body)
        qr_data = data.get('qr_data')
        
        if not qr_data:
            return JsonResponse({'error': 'No QR data provided', 'purchases': []}, status=400)
        
        # Decode QR data
        decoded_data = decode_qr_data(qr_data.strip())
        
        if isinstance(decoded_data, dict) and 'error' in decoded_data:
            return JsonResponse({'error': decoded_data['error'], 'purchases': []}, status=400)
        
        # Get purchase information
        purchase_info = get_user_purchases_from_qr(decoded_data)
        
        # If no purchases found or empty QR data
        if not purchase_info.get('purchases'):
            # Still return user info if possible
            user_info = {}
            try:
                user = User.objects.get(id=purchase_info.get('user_id'))
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email
                }
            except Exception:
                pass
            return JsonResponse({
                'error': 'No pending purchases found in this QR code.',
                'purchases': [],
                'buyer': user_info
            }, status=404)
        
        # Add buyer information
        try:
            user = User.objects.get(id=purchase_info['user_id'])
            purchase_info['buyer'] = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found', 'purchases': []}, status=404)
        
        # Always include purchases key
        if 'purchases' not in purchase_info:
            purchase_info['purchases'] = []
        
        return JsonResponse(purchase_info)
    except Exception as e:
        import traceback
        print('Error in get_purchases_by_qr:', traceback.format_exc())
        return JsonResponse({'error': f'Error processing request: {str(e)}', 'purchases': []}, status=500)

@login_required
@require_POST
def verify_buyer_credentials(request):
    """API endpoint to verify buyer credentials"""
    if not request.user.is_koraquest():
        return JsonResponse({'error': 'Access denied. KoraQuest role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user_id = data.get('user_id')  # This should match the user from the QR code
        
        if not all([username, password, user_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Verify credentials
        user = authenticate(username=username, password=password)
        
        if not user:
            return JsonResponse({'error': 'Invalid username or password'}, status=401)
        
        # Ensure the authenticated user matches the user from the QR code
        if user.id != int(user_id):
            return JsonResponse({'error': 'Authentication failed. User mismatch.'}, status=401)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
@require_POST
def send_otp(request):
    """API endpoint to send OTP for purchase verification"""
    if not request.user.is_koraquest():
        return JsonResponse({'error': 'Access denied. KoraQuest role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        purchase_id = data.get('purchase_id')
        
        if not user_id:
            return JsonResponse({'error': 'Missing user_id'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Create and send OTP
        otp_result = create_otp(user, 'purchase_confirmation')
        
        if not otp_result.get('email_sent'):
            return JsonResponse({'error': 'Failed to send OTP email'}, status=500)
        
        return JsonResponse({
            'success': True,
            'message': f'OTP sent to {user.email}',
            'session_id': otp_result.get('otp_id')
        })
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
@require_POST
def verify_otp_view(request):
    """API endpoint to verify OTP for purchase confirmation"""
    if not request.user.is_koraquest():
        return JsonResponse({'error': 'Access denied. KoraQuest role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        otp_code = data.get('otp_code')
        purchase_id = data.get('purchase_id')
        
        if not all([user_id, otp_code]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Verify OTP using the utility function
        otp_result = verify_otp_util(user, otp_code, 'purchase_confirmation')
        
        if not otp_result.get('valid'):
            return JsonResponse({'error': otp_result.get('error', 'Invalid OTP')}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'OTP verified successfully'
        })
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
@require_POST
def complete_purchase_pickup(request):
    """API endpoint to complete purchase pickup after OTP verification"""
    if not request.user.is_koraquest():
        return JsonResponse({'error': 'Access denied. KoraQuest role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        purchase_id = data.get('purchase_id')
        
        if not purchase_id:
            return JsonResponse({'error': 'Missing purchase_id'}, status=400)
        
        try:
            purchase = Purchase.objects.get(id=purchase_id)
        except Purchase.DoesNotExist:
            return JsonResponse({'error': 'Purchase not found'}, status=404)
        
        # Check if purchase is awaiting pickup
        if purchase.status != 'awaiting_pickup':
            return JsonResponse({'error': 'Invalid purchase status'}, status=400)
        
        # Complete the purchase
        purchase.status = 'completed'
        purchase.koraquest_user = request.user
        purchase.pickup_confirmed_at = timezone.now()
        purchase.save()
        
        # Update vendor and buyer stats
        vendor = purchase.product.user
        vendor.total_sales += purchase.vendor_payment_amount
        vendor.save()
        
        buyer = purchase.buyer
        buyer.total_purchases += (purchase.purchase_price * purchase.quantity)
        buyer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Purchase confirmed successfully!',
            'vendor_payment': str(purchase.vendor_payment_amount),
            'koraquest_commission': str(purchase.koraquest_commission_amount)
        })
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)
