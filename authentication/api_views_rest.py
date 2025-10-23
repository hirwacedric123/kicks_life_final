from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    User, Post, Purchase, Bookmark, ProductImage, 
    UserQRCode, OTPVerification, ProductReview
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    PostSerializer, PostCreateSerializer, PurchaseSerializer, PurchaseCreateSerializer,
    BookmarkSerializer, UserQRCodeSerializer, OTPVerificationSerializer,
    VendorStatisticsSerializer, DashboardStatsSerializer, ProductReviewSerializer
)
from .qr_utils import update_user_qr_code, decode_qr_data, get_user_purchases_from_qr
from .otp_utils import create_otp, verify_otp


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Authentication Views
class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Auto-login after registration
        login(request, user)
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout_view(request):
    """User logout endpoint"""
    logout(request)
    return Response({'message': 'Logout successful'})


# User Views
class UserViewSet(ModelViewSet):
    """User CRUD operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_vendor_role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_login', 'username']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return User.objects.all()
        elif self.request.user.is_staff_member():
            return User.objects.filter(Q(role='user') | Q(role='vendor'))
        else:
            return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def become_vendor(self, request, pk=None):
        """Convert user to vendor role"""
        user = self.get_object()
        if user.id != request.user.id and not request.user.is_koraquest():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        user.is_vendor_role = True
        user.save()
        
        return Response({
            'message': 'User successfully converted to vendor',
            'user': UserSerializer(user).data
        })


# Post Views
class PostViewSet(ModelViewSet):
    """Post CRUD operations"""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'user', 'price']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'total_purchases']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return Post.objects.all()
        else:
            return Post.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a post"""
        post = self.get_object()
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return Response({
            'liked': liked,
            'likes_count': post.total_likes()
        })
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark/unbookmark a post"""
        post = self.get_object()
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True
        
        return Response({
            'bookmarked': bookmarked
        })
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase a product"""
        post = self.get_object()
        serializer = PurchaseCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Check inventory
        if post.inventory < serializer.validated_data['quantity']:
            return Response(
                {'error': 'Insufficient inventory'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create purchase
        purchase = serializer.save()
        
        # Update inventory
        post.inventory -= purchase.quantity
        post.save()
        
        return Response({
            'message': 'Purchase created successfully',
            'purchase': PurchaseSerializer(purchase).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a product review"""
        post = self.get_object()
        serializer = ProductReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user has purchased this product
        if not Purchase.objects.filter(
            buyer=request.user, 
            product=post, 
            status='completed'
        ).exists():
            return Response(
                {'error': 'You must purchase this product before reviewing'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already reviewed
        if ProductReview.objects.filter(reviewer=request.user, product=post).exists():
            return Response(
                {'error': 'You have already reviewed this product'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(reviewer=request.user, product=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Purchase Views
class PurchaseViewSet(ModelViewSet):
    """Purchase CRUD operations"""
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'delivery_method', 'payment_method', 'buyer', 'product']
    search_fields = ['order_id', 'product__title']
    ordering_fields = ['created_at', 'purchase_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return Purchase.objects.all()
        elif self.request.user.is_vendor():
            return Purchase.objects.filter(product__user=self.request.user)
        else:
            return Purchase.objects.filter(buyer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update purchase status (KoraQuest only)"""
        if not request.user.is_koraquest():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        purchase = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Purchase.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        purchase.status = new_status
        if new_status == 'completed':
            purchase.koraquest_user = request.user
            purchase.pickup_confirmed_at = timezone.now()
        purchase.save()
        
        return Response({
            'message': 'Status updated successfully',
            'purchase': PurchaseSerializer(purchase).data
        })


# Bookmark Views
class BookmarkViewSet(ModelViewSet):
    """Bookmark CRUD operations"""
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


# Product Review Views
class ProductReviewViewSet(ModelViewSet):
    """Product Review CRUD operations"""
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'reviewer', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return ProductReview.objects.all()
        else:
            return ProductReview.objects.filter(reviewer=self.request.user)


# QR Code Views
class UserQRCodeViewSet(ModelViewSet):
    """User QR Code CRUD operations"""
    queryset = UserQRCode.objects.all()
    serializer_class = UserQRCodeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return UserQRCode.objects.all()
        else:
            return UserQRCode.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate_qr(self, request):
        """Generate QR code for current user"""
        user = request.user
        
        # Delete existing QR code
        UserQRCode.objects.filter(user=user).delete()
        
        # Generate new QR code
        try:
            update_user_qr_code(user)
            qr_code = UserQRCode.objects.get(user=user)
            return Response({
                'message': 'QR code generated successfully',
                'qr_code': UserQRCodeSerializer(qr_code).data
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate QR code: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# OTP Views
class OTPVerificationViewSet(ModelViewSet):
    """OTP Verification CRUD operations"""
    queryset = OTPVerification.objects.all()
    serializer_class = OTPVerificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_koraquest():
            return OTPVerification.objects.all()
        else:
            return OTPVerification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        """Send OTP to user"""
        user_id = request.data.get('user_id')
        purpose = request.data.get('purpose', 'general')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if not (request.user.is_koraquest() or request.user.id == user_id):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            otp_result = create_otp(user, purpose)
            if otp_result.get('email_sent'):
                return Response({
                    'message': f'OTP sent to {user.email}',
                    'session_id': otp_result.get('otp_id')
                })
            else:
                return Response(
                    {'error': 'Failed to send OTP'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to send OTP: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify OTP"""
        user_id = request.data.get('user_id')
        otp_code = request.data.get('otp_code')
        purpose = request.data.get('purpose', 'general')
        
        if not all([user_id, otp_code]):
            return Response(
                {'error': 'user_id and otp_code are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if not (request.user.is_koraquest() or request.user.id == user_id):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            otp_result = verify_otp(user, otp_code, purpose)
            if otp_result.get('valid'):
                return Response({
                    'message': 'OTP verified successfully',
                    'valid': True
                })
            else:
                return Response(
                    {'error': otp_result.get('error', 'Invalid OTP')}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to verify OTP: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Dashboard and Statistics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for current user"""
    user = request.user
    
    # Get user's posts
    user_posts = Post.objects.filter(user=user)
    total_posts = user_posts.count()
    
    # Get user's purchases
    user_purchases = Purchase.objects.filter(buyer=user)
    total_purchases = user_purchases.count()
    
    # Get user's sales (if vendor)
    if user.is_vendor():
        vendor_sales = Purchase.objects.filter(product__user=user, status='completed')
        total_sales = vendor_sales.aggregate(total=Sum('vendor_payment_amount'))['total'] or 0
    else:
        total_sales = 0
    
    # Get user's bookmarks
    total_bookmarks = Bookmark.objects.filter(user=user).count()
    
    # Get recent posts
    recent_posts = user_posts.order_by('-created_at')[:5]
    
    # Get recent purchases
    recent_purchases = user_purchases.order_by('-created_at')[:5]
    
    data = {
        'total_posts': total_posts,
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'total_bookmarks': total_bookmarks,
        'recent_posts': PostSerializer(recent_posts, many=True).data,
        'recent_purchases': PurchaseSerializer(recent_purchases, many=True).data
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_statistics(request, vendor_id):
    """Get vendor statistics (KoraQuest only)"""
    if not request.user.is_koraquest():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor = User.objects.get(id=vendor_id, is_vendor_role=True)
    except User.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get vendor's completed purchases
    purchases = Purchase.objects.filter(
        product__user=vendor,
        status='completed'
    )
    
    total_sales = purchases.count()
    total_revenue = purchases.aggregate(total=Sum('vendor_payment_amount'))['total'] or 0
    
    # Monthly statistics
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_purchases = purchases.filter(
        pickup_confirmed_at__month=current_month,
        pickup_confirmed_at__year=current_year
    )
    monthly_revenue = monthly_purchases.aggregate(total=Sum('vendor_payment_amount'))['total'] or 0
    
    # KoraQuest commission
    koraquest_commission = purchases.aggregate(total=Sum('koraquest_commission_amount'))['total'] or 0
    monthly_koraquest_commission = monthly_purchases.aggregate(
        total=Sum('koraquest_commission_amount')
    )['total'] or 0
    
    data = {
        'vendor': UserSerializer(vendor).data,
        'statistics': {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'monthly_sales': monthly_purchases.count(),
            'koraquest_commission': koraquest_commission,
            'monthly_koraquest_commission': monthly_koraquest_commission,
            'commission_rate': 80,
            'koraquest_rate': 20
        }
    }
    
    return Response(data)


# QR Code Purchase Flow (KoraQuest specific)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_purchases_by_qr(request):
    """Get purchases from QR code (KoraQuest only)"""
    if not request.user.is_koraquest():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    qr_data = request.data.get('qr_data')
    if not qr_data:
        return Response({'error': 'QR data is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode QR data
        decoded_data = decode_qr_data(qr_data.strip())
        
        if isinstance(decoded_data, dict) and 'error' in decoded_data:
            return Response({'error': decoded_data['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get purchase information
        purchase_info = get_user_purchases_from_qr(decoded_data)
        
        if not purchase_info.get('purchases'):
            return Response({
                'error': 'No pending purchases found in this QR code',
                'purchases': [],
                'buyer': purchase_info.get('buyer', {})
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(purchase_info)
        
    except Exception as e:
        return Response(
            {'error': f'Error processing QR code: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_purchase_pickup(request):
    """Complete purchase pickup (KoraQuest only)"""
    if not request.user.is_koraquest():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    purchase_id = request.data.get('purchase_id')
    if not purchase_id:
        return Response({'error': 'purchase_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        return Response({'error': 'Purchase not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if purchase.status not in ['awaiting_pickup', 'awaiting_delivery']:
        return Response(
            {'error': f'Invalid purchase status: {purchase.status}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    
    # Regenerate buyer's QR code
    try:
        update_user_qr_code(buyer)
    except Exception as e:
        pass  # QR update failure shouldn't break the flow
    
    return Response({
        'message': 'Purchase confirmed successfully',
        'vendor_payment': str(purchase.vendor_payment_amount),
        'koraquest_commission': str(purchase.koraquest_commission_amount)
    })
