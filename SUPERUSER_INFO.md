# Default Superuser Information

## 🔐 Automatic Superuser Creation

A default superuser is automatically created during deployment if no superuser exists.

### Default Credentials

**Username:** `admin`  
**Email:** `admin@koraquest.com`  
**Password:** `admin123`

### Admin Login URL

Once your app is deployed, access the admin panel at:

**`https://your-app-name.onrender.com/admin`**

For example:
- `https://koraquest.onrender.com/admin`

---

## ⚠️ IMPORTANT SECURITY NOTE

**🚨 Change the default password immediately after first login!**

### How to Change Password

1. Log in to the admin panel with the default credentials
2. Click on your username in the top right
3. Click "Change password"
4. Enter your current password (`admin123`)
5. Enter and confirm your new secure password
6. Click "Change my password"

---

## 🔧 Custom Superuser Credentials

You can set custom credentials by adding these environment variables in Render:

| Environment Variable | Purpose | Default Value |
|---------------------|---------|---------------|
| `DJANGO_SUPERUSER_USERNAME` | Admin username | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | Admin email | `admin@koraquest.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Admin password | `admin123` |

### To Set Custom Credentials:

1. Go to your Render dashboard
2. Select your web service
3. Click **"Environment"** in the left menu
4. Add the environment variables above with your desired values
5. Click **"Save Changes"**
6. Your service will redeploy with the new credentials

---

## 📝 Notes

- The superuser is only created if **no superuser exists** in the database
- On subsequent deployments, it won't overwrite existing superusers
- With SQLite (ephemeral storage), the superuser will be recreated on each restart
- For persistent superusers, consider upgrading to PostgreSQL

---

## 🆘 Troubleshooting

### "I forgot my admin password"

**For SQLite (current setup):**
- Simply redeploy your app or wait for a restart
- The default superuser will be recreated automatically

**For PostgreSQL (if you upgrade):**
- Add/update the `DJANGO_SUPERUSER_PASSWORD` environment variable
- Delete the existing admin user from the database
- Trigger a new deployment to recreate the superuser

### "Can't access /admin"

1. Make sure your app is fully deployed and running
2. Check the deployment logs for any errors
3. Verify the URL is correct: `https://your-app-name.onrender.com/admin`
4. Try accessing the homepage first to ensure the app is working

---

**Remember:** Always use strong, unique passwords for production deployments! 🔒

