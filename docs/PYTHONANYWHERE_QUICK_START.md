# PythonAnywhere Quick Start Guide (Free Plan)

## Your Deployment Info
- **PythonAnywhere Username**: `kickslife250`
- **Site URL**: `https://kickslife250.pythonanywhere.com`
- **Plan**: FREE (no custom domain support)

## Quick Deployment Steps

### 1. Upload Code
```bash
cd ~
git clone https://github.com/yourusername/kicks_life_final.git
cd kicks_life_final
```
(Replace `yourusername` with your actual GitHub username)

### 2. Set Up Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
In **Web** tab → **Environment variables**, add:
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False`
- `PYTHONANYWHERE_USERNAME=kickslife250` (automatically configures ALLOWED_HOSTS)

### 4. Run Setup Commands
```bash
cd ~/kicks_life_final
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Optional
```

### 5. Configure Web App
1. **Web** tab → **Add a new web app** → **Manual configuration** → Python 3.10
2. Edit **WSGI configuration file** (see below for code)
3. **Static files** mapping:
   - `/static/` → `/home/kickslife250/kicks_life_final/staticfiles`
   - `/media/` → `/home/kickslife250/kicks_life_final/media`

### 6. Enable SSL (Optional but Recommended)
1. **Web** tab → **Security** → **HTTPS certificate**
2. Select **Auto-renewed Let's Encrypt certificate**
3. Enter domain: `kickslife250.pythonanywhere.com`

### 7. Reload
Click the green **Reload** button in **Web** tab

## WSGI Configuration

Replace content of WSGI file with:

```python
import os
import sys

path = '/home/kickslife250/kicks_life_final'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'KoraQuest.settings'
os.environ['PYTHONANYWHERE_USERNAME'] = 'kickslife250'

activate_this = '/home/kickslife250/kicks_life_final/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Common Issues

### 502 Bad Gateway
- Check WSGI file path is `/home/kickslife250/kicks_life_final`
- Verify virtual environment path
- Check error logs in **Web** tab
- Ensure `PYTHONANYWHERE_USERNAME` is set in environment variables

### Static Files Not Loading
- Run `python manage.py collectstatic --noinput`
- Verify static files mapping in **Web** tab
- Check that `STATIC_ROOT` is set correctly

### Domain Not Working
- Verify `PYTHONANYWHERE_USERNAME=kickslife250` is set
- Check that site is accessible at `kickslife250.pythonanywhere.com`
- Check error logs in **Web** tab

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

## Free Plan Limitations

- ✅ Site available at `kickslife250.pythonanywhere.com`
- ✅ SSL/HTTPS support
- ❌ No custom domain (requires Hacker plan $5/month)
- ⚠️ Web app sleeps after 3 months of inactivity
- ⚠️ Limited CPU time (100 seconds per day)

## Quick Reference

- **Project Path**: `/home/kickslife250/kicks_life_final`
- **Virtual Environment**: `/home/kickslife250/kicks_life_final/venv`
- **Static Files**: `/home/kickslife250/kicks_life_final/staticfiles`
- **Media Files**: `/home/kickslife250/kicks_life_final/media`

## Full Documentation

See `PYTHONANYWHERE_DEPLOYMENT.md` for detailed instructions.
