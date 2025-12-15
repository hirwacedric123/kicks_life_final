# KoraQuest REST API

A comprehensive REST API for the KoraQuest marketplace platform built with Django REST Framework.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 5.2+
- SQLite (or PostgreSQL for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KoraQuest
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup script**
   ```bash
   python setup_api.py
   ```

4. **Start the development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the API**
   - API Base URL: `http://localhost:8000/auth/api/rest/`
   - Browsable API: `http://localhost:8000/auth/api/rest/`
   - Admin Panel: `http://localhost:8000/admin/`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/auth/api/rest/
```

### Authentication
The API uses Django's session-based authentication. Most endpoints require authentication.

### Key Endpoints

#### Authentication
- `POST /auth/register/` - Register new user
- `POST /auth/login/` - Login user
- `POST /auth/logout/` - Logout user

#### Users
- `GET /users/` - List users (KoraQuest only)
- `GET /users/me/` - Get current user profile
- `PUT /users/update_me/` - Update current user profile
- `POST /users/{id}/become_vendor/` - Convert user to vendor

#### Posts/Products
- `GET /posts/` - List all posts
- `POST /posts/` - Create new post
- `GET /posts/{id}/` - Get post details
- `PUT /posts/{id}/` - Update post
- `DELETE /posts/{id}/` - Delete post
- `POST /posts/{id}/like/` - Like/unlike post
- `POST /posts/{id}/bookmark/` - Bookmark/unbookmark post
- `POST /posts/{id}/purchase/` - Purchase product
- `POST /posts/{id}/add_review/` - Add product review

#### Purchases
- `GET /purchases/` - List purchases
- `GET /purchases/{id}/` - Get purchase details
- `POST /purchases/{id}/update_status/` - Update purchase status (KoraQuest only)

#### Bookmarks
- `GET /bookmarks/` - List user bookmarks
- `POST /bookmarks/` - Create bookmark
- `DELETE /bookmarks/{id}/` - Delete bookmark

#### Reviews
- `GET /reviews/` - List product reviews
- `GET /reviews/{id}/` - Get review details
- `PUT /reviews/{id}/` - Update review
- `DELETE /reviews/{id}/` - Delete review

#### QR Codes (Removed - Not Used)
- QR code functionality has been removed from the application

#### OTP (Removed - Not Used)
- OTP functionality has been removed from the application

#### Dashboard & Statistics
- `GET /dashboard/stats/` - Get dashboard statistics
- `GET /vendors/{id}/statistics/` - Get vendor statistics (KoraQuest only)

#### KoraQuest Specific
- `POST /purchases/complete-pickup/` - Complete purchase pickup

## 🔐 Role-Based Access Control

### User Role
- View and manage own profile
- Create, read, update, delete own posts
- Purchase products
- Bookmark posts
- Review purchased products

### Vendor Role
- All User permissions
- View sales statistics
- Manage product inventory

### Staff Role
- View all users and posts
- Moderate content

### KoraQuest Role
- Full access to all endpoints
- Manage all purchases
- View vendor statistics
- Process purchase confirmations
- Complete purchase pickups

## 📊 Features

### Core Features
- ✅ User registration and authentication
- ✅ Product/Post management
- ✅ Purchase system with status tracking
- ✅ Bookmark system
- ✅ Product reviews and ratings
- ✅ Role-based access control

### Advanced Features
- ✅ Pagination for large datasets
- ✅ Filtering and search capabilities
- ✅ File upload support for images
- ✅ Dashboard statistics
- ✅ Vendor analytics
- ✅ Purchase workflow management
- ✅ CORS support for frontend integration

## 🧪 Testing

### Run the test script
```bash
python test_api.py
```

### Manual testing with curl
```bash
# Register a user
curl -X POST http://localhost:8000/auth/api/rest/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "testpassword123",
    "password_confirm": "testpassword123"
  }'

# Login
curl -X POST http://localhost:8000/auth/api/rest/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'

# Get dashboard stats
curl -X GET http://localhost:8000/auth/api/rest/dashboard/stats/
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file for environment-specific settings:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Django Settings
Key settings in `KoraQuest/settings.py`:

```python
# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📈 Performance Considerations

### Database Optimization
- Use `select_related()` and `prefetch_related()` for related objects
- Implement database indexing for frequently queried fields
- Use pagination for large datasets

### Caching
- Consider implementing Redis caching for frequently accessed data
- Cache user sessions and authentication tokens
- Cache expensive calculations like statistics

### File Storage
- Use cloud storage (AWS S3, Google Cloud Storage) for production
- Implement image optimization and resizing
- Use CDN for static file delivery

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up proper email configuration
- [ ] Configure static file serving
- [ ] Set up SSL/HTTPS
- [ ] Configure CORS for production domains
- [ ] Set up monitoring and logging
- [ ] Implement rate limiting
- [ ] Set up backup strategy

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 API Documentation

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path and virtual environment

2. **Database Errors**
   - Run migrations: `python manage.py migrate`
   - Check database configuration in settings

3. **Permission Errors**
   - Ensure user has correct role for endpoint access
   - Check authentication status

4. **CORS Errors**
   - Add frontend domain to `CORS_ALLOWED_ORIGINS`
   - Check CORS middleware configuration

### Getting Help
- Check the Django REST Framework documentation
- Review the API documentation
- Check server logs for detailed error messages
- Use the browsable API for testing endpoints

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django REST Framework for the excellent API framework
- Django for the robust web framework
- All contributors and users of the KoraQuest platform
