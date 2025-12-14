# Kicks_life 250 👟

Kicks_life 250 is a Django-based e-commerce web application specialized in buying and selling shoes in Rwanda. From sneakers to boots, casual to formal - find your perfect kicks!

## 🌐 Demo UI

- **Live Website**: [Kicks_life 250 Marketplace](https://kickslife250.bonasolutions.tech)
- **GitHub Repository**: [Kicks_life 250](https://github.com/hirwacedric123/kicks_life_final)

## 🚀 Features

### 👤 User Features
- User Authentication System
- Browse shoes by category (Sneakers, Boots, Formal, Athletic, etc.)
- Advanced search and filtering
- Product reviews and ratings
- Wishlist/Bookmark system
- QR Code-based secure checkout
- Order tracking

### 🏪 Vendor Features
- Vendor account registration
- Product management dashboard
- Inventory tracking
- Sales analytics
- Commission system (80/20 split)

### 🎯 Platform Features
- QR Code Generation and Processing
- Account Upgrading (From Buyer to Vendor)
- Media File Management
- Email Integration (with OTP support)
- Secure payment processing
- Home delivery or pickup options

## 👟 Shoe Categories

- **Sneakers**: Latest trendy sneakers and street fashion
- **Boots**: Stylish boots for all occasions
- **Formal Shoes**: Professional footwear for work and events
- **Sandals & Slippers**: Comfortable everyday wear
- **Athletic & Sports**: Performance shoes for athletes
- **Casual Shoes**: Everyday comfortable footwear
- **Kids Shoes**: Quality footwear for children
- **Other**: Specialty and unique footwear

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8+
- pip (Python package manager)
- Git

## 🛠️ Installation

1. Clone the repository
```bash
git clone https://github.com/hirwacedric123/kicks_life_final.git
cd kicks_life_final
```

2. Create a virtual environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up the database
```bash
python manage.py migrate
```

5. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

6. Collect static files
```bash
python manage.py collectstatic
```

## ⚙️ Configuration

1. Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

2. Update email settings in `KoraQuest/settings.py` if needed:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

For more details, check:
- [Django Email Documentation](https://docs.djangoproject.com/en/5.2/topics/email)

## 🚀 Running the Application

1. Start the development server
```bash
python manage.py runserver
```

2. Access the application:
- Main site: http://127.0.0.1:8000
- Admin interface: http://127.0.0.1:8000/admin

## 🌐 Deployment

This project can be deployed to various platforms. Choose the one that best fits your needs:

### Free Hosting Options (with Custom Domain Support)

1. **Render** (Recommended - Free with custom domain)
   - ✅ Free tier available
   - ✅ Custom domain support (FREE)
   - ✅ Automatic SSL certificates
   - 📖 See `DEPLOYMENT.md` for detailed instructions

2. **Fly.io** (Free tier with custom domain)
   - ✅ Free tier available
   - ✅ Custom domain support (FREE)
   - ✅ Global edge network
   - 📖 See `FLYIO_DEPLOYMENT.md` for detailed instructions

### Other Deployment Options

3. **PythonAnywhere**
   - Free tier available (subdomain only)
   - Custom domain requires $5/month (Hacker plan)
   - 📖 See `PYTHONANYWHERE_DEPLOYMENT.md` for detailed instructions

### Quick Start

**For Render:**
```bash
# See DEPLOYMENT.md
```

**For Fly.io:**
```bash
# Install Fly.io CLI
brew install flyctl  # macOS
# or
curl -L https://fly.io/install.sh | sh  # Linux

# Login and deploy
flyctl auth login
flyctl launch
flyctl deploy
# See FLYIO_DEPLOYMENT.md for full instructions
```

**For PythonAnywhere:**
```bash
# See PYTHONANYWHERE_DEPLOYMENT.md
```

For more information, see:
- `DEPLOYMENT.md` - Render deployment guide
- `FLYIO_DEPLOYMENT.md` - Fly.io deployment guide
- `PYTHONANYWHERE_DEPLOYMENT.md` - PythonAnywhere deployment guide
- `FREE_HOSTING_OPTIONS.md` - Comparison of free hosting options

## 📁 Project Structure

```
kicks_life_final/
├── authentication/       # Authentication and main app
├── KoraQuest/           # Django project settings
├── static/              # Static files (CSS, JS, images)
├── staticfiles/         # Collected static files (generated)
├── media/               # User uploaded files (product images)
├── requirements.txt     # Python dependencies
├── manage.py           # Django management script
└── README.md           # This file
```

## 💳 Payment & Commission

### Revenue Split
- **Vendors**: Receive 80% of product sale price
- **Kicks_life 250**: Receives 20% commission + full delivery fees

### Payment Methods
- Mobile Money (MoMo)
- Credit Card

### Delivery Options
- **Pickup**: Free pickup from Kicks_life 250 location
- **Home Delivery**: RWF 5,000 delivery fee

## 🔒 Security Notes

### Production Settings
- Set `DEBUG = False`
- Use a strong `SECRET_KEY` (use environment variables)
- Configure proper `ALLOWED_HOSTS`
- Use secure email settings
- Enable HTTPS
- Use PostgreSQL or MySQL instead of SQLite

### Development Settings
- SQLite database is used by default
- Debug mode is enabled
- Email backend is set to console

## 📝 Additional Notes

- QR codes are configured to update every 10 minutes for security
- Static files are served from the 'staticfiles' directory
- Media files (product images) are stored in the 'media' directory
- The project uses Django's built-in authentication system with custom user model
- All prices are in Rwandan Francs (RWF)

## 🎨 User Roles

1. **User**: Regular customers who can browse and purchase shoes
2. **Vendor**: Sellers who can list and manage their shoe inventory
3. **Staff**: Platform moderators with management permissions
4. **Kicks_life 250**: Platform administrators with full access

## 📊 API Endpoints

The platform includes a REST API for integration. See `API_DOCUMENTATION.md` for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Development Team - Kicks_life 250
- Based on KoraQuest marketplace platform

## 🙏 Acknowledgments

- Django Framework
- Python Community
- All contributors and shoe enthusiasts
- Rwanda's vibrant e-commerce community

## 🆘 Support

For support, email support@kickslife250.rw or open an issue in the GitHub repository.

## 🔗 Links

- **Website**: https://kickslife250.bonasolutions.tech
- **GitHub**: https://github.com/hirwacedric123/kicks_life_final
- **Documentation**: See API_DOCUMENTATION.md

---

**Made with ❤️ for shoe lovers in Rwanda** 👟🇷🇼
