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
    User, Post, Purchase, Bookmark, ProductImage, ProductReview
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    PostSerializer, PostCreateSerializer, PurchaseSerializer, PurchaseCreateSerializer,
    BookmarkSerializer, DashboardStatsSerializer, ProductReviewSerializer
)


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
    filterset_fields = ['role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_login', 'username']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        if self.request.user.is_admin():
            return User.objects.all()
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
        if self.request.user.is_admin():
            return Purchase.objects.all()
        else:
            return Purchase.objects.filter(buyer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update purchase status (Admin only)"""
        if not request.user.is_admin():
            return Response({'error': 'Permission denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        purchase = self.get_object()
        new_status = request.data.get('status')
        tracking_number = request.data.get('tracking_number', '')
        
        if new_status not in dict(Purchase.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        purchase.status = new_status
        if tracking_number:
            purchase.tracking_number = tracking_number
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
# Removed QR Code and OTP ViewSets for simplified workflow


# Dashboard and Statistics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for current user"""
    user = request.user
    
    # Get user's posts (for admin)
    if user.is_admin():
        user_posts = Post.objects.all()
        total_posts = user_posts.count()
    else:
        total_posts = 0
    
    # Get user's purchases
    user_purchases = Purchase.objects.filter(buyer=user)
    total_purchases = user_purchases.count()
    
    # Get user's sales (if admin)
    if user.is_admin():
        admin_sales = Purchase.objects.filter(status='completed')
        total_sales = admin_sales.aggregate(total=Sum('purchase_price'))['total'] or 0
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


# Removed vendor statistics and QR/OTP functions for simplified single-store workflow
