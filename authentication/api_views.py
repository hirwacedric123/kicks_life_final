from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Purchase, User, Post
import json
from django.db.models import Sum, Count, Avg
from decimal import Decimal

# Simplified API views for direct store operations (admin-only)

@login_required
@require_POST
def verify_buyer_credentials(request):
    """Verify buyer credentials for order confirmation (Admin only)"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Access denied. Admin role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return JsonResponse({'error': 'Username and email are required'}, status=400)
        
        try:
            user = User.objects.get(username=username, email=email)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found with provided credentials'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
@require_POST
def update_order_status_api(request):
    """Update order status (Admin only)"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Access denied. Admin role required.'}, status=403)
    
    try:
        data = json.loads(request.body)
        purchase_id = data.get('purchase_id')
        new_status = data.get('status')
        tracking_number = data.get('tracking_number', '')
        
        if not purchase_id or not new_status:
            return JsonResponse({'error': 'Purchase ID and status are required'}, status=400)
        
        if new_status not in ['processing', 'shipped', 'delivered', 'completed', 'cancelled']:
            return JsonResponse({'error': 'Invalid status value'}, status=400)
        
        purchase = Purchase.objects.get(id=purchase_id)
        purchase.status = new_status
        if tracking_number:
            purchase.tracking_number = tracking_number
        purchase.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Order {purchase.order_id} status updated to {new_status}',
            'order': {
                'id': purchase.id,
                'order_id': purchase.order_id,
                'status': purchase.status,
                'tracking_number': purchase.tracking_number
            }
        })
    except Purchase.DoesNotExist:
        return JsonResponse({'error': 'Purchase not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
def get_admin_statistics(request):
    """Get admin dashboard statistics (Admin only)"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Access denied. Admin role required.'}, status=403)
    
    try:
        products = Post.objects.all()
        purchases = Purchase.objects.all()
        
        total_orders = purchases.count()
        pending_orders = purchases.filter(status='pending').count()
        completed_orders = purchases.filter(status='completed').count()
        
        total_revenue = purchases.filter(status='completed').aggregate(
            total=Sum('purchase_price')
        )['total'] or 0
        
        # Monthly statistics
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_revenue = purchases.filter(
            status='completed',
            created_at__month=current_month,
            created_at__year=current_year
        ).aggregate(total=Sum('purchase_price'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'total_revenue': float(total_revenue),
                'monthly_revenue': float(monthly_revenue),
                'total_products': products.count(),
                'low_stock_products': products.filter(inventory__lte=5).count()
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@login_required
def get_order_details(request, order_id):
    """Get detailed order information (Admin only)"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Access denied. Admin role required.'}, status=403)
    
    try:
        purchase = Purchase.objects.select_related('buyer', 'product').get(order_id=order_id)
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': purchase.id,
                'order_id': purchase.order_id,
                'buyer': {
                    'username': purchase.buyer.username,
                    'email': purchase.buyer.email,
                    'phone': purchase.buyer.phone_number
                },
                'product': {
                    'title': purchase.product.title,
                    'price': float(purchase.product.price)
                },
                'quantity': purchase.quantity,
                'purchase_price': float(purchase.purchase_price),
                'status': purchase.status,
                'delivery_method': purchase.delivery_method,
                'payment_method': purchase.payment_method,
                'delivery_fee': float(purchase.delivery_fee),
                'delivery_address': purchase.delivery_address,
                'notes': purchase.notes,
                'tracking_number': purchase.tracking_number,
                'created_at': purchase.created_at.isoformat(),
                'updated_at': purchase.updated_at.isoformat()
            }
        })
        
    except Purchase.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)
