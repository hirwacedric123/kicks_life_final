# Next Steps After Fly.io Deployment

Your app has been deployed! Here's what to do next:

## ✅ What's Done

1. ✅ App created: `kickslife250`
2. ✅ Environment variables set
3. ✅ Docker image built and deployed
4. ✅ App URL: https://kickslife250.fly.dev

## 🔄 Next Steps

### Step 1: Test Your App (This Will Wake the Machine)

Visit your app URL:
```
https://kickslife250.fly.dev
```

**Note:** On free tier, the machine sleeps after inactivity. The first request may take 10-30 seconds (cold start).

### Step 2: Run Database Migrations

Once the app is accessible, run migrations:

```bash
export PATH="$HOME/.fly/bin:$PATH"
flyctl ssh console -C "python manage.py migrate"
```

### Step 3: Collect Static Files (If Needed)

```bash
flyctl ssh console -C "python manage.py collectstatic --noinput"
```

### Step 4: Create Superuser (Admin Account)

```bash
flyctl ssh console -C "python manage.py createsuperuser"
```

Follow the prompts to create your admin account.

### Step 5: Test Your App

1. Visit: https://kickslife250.fly.dev
2. Test registration
3. Test login
4. Access admin: https://kickslife250.fly.dev/admin

### Step 6: Set Up Custom Domain (kickslife250.com)

#### 6.1: Add SSL Certificates

```bash
export PATH="$HOME/.fly/bin:$PATH"
flyctl certs add kickslife250.com
flyctl certs add www.kickslife250.com
```

This will show you DNS records to add.

#### 6.2: Configure DNS in DreamHost

1. Log in to DreamHost
2. Go to **Domains** → **DNS**
3. Select `kickslife250.com`

**Add CNAME for www:**
- Type: `CNAME`
- Name: `www`
- Value: `kickslife250.fly.dev` (or what Fly.io shows)
- TTL: `3600`

**Set up redirect for root domain:**
- Go to **Domains** → **Manage Domains**
- Click **Edit** next to `kickslife250.com`
- Enable **Redirect** → `www.kickslife250.com`

#### 6.3: Verify Certificate

```bash
flyctl certs show www.kickslife250.com
```

Wait for status to show `Issued` (may take a few minutes).

#### 6.4: Update ALLOWED_HOSTS (If Needed)

The secrets are already set, but verify:

```bash
flyctl secrets list
```

#### 6.5: Redeploy

```bash
flyctl deploy
```

### Step 7: Verify Custom Domain

Wait for DNS propagation (up to 48 hours, usually faster), then visit:

```
https://www.kickslife250.com
```

## 📊 Useful Commands

### View Logs
```bash
flyctl logs
```

### Check Status
```bash
flyctl status
```

### SSH into App
```bash
flyctl ssh console
```

### Run Django Commands
```bash
flyctl ssh console -C "python manage.py <command>"
```

### View Secrets
```bash
flyctl secrets list
```

### Open App in Browser
```bash
flyctl open
```

## ⚠️ Important Notes

1. **Free Tier Auto-Sleep**: Machines sleep after inactivity. First request after sleep takes 10-30 seconds.

2. **Database**: Currently using SQLite (ephemeral). For production, consider:
   - Fly.io PostgreSQL: `flyctl postgres create`
   - External PostgreSQL database

3. **Static Files**: Already collected during build, but you can re-collect if needed.

4. **Environment Variables**: Already set, but you can add more:
   ```bash
   flyctl secrets set KEY="value"
   ```

## 🎯 Quick Checklist

- [ ] Test app at https://kickslife250.fly.dev
- [ ] Run migrations
- [ ] Create superuser
- [ ] Test registration/login
- [ ] Add SSL certificates for custom domain
- [ ] Configure DNS in DreamHost
- [ ] Wait for DNS propagation
- [ ] Test custom domain

## 🆘 Troubleshooting

### App Not Responding
- Check logs: `flyctl logs`
- Check status: `flyctl status`
- Wait a moment (cold start on free tier)

### Database Errors
- Run migrations: `flyctl ssh console -C "python manage.py migrate"`
- Check if database file exists

### Static Files Not Loading
- Re-collect: `flyctl ssh console -C "python manage.py collectstatic --noinput"`
- Redeploy: `flyctl deploy`

### Custom Domain Not Working
- Wait for DNS propagation (up to 48 hours)
- Check certificate: `flyctl certs show www.kickslife250.com`
- Verify DNS records in DreamHost

---

**Your app is live!** 🎉

Visit: https://kickslife250.fly.dev


