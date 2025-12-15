# Deploying KicksLife250 to PythonAnywhere with Custom Domain

This guide will walk you through deploying your Django application to PythonAnywhere and connecting your custom domain `kickslife250.com` from DreamHost.

## ⚠️ Important: Custom Domain Limitation

**PythonAnywhere's FREE plan does NOT support custom domains.**

To use your custom domain `kickslife250.com`, you need to upgrade to at least the **Hacker plan ($5/month)**, which allows:
- 1 web app on a custom domain
- 512 MB disk space
- 1 CPU core
- Better performance than free tier

**Free Plan Alternative:** If you want to stay on the free plan, you can use the default PythonAnywhere subdomain (e.g., `yourusername.pythonanywhere.com`), but you won't be able to use `kickslife250.com`.

## Prerequisites

1. A PythonAnywhere account (sign up at https://www.pythonanywhere.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. A paid PythonAnywhere plan (Hacker or higher) for custom domain support
4. Access to your DreamHost DNS settings for `kickslife250.com`

## Step 1: Upgrade to Hacker Plan (Required for Custom Domain)

1. Log in to PythonAnywhere
2. Go to **Account** → **Upgrade**
3. Select **Hacker plan ($5/month)**
4. Complete the payment process

## Step 2: Upload Your Code to PythonAnywhere

### Option A: Using Git (Recommended)

1. Open a **Bash console** in PythonAnywhere
2. Navigate to your home directory:
   ```bash
   cd ~
   ```
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/kicks_life_final.git
   ```
   (Replace with your actual repository URL)

4. Navigate to the project directory:
   ```bash
   cd kicks_life_final
   ```

### Option B: Using Files Tab

1. Go to the **Files** tab in PythonAnywhere
2. Navigate to your home directory
3. Upload your project files (or use the uploader)

## Step 3: Set Up Python Virtual Environment

1. In the Bash console, create a virtual environment:
   ```bash
   cd ~/kicks_life_final
   python3.10 -m venv venv
   ```
   (Use the Python version available on PythonAnywhere, typically 3.10)

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Django Settings

1. In the **Files** tab, navigate to `~/kicks_life_final/KoraQuest/settings.py`

2. Update the following settings for PythonAnywhere:

   - **ALLOWED_HOSTS**: Should include your custom domain
   - **STATIC_ROOT**: Should point to `/home/yourusername/kicks_life_final/staticfiles`
   - **MEDIA_ROOT**: Should point to `/home/yourusername/kicks_life_final/media`

   The settings file should already be configured to read from environment variables, but verify these paths.

## Step 5: Set Up Environment Variables

1. Go to the **Files** tab
2. Navigate to your project directory: `~/kicks_life_final/`
3. Create a `.env` file (or use PythonAnywhere's environment variables feature)

   In the **Web** tab, you can add environment variables. Add these:

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `SECRET_KEY` | (Generate a new one) | Django secret key |
   | `DEBUG` | `False` | Debug mode (False for production) |
   | `ALLOWED_HOSTS` | `kickslife250.com,www.kickslife250.com,yourusername.pythonanywhere.com` | Allowed hosts |
   | `EMAIL_HOST` | `smtp.gmail.com` | SMTP server (optional) |
   | `EMAIL_PORT` | `587` | SMTP port (optional) |
   | `EMAIL_USE_TLS` | `True` | Use TLS (optional) |
   | `EMAIL_HOST_USER` | Your email | Email username (optional) |
   | `EMAIL_HOST_PASSWORD` | Your app password | Email password (optional) |

   **To generate a SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

## Step 6: Run Database Migrations

1. In the Bash console (with venv activated):
   ```bash
   cd ~/kicks_life_final
   source venv/bin/activate
   python manage.py migrate
   ```

2. Create a superuser (if needed):
   ```bash
   python manage.py createsuperuser
   ```

3. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

## Step 7: Configure Web App in PythonAnywhere

1. Go to the **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not "Django")
4. Select Python version (3.10 recommended)
5. Click **Next** → **Finish**

## Step 8: Configure WSGI File

1. In the **Web** tab, click on the WSGI configuration file link
2. Delete all the default content
3. Add this configuration:

```python
import os
import sys

# Add your project directory to the Python path
path = '/home/yourusername/kicks_life_final'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'KoraQuest.settings'

# Activate your virtual environment
activate_this = '/home/yourusername/kicks_life_final/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Important:** Replace `yourusername` with your actual PythonAnywhere username!

## Step 9: Configure Static Files and Media Files

1. In the **Web** tab, scroll down to **Static files**
2. Add these mappings:

   | URL | Directory |
   |-----|-----------|
   | `/static/` | `/home/yourusername/kicks_life_final/staticfiles` |
   | `/media/` | `/home/yourusername/kicks_life_final/media` |

3. Click **Save**

## Step 10: Set Up Custom Domain

1. In the **Web** tab, find **Domain** section
2. Click the pencil icon next to your domain
3. Enter your custom domain: `www.kickslife250.com`
4. Click **Save**

## Step 11: Configure DNS on DreamHost

1. Log in to your DreamHost account
2. Go to **Domains** → **DNS**
3. Select `kickslife250.com`
4. Add/Edit DNS records:

   **For www subdomain (CNAME):**
   - Type: `CNAME`
   - Name: `www`
   - Value: `webapp-XXXX.pythonanywhere.com` (PythonAnywhere will show you this)
   - TTL: `3600` (or default)

   **For root domain (A record or redirect):**
   - Since CNAME can't be used for root domain, you have two options:
   
   **Option A: A Record (if PythonAnywhere provides IP)**
   - Type: `A`
   - Name: `@` (or leave blank)
   - Value: IP address from PythonAnywhere
   - TTL: `3600`
   
   **Option B: Redirect (Recommended)**
   - Use DreamHost's redirect feature to redirect `kickslife250.com` → `www.kickslife250.com`
   - Go to **Domains** → **Manage Domains**
   - Click **Edit** next to `kickslife250.com`
   - Enable **Redirect** and set it to `www.kickslife250.com`

5. **Wait for DNS propagation** (can take 24-48 hours, usually much faster)

## Step 12: Set Up SSL/HTTPS Certificate

1. In PythonAnywhere **Web** tab, scroll to **Security** section
2. Click the pencil icon next to **HTTPS certificate**
3. Select **Auto-renewed Let's Encrypt certificate**
4. Enter your domain: `www.kickslife250.com`
5. Click **Save**
6. PythonAnywhere will automatically obtain and renew the SSL certificate

## Step 13: Reload Web App

1. In the **Web** tab, click the green **Reload** button
2. Wait for the reload to complete
3. Your site should now be accessible at `https://www.kickslife250.com`

## Step 14: Verify Deployment

1. Visit `https://www.kickslife250.com` in your browser
2. Check that:
   - Site loads correctly
   - Static files (CSS, JS, images) load
   - Media files (if any) load
   - Admin panel works: `https://www.kickslife250.com/admin`
   - All pages function correctly

## Troubleshooting

### Site Shows "502 Bad Gateway"

1. Check the **Error log** in the **Web** tab
2. Verify WSGI file path is correct
3. Ensure virtual environment is activated in WSGI file
4. Check that all dependencies are installed

### Static Files Not Loading

1. Verify static files mapping in **Web** tab
2. Run `python manage.py collectstatic --noinput` again
3. Check that `STATIC_ROOT` in settings.py matches the directory in PythonAnywhere

### Database Errors

1. Ensure migrations are run: `python manage.py migrate`
2. Check database file permissions
3. Verify database path in settings.py

### Custom Domain Not Working

1. Verify DNS records are correct in DreamHost
2. Check DNS propagation: Use `nslookup www.kickslife250.com` or `dig www.kickslife250.com`
3. Ensure domain is added in PythonAnywhere **Web** tab
4. Wait for DNS propagation (can take up to 48 hours)

### SSL Certificate Issues

1. Ensure domain is correctly configured in PythonAnywhere
2. Wait a few minutes after requesting certificate
3. Check **Error log** for certificate-related errors
4. Verify DNS is pointing to PythonAnywhere before requesting certificate

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Django secret key | Auto-generated |
| `DEBUG` | Yes | Debug mode | `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated hosts | `kickslife250.com,www.kickslife250.com` |
| `EMAIL_HOST` | No | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | No | SMTP port | `587` |
| `EMAIL_USE_TLS` | No | Use TLS | `True` |
| `EMAIL_HOST_USER` | No | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | No | Email password | App password |
| `DEFAULT_FROM_EMAIL` | No | Default sender | `KicksLife250 <noreply@kickslife250.com>` |

## Updating Your Application

To deploy updates:

1. Pull latest changes in Bash console:
   ```bash
   cd ~/kicks_life_final
   git pull origin main
   ```

2. Activate virtual environment and install new dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run migrations (if any):
   ```bash
   python manage.py migrate
   ```

4. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

5. Reload web app in **Web** tab

## PythonAnywhere Free Plan Alternative

If you want to use the free plan (without custom domain):

1. Follow all steps above EXCEPT Step 1 (upgrade) and Step 10-11 (custom domain)
2. Your site will be available at `yourusername.pythonanywhere.com`
3. Update `ALLOWED_HOSTS` to include `yourusername.pythonanywhere.com`
4. You can still set up SSL for the PythonAnywhere subdomain

## Cost Summary

- **Hacker Plan**: $5/month (required for custom domain)
- **DreamHost Domain**: Already purchased
- **Total**: $5/month for hosting

## Security Checklist

- ✅ `DEBUG = False` in production
- ✅ Strong `SECRET_KEY` (not the default)
- ✅ HTTPS/SSL enabled
- ✅ CSRF protection enabled
- ✅ Secure cookies in production
- ✅ `ALLOWED_HOSTS` properly configured
- ✅ Change default admin password

## Support Resources

- PythonAnywhere Help: https://help.pythonanywhere.com
- PythonAnywhere Community: https://www.pythonanywhere.com/forums/
- Django Documentation: https://docs.djangoproject.com
- DreamHost DNS Help: https://help.dreamhost.com/hc/en-us/articles/214694348-Basic-DNS-records

---

**Happy Deploying! 🚀**

Your site should now be live at `https://www.kickslife250.com`

