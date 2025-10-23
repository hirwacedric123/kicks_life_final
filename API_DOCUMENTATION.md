# KoraQuest API Documentation

This document provides comprehensive documentation for the KoraQuest REST API endpoints.

## Base URL
```
http://localhost:8000/auth/api/rest/
```

## Authentication
The API uses Django's session-based authentication. You need to be logged in to access most endpoints.

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /auth/api/rest/auth/register/
```
**Request Body:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+250123456789",
    "password": "securepassword",
    "password_confirm": "securepassword"
}
```

#### Login User
```http
POST /auth/api/rest/auth/login/
```
**Request Body:**
```json
{
    "username": "johndoe",
    "password": "securepassword"
}
```

#### Logout User
```http
POST /auth/api/rest/auth/logout/
```

### User Management

#### Get All Users (KoraQuest only)
```http
GET /auth/api/rest/users/
```

#### Get Current User Profile
```http
GET /auth/api/rest/users/me/
```

#### Update Current User Profile
```http
PUT /auth/api/rest/users/update_me/
PATCH /auth/api/rest/users/update_me/
```

#### Convert User to Vendor
```http
POST /auth/api/rest/users/{user_id}/become_vendor/
```

### Post Management

#### Get All Posts
```http
GET /auth/api/rest/posts/
```
**Query Parameters:**
- `category`: Filter by category
- `user`: Filter by user ID
- `price`: Filter by price
- `search`: Search in title and description
- `ordering`: Order by field (created_at, price, total_purchases)

#### Create Post
```http
POST /auth/api/rest/posts/
```
**Request Body:**
```json
{
    "title": "Product Title",
    "description": "Product Description",
    "image": "image_file",
    "price": "99.99",
    "category": "electronics",
    "inventory": 10,
    "auxiliary_images": ["image1.jpg", "image2.jpg"]
}
```

#### Get Post Details
```http
GET /auth/api/rest/posts/{post_id}/
```

#### Update Post
```http
PUT /auth/api/rest/posts/{post_id}/
PATCH /auth/api/rest/posts/{post_id}/
```

#### Delete Post
```http
DELETE /auth/api/rest/posts/{post_id}/
```

#### Like/Unlike Post
```http
POST /auth/api/rest/posts/{post_id}/like/
```

#### Bookmark/Unbookmark Post
```http
POST /auth/api/rest/posts/{post_id}/bookmark/
```

#### Purchase Product
```http
POST /auth/api/rest/posts/{post_id}/purchase/
```
**Request Body:**
```json
{
    "quantity": 2,
    "delivery_method": "pickup",
    "payment_method": "momo",
    "delivery_address": "123 Main St",
    "delivery_latitude": -1.9441,
    "delivery_longitude": 30.0619
}
```

#### Add Product Review
```http
POST /auth/api/rest/posts/{post_id}/add_review/
```
**Request Body:**
```json
{
    "rating": 5,
    "comment": "Great product!"
}
```

### Purchase Management

#### Get All Purchases
```http
GET /auth/api/rest/purchases/
```
**Query Parameters:**
- `status`: Filter by status
- `delivery_method`: Filter by delivery method
- `payment_method`: Filter by payment method
- `buyer`: Filter by buyer ID
- `product`: Filter by product ID

#### Get Purchase Details
```http
GET /auth/api/rest/purchases/{purchase_id}/
```

#### Update Purchase Status (KoraQuest only)
```http
POST /auth/api/rest/purchases/{purchase_id}/update_status/
```
**Request Body:**
```json
{
    "status": "completed"
}
```

### Bookmark Management

#### Get User Bookmarks
```http
GET /auth/api/rest/bookmarks/
```

#### Create Bookmark
```http
POST /auth/api/rest/bookmarks/
```
**Request Body:**
```json
{
    "post": 1
}
```

#### Delete Bookmark
```http
DELETE /auth/api/rest/bookmarks/{bookmark_id}/
```

### Product Reviews

#### Get All Reviews
```http
GET /auth/api/rest/reviews/
```
**Query Parameters:**
- `product`: Filter by product ID
- `reviewer`: Filter by reviewer ID
- `rating`: Filter by rating

#### Get Review Details
```http
GET /auth/api/rest/reviews/{review_id}/
```

#### Update Review
```http
PUT /auth/api/rest/reviews/{review_id}/
PATCH /auth/api/rest/reviews/{review_id}/
```

#### Delete Review
```http
DELETE /auth/api/rest/reviews/{review_id}/
```

### QR Code Management

#### Get User QR Codes
```http
GET /auth/api/rest/qr-codes/
```

#### Generate QR Code
```http
POST /auth/api/rest/qr-codes/generate_qr/
```

### OTP Management

#### Send OTP
```http
POST /auth/api/rest/otp/send_otp/
```
**Request Body:**
```json
{
    "user_id": 1,
    "purpose": "purchase_confirmation"
}
```

#### Verify OTP
```http
POST /auth/api/rest/otp/verify_otp/
```
**Request Body:**
```json
{
    "user_id": 1,
    "otp_code": "123456",
    "purpose": "purchase_confirmation"
}
```

### Dashboard and Statistics

#### Get Dashboard Statistics
```http
GET /auth/api/rest/dashboard/stats/
```

#### Get Vendor Statistics (KoraQuest only)
```http
GET /auth/api/rest/vendors/{vendor_id}/statistics/
```

### KoraQuest Specific Endpoints

#### Get Purchases by QR Code
```http
POST /auth/api/rest/qr/purchases/
```
**Request Body:**
```json
{
    "qr_data": "encoded_qr_data"
}
```

#### Complete Purchase Pickup
```http
POST /auth/api/rest/purchases/complete-pickup/
```
**Request Body:**
```json
{
    "purchase_id": 1
}
```

## Response Format

All API responses follow this format:

### Success Response
```json
{
    "data": {...},
    "message": "Success message"
}
```

### Error Response
```json
{
    "error": "Error message",
    "details": {...}
}
```

### Paginated Response
```json
{
    "count": 100,
    "next": "http://api.example.com/items/?page=2",
    "previous": null,
    "results": [...]
}
```

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Role-Based Access

### User Role
- Can view and manage their own profile
- Can create, read, update, delete their own posts
- Can purchase products
- Can bookmark posts
- Can review products they've purchased

### Vendor Role
- All User permissions
- Can view their sales statistics
- Can manage their product inventory

### Staff Role
- Can view all users and posts
- Can moderate content

### KoraQuest Role
- Full access to all endpoints
- Can manage all purchases
- Can view vendor statistics
- Can process QR code purchases
- Can complete purchase pickups

## Filtering and Search

Most list endpoints support:
- **Filtering**: Use query parameters to filter results
- **Search**: Use `search` parameter for text search
- **Ordering**: Use `ordering` parameter to sort results
- **Pagination**: Use `page` and `page_size` parameters

## Examples

### Creating a Product
```bash
curl -X POST http://localhost:8000/auth/api/rest/posts/ \
  -H "Content-Type: multipart/form-data" \
  -F "title=iPhone 15" \
  -F "description=Latest iPhone model" \
  -F "price=999.99" \
  -F "category=electronics" \
  -F "inventory=5" \
  -F "image=@iphone.jpg"
```

### Purchasing a Product
```bash
curl -X POST http://localhost:8000/auth/api/rest/posts/1/purchase/ \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 1,
    "delivery_method": "pickup",
    "payment_method": "momo"
  }'
```

### Getting Dashboard Statistics
```bash
curl -X GET http://localhost:8000/auth/api/rest/dashboard/stats/
```

## Error Handling

The API provides detailed error messages for common scenarios:

- **Validation Errors**: Field-specific validation messages
- **Permission Errors**: Clear indication of required permissions
- **Not Found Errors**: Resource identification issues
- **Business Logic Errors**: Domain-specific error messages

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Security Considerations

1. **Authentication**: Session-based authentication is used
2. **Authorization**: Role-based access control
3. **CSRF Protection**: Enabled for state-changing operations
4. **Input Validation**: All inputs are validated
5. **File Uploads**: Image uploads are restricted to specific formats

## Development Notes

- The API is built with Django REST Framework
- All endpoints are versioned under `/api/rest/`
- Browsable API is available for development
- CORS is configured for frontend integration
- Pagination is implemented for large datasets
