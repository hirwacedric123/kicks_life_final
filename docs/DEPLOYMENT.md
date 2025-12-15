# Deploying KoraQuest to Render

This guide will walk you through deploying your KoraQuest Django application to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Basic understanding of environment variables

## Deployment Options

You can deploy to Render in two ways:

### Option 1: Using render.yaml (Recommended)

This is the easiest method as it automatically sets up your web service with SQLite database.

**⚠️ Important Note:** This setup uses SQLite on Render's ephemeral filesystem. Your database will be reset when the service restarts or redeploys. This is suitable for testing/demo purposes. For production with persistent data, consider using PostgreSQL (see Alternative Setup below).

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create a new Blueprint on Render**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file
   - Click "Apply" to create the service

3. **Set environment variables**
   After the service is created, go to your web service dashboard and set these environment variables:
   
   **Required:**
   - `ALLOWED_HOSTS`: Your Render domain (e.g., `your-app.onrender.com`)
   - `SECRET_KEY`: Generate a new secret key (will be auto-generated if not set)
   
   **Optional (for email functionality):**
   - `EMAIL_HOST_USER`: Your email address
   - `EMAIL_HOST_PASSWORD`: Your email password or app-specific password
   - `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins (e.g., `https://yourdomain.com,https://anotherdomain.com`)

4. **Access your application**
   - Once deployed, your app will be available at `https://your-app.onrender.com`

### Option 2: Manual Setup

If you prefer to set up services manually:

#### Step 1: Create a Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Fill in the details:
   - Name: `koraquest`
   - Runtime: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn KoraQuest.wsgi:application`
   - Plan: Free (or your preferred plan)

4. **Add Environment Variables:**

   Click "Advanced" and add these environment variables:

   | Key | Value |
   |-----|-------|
   | `PYTHON_VERSION` | `3.11.0` |
   | `SECRET_KEY` | Generate a secure key (see below) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | Your Render domain (e.g., `your-app.onrender.com`) |
   | `EMAIL_HOST` | `smtp.gmail.com` (optional - for OTP emails) |
   | `EMAIL_PORT` | `587` (optional) |
   | `EMAIL_USE_TLS` | `True` (optional) |
   | `EMAIL_HOST_USER` | Your email address (optional) |
   | `EMAIL_HOST_PASSWORD` | Your email password (optional) |
   | `DEFAULT_FROM_EMAIL` | `KoraQuest <noreply@koraquest.com>` (optional) |
   | `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins (optional) |

5. Click "Create Web Service"

## Generating a Secret Key

To generate a secure Django secret key, run this in your terminal:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Or use an online generator like: https://djecrety.ir/

## Email Configuration (Gmail)

If you're using Gmail for sending emails:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "KoraQuest" and click "Generate"
   - Use the generated password as `EMAIL_HOST_PASSWORD`

## Post-Deployment Steps

### 1. Access Admin Panel

A default superuser is automatically created during deployment!

**Default Credentials:**
- Username: `admin`
- Email: `admin@koraquest.com`
- Password: `admin123`

**Admin URL:** `https://your-app.onrender.com/admin`

**⚠️ SECURITY WARNING:** Change the default password immediately after first login!

#### Customizing Superuser Credentials

To use custom credentials, add these environment variables in Render before deployment:

| Variable | Default |
|----------|---------|
| `DJANGO_SUPERUSER_USERNAME` | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | `admin@koraquest.com` |
| `DJANGO_SUPERUSER_PASSWORD` | `admin123` |

For detailed superuser management, see `SUPERUSER_INFO.md`.

### 2. Change Default Password

1. Log in to admin panel with default credentials
2. Click your username (top right) → "Change password"
3. Enter current password and set a new secure password
4. Save changes

## Important Notes

### Database (SQLite) Limitations ⚠️

**IMPORTANT:** This deployment uses SQLite on Render's ephemeral filesystem:
- **Database resets** when the service restarts or redeploys
- **All data is lost** (users, posts, etc.) on restart
- **Suitable for:** Testing, demos, proof of concept
- **Not suitable for:** Production with real user data

**For production with persistent data:**
- Use PostgreSQL (see Alternative Setup section below)
- Or use a managed database service (AWS RDS, Supabase, etc.)

### Free Tier Limitations

Render's free tier has some limitations:
- Services spin down after 15 minutes of inactivity
- First request after inactivity may take 30-60 seconds (cold start)
- Consider upgrading to paid plans for production use

### Static Files

Static files are served using WhiteNoise, which is already configured in `settings.py`. Your CSS, JavaScript, and images will be automatically collected and served.

### Media Files (User Uploads)

For production, consider using cloud storage for media files:
- AWS S3
- Cloudinary
- Azure Storage

The current setup stores media files on Render's disk, which is ephemeral on the free tier.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Django secret key | Auto-generated |
| `DEBUG` | Yes | Debug mode (False for production) | `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hosts | `your-app.onrender.com` |
| `DATABASE_URL` | No | PostgreSQL connection string (if using PostgreSQL) | `postgresql://user:pass@host/db` |
| `EMAIL_HOST` | No | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_PORT` | No | SMTP server port | `587` |
| `EMAIL_USE_TLS` | No | Use TLS for email | `True` |
| `EMAIL_HOST_USER` | No | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | No | Email password | Your app password |
| `DEFAULT_FROM_EMAIL` | No | Default sender email | `KoraQuest <noreply@koraquest.com>` |
| `CORS_ALLOWED_ORIGINS` | No | Allowed CORS origins | `https://example.com,https://app.example.com` |

## Troubleshooting

### Build Fails

1. Check the build logs in Render dashboard
2. Ensure all dependencies are in `requirements.txt`
3. Verify `build.sh` has execute permissions (should be set automatically)

### Application Won't Start

1. Check the logs in Render dashboard
2. Verify environment variables are set correctly
3. Check `DATABASE_URL` is properly configured
4. Ensure `ALLOWED_HOSTS` includes your Render domain

### Static Files Not Loading

1. The build script runs `collectstatic` automatically
2. Check that `STATIC_ROOT` is set correctly in `settings.py`
3. Verify WhiteNoise is in `MIDDLEWARE` (already configured)

### Database Connection Issues

1. Verify `DATABASE_URL` environment variable is set
2. Check that the database service is running
3. Ensure your web service has access to the database

### Email Not Sending

1. Verify all email environment variables are set
2. Check that your email provider allows SMTP access
3. For Gmail, ensure you're using an App Password, not your regular password
4. Check the application logs for specific error messages

## Updating Your Application

To deploy updates:

1. Make your changes locally
2. Commit and push to your repository:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```
3. Render will automatically detect the changes and redeploy

## Monitoring

1. **Logs**: View real-time logs in the Render dashboard
2. **Metrics**: Monitor CPU, memory, and bandwidth usage
3. **Alerts**: Set up email alerts for service health

## Scaling

As your application grows:

1. **Upgrade Plans**: Move from free to paid plans for better performance
2. **Database**: Upgrade database plan for more storage and connections
3. **Workers**: Add background workers for Celery tasks (if needed)
4. **CDN**: Use a CDN for static files for better performance

## Security Checklist

- ✅ `DEBUG = False` in production
- ✅ Strong `SECRET_KEY`
- ✅ HTTPS enforced (automatic on Render)
- ✅ CSRF protection enabled
- ✅ Secure cookies in production
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection enabled

## Support

- Render Documentation: https://render.com/docs
- Django Documentation: https://docs.djangoproject.com
- KoraQuest Issues: [Your GitHub Repository Issues]

## Alternative Setup: Using PostgreSQL for Persistent Data

If you need persistent data storage (recommended for production):

### Option A: Add PostgreSQL via render.yaml

1. Add this to your `render.yaml` file:
   ```yaml
   # PostgreSQL Database
   - type: pgsql
     name: koraquest-db
     plan: free
     databaseName: koraquest
     user: koraquest
   ```

2. Add this to the web service envVars in `render.yaml`:
   ```yaml
   - key: DATABASE_URL
     fromDatabase:
       name: koraquest-db
       property: connectionString
   ```

3. Redeploy via Blueprint

### Option B: Create PostgreSQL Manually

1. In Render dashboard: **New** → **PostgreSQL**
2. Name: `koraquest-db`
3. Copy the **Internal Database URL**
4. Add to web service as `DATABASE_URL` environment variable

The application will automatically detect `DATABASE_URL` and use PostgreSQL instead of SQLite.

## Next Steps

1. Set up custom domain (optional)
2. Configure monitoring and alerts
3. Set up automated backups (if using PostgreSQL)
4. Configure cloud storage for media files
5. Set up CI/CD pipeline (optional)

---

**Happy Deploying! 🚀**

