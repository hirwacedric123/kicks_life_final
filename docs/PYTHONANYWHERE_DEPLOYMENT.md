# Deploying KicksLife250 to PythonAnywhere (Free Plan)

This guide will walk you through deploying your Django application to PythonAnywhere's **FREE plan** with username `kickslife250`. Your site will be available at `kickslife250.pythonanywhere.com`.

## ⚠️ Free Plan Limitations

**PythonAnywhere's FREE plan:**
- ✅ Free hosting with PythonAnywhere subdomain (`kickslife250.pythonanywhere.com`)
- ✅ 512 MB disk space
- ✅ 1 web app
- ✅ SSL/HTTPS support
- ❌ **NO custom domains** (requires Hacker plan at $5/month)
- ❌ Limited CPU time (100 seconds per day)
- ❌ Web app sleeps after inactivity

**Note:** If you want to use a custom domain (`kickslife250.com`), you'll need to upgrade to the Hacker plan ($5/month). This guide focuses on the free plan.

## Prerequisites

1. A PythonAnywhere account with username `kickslife250` (sign up at https://www.pythonanywhere.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Basic knowledge of command line and Django

## Step 1: Upload Your Code to PythonAnywhere

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
   (Replace `yourusername` with your actual GitHub username)

4. Navigate to the project directory:
   ```bash
   cd kicks_life_final
   ```

### Option B: Using Files Tab

1. Go to the **Files** tab in PythonAnywhere
2. Navigate to your home directory (`/home/kickslife250/`)
3. Upload your project files (or use the uploader)

## Step 2: Set Up Python Virtual Environment

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

## Step 3: Configure Django Settings

The Django settings file (`KoraQuest/settings.py`) is already configured to automatically detect PythonAnywhere and add the correct domain to `ALLOWED_HOSTS`. However, you need to set the environment variable.

**Note:** The settings file will automatically:
- Detect PythonAnywhere from the `PYTHONANYWHERE_USERNAME` environment variable
- Add `kickslife250.pythonanywhere.com` to `ALLOWED_HOSTS`
- Configure CSRF trusted origins
- Set up CORS settings

You just need to set the environment variable in Step 4.

## Step 4: Set Up Environment Variables

1. First, generate a SECRET_KEY in the Bash console:
   ```bash
   cd ~/kicks_life_final
   source venv/bin/activate
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the generated key.

2. Go to the **Web** tab in PythonAnywhere
3. Scroll down to **Environment variables** section
4. Add these environment variables:

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `SECRET_KEY` | (Paste the generated key) | Django secret key |
   | `DEBUG` | `False` | Debug mode (False for production) |
   | `PYTHONANYWHERE_USERNAME` | `kickslife250` | Your PythonAnywhere username |
   | `EMAIL_HOST` | `smtp.gmail.com` | SMTP server (optional) |
   | `EMAIL_PORT` | `587` | SMTP port (optional) |
   | `EMAIL_USE_TLS` | `True` | Use TLS (optional) |
   | `EMAIL_HOST_USER` | Your email | Email username (optional) |
   | `EMAIL_HOST_PASSWORD` | Your app password | Email password (optional) |

   **Important:** The `PYTHONANYWHERE_USERNAME` variable will automatically configure `ALLOWED_HOSTS` to include `kickslife250.pythonanywhere.com`.

## Step 5: Run Database Migrations

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
   Follow the prompts to create your admin account.

3. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

## Step 6: Configure Web App in PythonAnywhere

1. Go to the **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not "Django")
4. Select Python version (3.10 recommended)
5. Click **Next** → **Finish**

## Step 7: Configure WSGI File

1. In the **Web** tab, click on the WSGI configuration file link (usually `/var/www/kickslife250_pythonanywhere_com_wsgi.py`)
2. Delete all the default content
3. Add this configuration:

```python
import os
import sys

# Add your project directory to the Python path
path = '/home/kickslife250/kicks_life_final'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'KoraQuest.settings'

# Set PythonAnywhere username for automatic ALLOWED_HOSTS configuration
os.environ['PYTHONANYWHERE_USERNAME'] = 'kickslife250'

# Activate your virtual environment
activate_this = '/home/kickslife250/kicks_life_final/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 8: Configure Static Files and Media Files

1. In the **Web** tab, scroll down to **Static files**
2. Add these mappings:

   | URL | Directory |
   |-----|-----------|
   | `/static/` | `/home/kickslife250/kicks_life_final/staticfiles` |
   | `/media/` | `/home/kickslife250/kicks_life_final/media` |

3. Click **Save**

## Step 9: Set Up SSL/HTTPS Certificate (Optional but Recommended)

1. In PythonAnywhere **Web** tab, scroll to **Security** section
2. Click the pencil icon next to **HTTPS certificate**
3. Select **Auto-renewed Let's Encrypt certificate**
4. Enter your domain: `kickslife250.pythonanywhere.com`
5. Click **Save**
6. PythonAnywhere will automatically obtain and renew the SSL certificate

## Step 10: Reload Web App

1. In the **Web** tab, click the green **Reload** button
2. Wait for the reload to complete (usually takes 10-30 seconds)
3. Your site should now be accessible at `https://kickslife250.pythonanywhere.com`

## Step 11: Verify Deployment

1. Visit `https://kickslife250.pythonanywhere.com` in your browser
2. Check that:
   - Site loads correctly
   - Static files (CSS, JS, images) load
   - Media files (if any) load
   - Admin panel works: `https://kickslife250.pythonanywhere.com/admin`
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

### Domain Not Working

1. Verify `PYTHONANYWHERE_USERNAME` environment variable is set to `kickslife250`
2. Check that `ALLOWED_HOSTS` includes `kickslife250.pythonanywhere.com`
3. Verify WSGI file path is correct: `/home/kickslife250/kicks_life_final`
4. Check the error log in the **Web** tab for specific issues

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
| `PYTHONANYWHERE_USERNAME` | Yes | Your PythonAnywhere username | `kickslife250` |
| `EMAIL_HOST` | No | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | No | SMTP port | `587` |
| `EMAIL_USE_TLS` | No | Use TLS | `True` |
| `EMAIL_HOST_USER` | No | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | No | Email password | App password |
| `DEFAULT_FROM_EMAIL` | No | Default sender | `KicksLife250 <noreply@kickslife250.com>` |

**Note:** `ALLOWED_HOSTS` is automatically configured based on `PYTHONANYWHERE_USERNAME`. You don't need to set it manually.

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

## Free Plan Limitations & Considerations

**Current Setup (Free Plan):**
- ✅ Site available at `https://kickslife250.pythonanywhere.com`
- ✅ SSL/HTTPS support
- ✅ All Django features work
- ❌ Custom domain not available (requires Hacker plan)
- ⚠️ Web app sleeps after 3 months of inactivity (free accounts)
- ⚠️ Limited CPU time (100 seconds per day)

**Upgrading to Hacker Plan ($5/month):**
If you want to use `kickslife250.com` instead of the PythonAnywhere subdomain:
1. Upgrade to Hacker plan in PythonAnywhere
2. Follow the custom domain setup steps (DNS configuration)
3. Update environment variables to include custom domain

## Cost Summary

- **Current Plan**: FREE (using `kickslife250.pythonanywhere.com`)
- **Hacker Plan**: $5/month (if you want custom domain `kickslife250.com`)

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

Your site should now be live at `https://kickslife250.pythonanywhere.com`

## Quick Reference

- **Your PythonAnywhere Username**: `kickslife250`
- **Your Site URL**: `https://kickslife250.pythonanywhere.com`
- **Project Path**: `/home/kickslife250/kicks_life_final`
- **Virtual Environment**: `/home/kickslife250/kicks_life_final/venv`
- **Static Files**: `/home/kickslife250/kicks_life_final/staticfiles`
- **Media Files**: `/home/kickslife250/kicks_life_final/media`

