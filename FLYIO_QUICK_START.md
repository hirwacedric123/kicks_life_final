# Fly.io Quick Start Guide

## Prerequisites

1. Install Fly.io CLI:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. Login:
   ```bash
   flyctl auth login
   ```

## Quick Deployment Steps

### 1. Initialize App
```bash
cd /mnt/data/PROJECTS/Cedric_Personal/kicks_life_final
flyctl launch
```
- App name: `kickslife250`
- Region: Choose closest (e.g., `iad`)
- PostgreSQL: `n` (add later if needed)
- Redis: `n`

### 2. Set Environment Variables
```bash
# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set secrets
flyctl secrets set SECRET_KEY="your-secret-key"
flyctl secrets set DEBUG="False"
flyctl secrets set ALLOWED_HOSTS="kickslife250.fly.dev,kickslife250.com,www.kickslife250.com"
flyctl secrets set FLY_APP_NAME="kickslife250"
flyctl secrets set CUSTOM_DOMAIN="kickslife250.com"
```

### 3. Deploy
```bash
flyctl deploy
```

### 4. Run Migrations
```bash
flyctl ssh console -C "python manage.py migrate"
```

### 5. Create Superuser (Optional)
```bash
flyctl ssh console -C "python manage.py createsuperuser"
```

### 6. Set Up Custom Domain

**Add certificates:**
```bash
flyctl certs add kickslife250.com
flyctl certs add www.kickslife250.com
```

**Configure DNS (DreamHost):**
- CNAME: `www` → `kickslife250.fly.dev`
- Redirect: `kickslife250.com` → `www.kickslife250.com`

**Verify:**
```bash
flyctl certs show www.kickslife250.com
```

**Redeploy:**
```bash
flyctl deploy
```

## Common Commands

```bash
# View logs
flyctl logs

# SSH into app
flyctl ssh console

# Run Django command
flyctl ssh console -C "python manage.py <command>"

# Deploy updates
flyctl deploy

# Open app
flyctl open

# View status
flyctl status
```

## Troubleshooting

### App won't start
```bash
flyctl logs
flyctl status
```

### Static files not loading
```bash
flyctl ssh console -C "python manage.py collectstatic --noinput"
flyctl deploy
```

### Domain not working
- Wait for DNS propagation (up to 48 hours)
- Check: `flyctl certs show www.kickslife250.com`
- Verify DNS records in DreamHost

## Full Documentation

See `FLYIO_DEPLOYMENT.md` for detailed instructions.

