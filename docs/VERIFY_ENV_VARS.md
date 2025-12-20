# How to Verify Environment Variables in PythonAnywhere

If you're getting `DisallowedHost` errors, verify that your environment variables are set correctly.

## Method 1: Check in PythonAnywhere Console

1. Go to PythonAnywhere → **Consoles** tab
2. Open a **Bash console**
3. Run these commands:

```bash
cd ~/kicks_life_final
source venv/bin/activate
python manage.py shell
```

4. In the Python shell, run:

```python
import os
from django.conf import settings

# Check environment variables
print("CUSTOM_DOMAIN:", os.environ.get('CUSTOM_DOMAIN'))
print("PYTHONANYWHERE_USERNAME:", os.environ.get('PYTHONANYWHERE_USERNAME'))

# Check ALLOWED_HOSTS
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
```

**Expected output:**
```
CUSTOM_DOMAIN: kickslife250.com
PYTHONANYWHERE_USERNAME: kickslife250
ALLOWED_HOSTS: ['localhost', '127.0.0.1', 'kickslife250.pythonanywhere.com', 'kickslife250.com', 'www.kickslife250.com']
```

If `CUSTOM_DOMAIN` is `None` or empty, it's not set in the environment variables.

## Method 2: Check Web Tab Environment Variables

1. Go to PythonAnywhere → **Web** tab
2. Scroll down to **Environment variables** section
3. Verify you see:
   - `CUSTOM_DOMAIN` = `kickslife250.com`
   - `PYTHONANYWHERE_USERNAME` = `kickslife250`

## Method 3: Check WSGI File

The WSGI file might need to set environment variables. Check your WSGI file:

1. Go to **Web** tab
2. Click on the WSGI configuration file link
3. Make sure it sets the environment variables if needed:

```python
os.environ['CUSTOM_DOMAIN'] = 'kickslife250.com'
os.environ['PYTHONANYWHERE_USERNAME'] = 'kickslife250'
```

## Troubleshooting

### If CUSTOM_DOMAIN is None:

1. **Set it in Web tab:**
   - Go to **Web** tab → **Environment variables**
   - Add: `CUSTOM_DOMAIN` = `kickslife250.com`
   - Click **Save**

2. **Reload web app:**
   - Click the green **Reload** button
   - Wait for reload to complete

3. **Verify again:**
   - Run the Python shell check again
   - `CUSTOM_DOMAIN` should now show `kickslife250.com`

### If ALLOWED_HOSTS doesn't include your domain:

1. Check that `CUSTOM_DOMAIN` is set correctly (no www, no https://)
2. Reload the web app
3. The settings should automatically add both `kickslife250.com` and `www.kickslife250.com`

### Common Mistakes:

- ❌ `CUSTOM_DOMAIN=www.kickslife250.com` (should be without www)
- ❌ `CUSTOM_DOMAIN=https://kickslife250.com` (should be without protocol)
- ❌ `CUSTOM_DOMAIN=kickslife250.com/` (should be without trailing slash)
- ✅ `CUSTOM_DOMAIN=kickslife250.com` (correct)

