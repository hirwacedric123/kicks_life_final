from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import (
    User, Post, Purchase, Bookmark, ProductImage, 
    UserQRCode, OTPVerification, ProductReview
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'role', 'is_vendor_role', 'profile_picture',
            'total_sales', 'total_purchases', 'date_joined', 'last_login',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'total_sales', 'total_purchases']
    
    def validate(self, attrs):
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'display_order', 'created_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview model"""
    reviewer = UserSerializer(read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'reviewer', 'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model"""
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()
    auxiliary_images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'description', 'image', 'price', 'category',
            'inventory', 'total_purchases', 'created_at', 'updated_at',
            'user', 'likes_count', 'average_rating', 'review_count',
            'is_sold_out', 'auxiliary_images', 'reviews'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_purchases']
    
    def get_likes_count(self, obj):
        return obj.total_likes()
    
    def get_average_rating(self, obj):
        return obj.average_rating()
    
    def get_review_count(self, obj):
        return obj.review_count()
    
    def get_is_sold_out(self, obj):
        return obj.is_sold_out()


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""
    auxiliary_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Post
        fields = [
            'title', 'description', 'image', 'price', 'category',
            'inventory', 'auxiliary_images'
        ]
    
    def create(self, validated_data):
        auxiliary_images = validated_data.pop('auxiliary_images', [])
        post = Post.objects.create(**validated_data)
        
        for i, image in enumerate(auxiliary_images):
            ProductImage.objects.create(
                product=post,
                image=image,
                display_order=i
            )
        
        return post


class PurchaseSerializer(serializers.ModelSerializer):
    """Serializer for Purchase model"""
    buyer = UserSerializer(read_only=True)
    product = PostSerializer(read_only=True)
    koraquest_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Purchase
        fields = [
            'id', 'order_id', 'buyer', 'product', 'quantity', 'purchase_price',
            'status', 'delivery_method', 'payment_method', 'delivery_fee',
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'created_at', 'updated_at', 'koraquest_user', 'pickup_confirmed_at',
            'vendor_payment_sent', 'koraquest_commission_sent',
            'vendor_payment_amount', 'koraquest_commission_amount'
        ]
        read_only_fields = [
            'id', 'order_id', 'created_at', 'updated_at', 'koraquest_user',
            'pickup_confirmed_at', 'vendor_payment_sent', 'koraquest_commission_sent',
            'vendor_payment_amount', 'koraquest_commission_amount'
        ]


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating purchases"""
    class Meta:
        model = Purchase
        fields = [
            'product', 'quantity', 'delivery_method', 'payment_method',
            'delivery_address', 'delivery_latitude', 'delivery_longitude'
        ]
    
    def create(self, validated_data):
        validated_data['buyer'] = self.context['request'].user
        validated_data['purchase_price'] = validated_data['product'].price * validated_data['quantity']
        return super().create(validated_data)


class BookmarkSerializer(serializers.ModelSerializer):
    """Serializer for Bookmark model"""
    user = UserSerializer(read_only=True)
    post = PostSerializer(read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserQRCodeSerializer(serializers.ModelSerializer):
    """Serializer for UserQRCode model"""
    user = UserSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = UserQRCode
        fields = [
            'id', 'user', 'qr_data', 'qr_image', 'created_at', 'updated_at',
            'expires_at', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class OTPVerificationSerializer(serializers.ModelSerializer):
    """Serializer for OTPVerification model"""
    user = UserSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPVerification
        fields = [
            'id', 'user', 'otp_code', 'purpose', 'created_at', 'expires_at',
            'is_used', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class VendorStatisticsSerializer(serializers.Serializer):
    """Serializer for vendor statistics"""
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_sales = serializers.IntegerField()
    koraquest_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_koraquest_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    commission_rate = serializers.IntegerField()
    koraquest_rate = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_posts = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_bookmarks = serializers.IntegerField()
    recent_posts = PostSerializer(many=True)
    recent_purchases = PurchaseSerializer(many=True)
