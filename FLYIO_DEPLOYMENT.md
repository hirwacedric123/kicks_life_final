# Deploying KicksLife250 to Fly.io with Custom Domain

This guide will walk you through deploying your Django application to Fly.io and connecting your custom domain `kickslife250.com` from DreamHost.

## Prerequisites

1. A Fly.io account (sign up at https://fly.io - free tier available)
2. Fly.io CLI installed on your local machine
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
4. Access to your DreamHost DNS settings for `kickslife250.com`

## Step 1: Install Fly.io CLI

### macOS
```bash
brew install flyctl
```

### Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### Windows
Download from: https://fly.io/docs/hands-on/install-flyctl/

### Verify Installation
```bash
flyctl version
```

## Step 2: Login to Fly.io

```bash
flyctl auth login
```

This will open your browser to authenticate. After logging in, you'll be redirected back to the terminal.

## Step 3: Initialize Your App

Navigate to your project directory:

```bash
cd /mnt/data/PROJECTS/Cedric_Personal/kicks_life_final
```

Initialize Fly.io app (this will use the existing `fly.toml`):

```bash
flyctl launch
```

**When prompted:**
- **App name:** `kickslife250` (or choose your own)
- **Region:** Choose closest to your users (e.g., `iad` for US East, `ord` for US Central)
- **PostgreSQL:** Type `n` (we'll set up database separately if needed)
- **Redis:** Type `n` (optional, add later if needed)

This will create your app on Fly.io and may update `fly.toml` if needed.

## Step 4: Set Environment Variables

Set your environment variables using Fly.io secrets:

```bash
# Generate a secret key first
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then set the secrets:

```bash
flyctl secrets set SECRET_KEY="your-generated-secret-key-here"
flyctl secrets set DEBUG="False"
flyctl secrets set ALLOWED_HOSTS="kickslife250.fly.dev,kickslife250.com,www.kickslife250.com"
flyctl secrets set CUSTOM_DOMAIN="kickslife250.com"
flyctl secrets set FLY_APP_NAME="kickslife250"
```

**Optional (for email functionality):**
```bash
flyctl secrets set EMAIL_HOST="smtp.gmail.com"
flyctl secrets set EMAIL_PORT="587"
flyctl secrets set EMAIL_USE_TLS="True"
flyctl secrets set EMAIL_HOST_USER="your-email@gmail.com"
flyctl secrets set EMAIL_HOST_PASSWORD="your-app-password"
flyctl secrets set DEFAULT_FROM_EMAIL="KicksLife250 <noreply@kickslife250.com>"
```

**Optional (for CORS):**
```bash
flyctl secrets set CORS_ALLOWED_ORIGINS="https://kickslife250.com,https://www.kickslife250.com"
```

**View all secrets:**
```bash
flyctl secrets list
```

## Step 5: Set Up Database (Optional)

### Option A: Use SQLite (Free, but ephemeral)
SQLite will work but data is lost on each deployment. Good for testing.

### Option B: Use Fly.io PostgreSQL (Recommended for Production)

Create a PostgreSQL database:

```bash
flyctl postgres create --name kickslife250-db --region iad
```

**Note the connection details** from the output, then attach it to your app:

```bash
flyctl postgres attach kickslife250-db --app kickslife250
```

This automatically sets the `DATABASE_URL` environment variable.

### Option C: Use External Database
If you have an external PostgreSQL database, set the connection string:

```bash
flyctl secrets set DATABASE_URL="postgresql://user:password@host:port/dbname"
```

## Step 6: Deploy Your Application

Deploy to Fly.io:

```bash
flyctl deploy
```

This will:
1. Build your Docker image
2. Push it to Fly.io
3. Deploy your application

**First deployment may take 5-10 minutes.**

## Step 7: Run Database Migrations

After deployment, run migrations:

```bash
flyctl ssh console -C "python manage.py migrate"
```

Or if you prefer to run it locally and connect:

```bash
flyctl ssh console
# Then inside the console:
python manage.py migrate
python manage.py collectstatic --noinput
exit
```

## Step 8: Create Superuser (Optional)

Create an admin user:

```bash
flyctl ssh console -C "python manage.py createsuperuser"
```

Or interactively:

```bash
flyctl ssh console
python manage.py createsuperuser
# Follow prompts
exit
```

## Step 9: Verify Initial Deployment

Your app should now be live at:
```
https://kickslife250.fly.dev
```

Test it in your browser!

## Step 10: Set Up Custom Domain

### 10.1: Add Certificate for Your Domain

Add SSL certificate for your custom domain:

```bash
flyctl certs add kickslife250.com
flyctl certs add www.kickslife250.com
```

This will provide you with DNS records to add.

### 10.2: Configure DNS on DreamHost

1. Log in to your DreamHost account
2. Go to **Domains** → **DNS**
3. Select `kickslife250.com`

**For www subdomain (CNAME):**
- Type: `CNAME`
- Name: `www`
- Value: `kickslife250.fly.dev` (or the value shown by `flyctl certs show`)
- TTL: `3600` (or default)

**For root domain (@):**
You have two options:

**Option A: A Record (if Fly.io provides IP)**
- Type: `A`
- Name: `@` (or leave blank)
- Value: IP address from Fly.io (check with `flyctl certs show kickslife250.com`)
- TTL: `3600`

**Option B: Redirect (Recommended)**
- Use DreamHost's redirect feature
- Go to **Domains** → **Manage Domains**
- Click **Edit** next to `kickslife250.com`
- Enable **Redirect** and set to `www.kickslife250.com`

### 10.3: Verify Certificate

Check certificate status:

```bash
flyctl certs show kickslife250.com
flyctl certs show www.kickslife250.com
```

Wait for status to show `Issued` (may take a few minutes).

### 10.4: Update Environment Variables

Make sure your domain is in ALLOWED_HOSTS:

```bash
flyctl secrets set ALLOWED_HOSTS="kickslife250.fly.dev,kickslife250.com,www.kickslife250.com"
```

### 10.5: Redeploy

Redeploy to apply changes:

```bash
flyctl deploy
```

## Step 11: Verify Custom Domain

Wait for DNS propagation (can take up to 48 hours, usually much faster), then visit:

```
https://www.kickslife250.com
https://kickslife250.com (if you set up A record or redirect)
```

## Troubleshooting

### App Won't Start

1. **Check logs:**
   ```bash
   flyctl logs
   ```

2. **Check app status:**
   ```bash
   flyctl status
   ```

3. **SSH into the app:**
   ```bash
   flyctl ssh console
   ```

### Static Files Not Loading

1. **Check if collectstatic ran:**
   ```bash
   flyctl ssh console -C "ls -la /app/staticfiles"
   ```

2. **Run collectstatic manually:**
   ```bash
   flyctl ssh console -C "python manage.py collectstatic --noinput"
   ```

3. **Redeploy:**
   ```bash
   flyctl deploy
   ```

### Database Connection Issues

1. **Check DATABASE_URL:**
   ```bash
   flyctl secrets list
   ```

2. **Verify database is running:**
   ```bash
   flyctl postgres list
   ```

3. **Test connection:**
   ```bash
   flyctl ssh console -C "python manage.py dbshell"
   ```

### Custom Domain Not Working

1. **Check DNS records:**
   ```bash
   dig www.kickslife250.com
   nslookup www.kickslife250.com
   ```

2. **Verify certificate:**
   ```bash
   flyctl certs show www.kickslife250.com
   ```

3. **Check ALLOWED_HOSTS:**
   ```bash
   flyctl secrets list
   ```

4. **Wait for DNS propagation** (can take up to 48 hours)

### 502 Bad Gateway

1. **Check app logs:**
   ```bash
   flyctl logs
   ```

2. **Restart the app:**
   ```bash
   flyctl apps restart kickslife250
   ```

3. **Check machine status:**
   ```bash
   flyctl status
   ```

## Common Commands

### View Logs
```bash
flyctl logs
```

### SSH into App
```bash
flyctl ssh console
```

### Run Django Commands
```bash
flyctl ssh console -C "python manage.py <command>"
```

### View App Status
```bash
flyctl status
```

### List Secrets
```bash
flyctl secrets list
```

### Set Secret
```bash
flyctl secrets set KEY="value"
```

### Remove Secret
```bash
flyctl secrets unset KEY
```

### Deploy
```bash
flyctl deploy
```

### Open App in Browser
```bash
flyctl open
```

### Scale App
```bash
flyctl scale count 1  # Number of instances
flyctl scale vm shared-cpu-1x  # VM size
```

## Updating Your Application

To deploy updates:

1. **Make your changes locally**

2. **Commit and push to Git:**
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```

3. **Deploy to Fly.io:**
   ```bash
   flyctl deploy
   ```

4. **Run migrations (if needed):**
   ```bash
   flyctl ssh console -C "python manage.py migrate"
   ```

5. **Collect static files (if needed):**
   ```bash
   flyctl ssh console -C "python manage.py collectstatic --noinput"
   ```

## Fly.io Free Tier Limitations

Fly.io free tier includes:
- **3 shared-cpu-1x VMs** (can be used for app + database)
- **3GB persistent volume storage**
- **160GB outbound data transfer**

**Important Notes:**
- Machines auto-sleep after inactivity (free tier)
- First request after sleep may take a few seconds (cold start)
- Consider upgrading for production traffic

## Scaling

### Scale Up (More Resources)
```bash
flyctl scale vm shared-cpu-2x  # Better CPU
flyctl scale count 2  # More instances
```

### Scale Down (Save Resources)
```bash
flyctl scale vm shared-cpu-1x  # Basic CPU
flyctl scale count 1  # Single instance
```

## Monitoring

### View Metrics
```bash
flyctl metrics
```

### View Logs in Real-time
```bash
flyctl logs --follow
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Django secret key | Auto-generated |
| `DEBUG` | Yes | Debug mode | `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated hosts | `kickslife250.fly.dev,kickslife250.com` |
| `FLY_APP_NAME` | Yes | Your Fly.io app name | `kickslife250` |
| `CUSTOM_DOMAIN` | No | Your custom domain | `kickslife250.com` |
| `DATABASE_URL` | No | PostgreSQL connection string | Auto-set if using Fly Postgres |
| `EMAIL_HOST` | No | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | No | SMTP port | `587` |
| `EMAIL_USE_TLS` | No | Use TLS | `True` |
| `EMAIL_HOST_USER` | No | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | No | Email password | App password |
| `DEFAULT_FROM_EMAIL` | No | Default sender | `KicksLife250 <noreply@kickslife250.com>` |
| `CORS_ALLOWED_ORIGINS` | No | Allowed CORS origins | `https://kickslife250.com` |

## Security Checklist

- ✅ `DEBUG = False` in production
- ✅ Strong `SECRET_KEY` (not the default)
- ✅ HTTPS/SSL enabled (automatic with Fly.io)
- ✅ CSRF protection enabled
- ✅ Secure cookies in production
- ✅ `ALLOWED_HOSTS` properly configured
- ✅ Change default admin password
- ✅ Environment variables stored as secrets

## Cost Estimate

**Free Tier:**
- App: Free (3 shared-cpu-1x VMs)
- Database: Free (if using SQLite or included PostgreSQL)
- Custom Domain: Free
- SSL Certificate: Free (Let's Encrypt)
- **Total: $0/month**

**If you exceed free tier:**
- Additional VMs: ~$1.94/month per shared-cpu-1x
- Additional storage: ~$0.15/GB/month
- Outbound data: $0.02/GB after 160GB

## Support Resources

- Fly.io Documentation: https://fly.io/docs
- Fly.io Community: https://community.fly.io
- Django Documentation: https://docs.djangoproject.com
- DreamHost DNS Help: https://help.dreamhost.com/hc/en-us/articles/214694348-Basic-DNS-records

## Next Steps

1. ✅ Deploy to Fly.io
2. ✅ Set up custom domain
3. ✅ Configure SSL certificate
4. ✅ Test all functionality
5. ⬜ Set up monitoring and alerts
6. ⬜ Configure automated backups (if using PostgreSQL)
7. ⬜ Set up CI/CD pipeline (optional)
8. ⬜ Optimize performance

---

**Happy Deploying! 🚀**

Your site should now be live at `https://www.kickslife250.com`

