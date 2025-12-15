# Quick Start: Deploy to Render

This is a quick reference guide to deploy KoraQuest to Render. For detailed instructions, see `DEPLOYMENT.md`.

## Pre-Deployment Checklist

- [x] Updated `settings.py` for production
- [x] Added `gunicorn`, `whitenoise`, and `dj-database-url` to requirements.txt
- [x] Created `build.sh` script
- [x] Created `render.yaml` for automated deployment
- [x] Environment variables documented in `env.example.txt`
- [x] Using SQLite (data will reset on restart - see warning below)

## ⚠️ Important: Database Warning

**This deployment uses SQLite which resets when the service restarts!**
- All data (users, posts, etc.) will be lost on restart/redeploy
- Suitable for testing and demos only
- For production, add PostgreSQL (see DEPLOYMENT.md)

## Fastest Way to Deploy (5 minutes)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://dashboard.render.com
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the repository containing KoraQuest
5. Render will detect `render.yaml` automatically
6. Click **"Apply"**

### Step 3: Set Required Environment Variables
After deployment starts, go to your web service and add:

**REQUIRED:**
- `ALLOWED_HOSTS` = `your-app-name.onrender.com` (your actual Render URL)

**OPTIONAL (but recommended for full functionality):**
- `EMAIL_HOST_USER` = Your Gmail address
- `EMAIL_HOST_PASSWORD` = Your Gmail app password (see below)
- `CORS_ALLOWED_ORIGINS` = Your frontend URLs (comma-separated)

### Step 4: Access Admin Panel
A superuser is automatically created during deployment!

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**Login at:** `https://your-app-name.onrender.com/admin`

**⚠️ IMPORTANT:** Change the password immediately after first login!

## Done! 🎉
Your app is now live at: `https://your-app-name.onrender.com`

For more details on superuser management, see `SUPERUSER_INFO.md`

---

## Gmail Setup (for OTP emails)

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password for "KoraQuest"
4. Use this password as `EMAIL_HOST_PASSWORD`

## Important Notes

- **Free tier**: Service sleeps after 15 minutes of inactivity
- **First request**: May take 30-60 seconds (cold start)
- **Database**: SQLite (resets on restart - data not persistent!)
- **Secret Key**: Generated automatically by Render
- **For persistent data**: Add PostgreSQL (see DEPLOYMENT.md)

## Troubleshooting

**Build fails?**
- Check build logs in Render dashboard
- Verify all packages in requirements.txt are compatible

**App won't start?**
- Check that `ALLOWED_HOSTS` is set correctly
- Review deploy logs for error messages

**Can't access admin?**
- Make sure you created a superuser (Step 4 above)
- Visit: `https://your-app-name.onrender.com/admin`

---

For detailed documentation, see **DEPLOYMENT.md**

