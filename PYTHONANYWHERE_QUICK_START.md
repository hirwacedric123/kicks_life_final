# PythonAnywhere Quick Start Guide

## ⚠️ Custom Domain Requirement

**PythonAnywhere FREE plan does NOT support custom domains.**

You need the **Hacker plan ($5/month)** to use `kickslife250.com`.

## Quick Deployment Steps

### 1. Upgrade Account
- Go to PythonAnywhere → Account → Upgrade
- Select **Hacker plan ($5/month)**

### 2. Upload Code
```bash
cd ~
git clone https://github.com/yourusername/kicks_life_final.git
cd kicks_life_final
```

### 3. Set Up Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
In **Web** tab → **Environment variables**, add:
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False`
- `ALLOWED_HOSTS=kickslife250.com,www.kickslife250.com,yourusername.pythonanywhere.com`
- `CUSTOM_DOMAIN=kickslife250.com`
- `PYTHONANYWHERE_USERNAME=yourusername` (your PythonAnywhere username)

### 5. Run Setup Commands
```bash
cd ~/kicks_life_final
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Optional
```

### 6. Configure Web App
1. **Web** tab → **Add a new web app** → **Manual configuration**
2. Edit **WSGI configuration file** (see full guide for code)
3. **Static files** mapping:
   - `/static/` → `/home/yourusername/kicks_life_final/staticfiles`
   - `/media/` → `/home/yourusername/kicks_life_final/media`
4. **Domain**: Set to `www.kickslife250.com`

### 7. Configure DNS (DreamHost)
1. Log in to DreamHost
2. Go to **Domains** → **DNS**
3. Add CNAME record:
   - Name: `www`
   - Value: `webapp-XXXX.pythonanywhere.com` (from PythonAnywhere)
4. Set up redirect: `kickslife250.com` → `www.kickslife250.com`

### 8. Enable SSL
1. **Web** tab → **Security** → **HTTPS certificate**
2. Select **Auto-renewed Let's Encrypt certificate**
3. Enter domain: `www.kickslife250.com`

### 9. Reload
Click the green **Reload** button in **Web** tab

## WSGI Configuration

Replace content of WSGI file with:

```python
import os
import sys

path = '/home/yourusername/kicks_life_final'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'KoraQuest.settings'

activate_this = '/home/yourusername/kicks_life_final/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Replace `yourusername` with your actual PythonAnywhere username!**

## Common Issues

### 502 Bad Gateway
- Check WSGI file path
- Verify virtual environment path
- Check error logs in **Web** tab

### Static Files Not Loading
- Run `python manage.py collectstatic --noinput`
- Verify static files mapping in **Web** tab

### Domain Not Working
- Wait for DNS propagation (up to 48 hours)
- Verify DNS records in DreamHost
- Check domain is set in PythonAnywhere **Web** tab

## Updating Your App

```bash
cd ~/kicks_life_final
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then **Reload** in **Web** tab.

## Full Documentation

See `PYTHONANYWHERE_DEPLOYMENT.md` for detailed instructions.

