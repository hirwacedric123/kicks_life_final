# Deploy to Fly.io - Step by Step

Follow these steps to deploy your KicksLife250 app to Fly.io:

## Step 1: Login to Fly.io

```bash
flyctl auth login
```

This will open your browser to authenticate. After logging in, you'll be redirected back.

## Step 2: Initialize Your App

```bash
cd /mnt/data/PROJECTS/Cedric_Personal/kicks_life_final
flyctl launch
```

**When prompted:**
- **App name:** `kickslife250` (or your preferred name)
- **Region:** Choose closest to your users (e.g., `iad` for US East, `ord` for US Central, `lhr` for London)
- **PostgreSQL:** Type `n` (we'll use SQLite for now, or add PostgreSQL later)
- **Redis:** Type `n` (not needed)

This will create your app and may update `fly.toml`.

## Step 3: Generate Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Copy the generated secret key** - you'll need it in the next step.

## Step 4: Set Environment Variables

Set your secrets (replace `your-secret-key-here` with the key from Step 3):

```bash
flyctl secrets set SECRET_KEY="your-secret-key-here"
flyctl secrets set DEBUG="False"
flyctl secrets set ALLOWED_HOSTS="kickslife250.fly.dev,kickslife250.com,www.kickslife250.com"
flyctl secrets set FLY_APP_NAME="kickslife250"
flyctl secrets set CUSTOM_DOMAIN="kickslife250.com"
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

## Step 5: Deploy Your App

```bash
flyctl deploy
```

This will:
- Build your Docker image
- Push it to Fly.io
- Deploy your application

**First deployment may take 5-10 minutes.**

## Step 6: Run Database Migrations

After deployment, run migrations:

```bash
flyctl ssh console -C "python manage.py migrate"
```

## Step 7: Collect Static Files

```bash
flyctl ssh console -C "python manage.py collectstatic --noinput"
```

## Step 8: Create Superuser (Optional)

Create an admin user:

```bash
flyctl ssh console -C "python manage.py createsuperuser"
```

Follow the prompts to create your admin account.

## Step 9: Test Your App

Your app should now be live at:
```
https://kickslife250.fly.dev
```

Open it in your browser:
```bash
flyctl open
```

## Step 10: Set Up Custom Domain (kickslife250.com)

### 10.1: Add SSL Certificates

```bash
flyctl certs add kickslife250.com
flyctl certs add www.kickslife250.com
```

This will provide DNS records to add.

### 10.2: Configure DNS on DreamHost

1. Log in to DreamHost
2. Go to **Domains** → **DNS**
3. Select `kickslife250.com`

**Add CNAME record for www:**
- Type: `CNAME`
- Name: `www`
- Value: `kickslife250.fly.dev` (or the value shown by `flyctl certs show`)
- TTL: `3600`

**Set up redirect for root domain:**
- Go to **Domains** → **Manage Domains**
- Click **Edit** next to `kickslife250.com`
- Enable **Redirect** and set to `www.kickslife250.com`

### 10.3: Verify Certificate

```bash
flyctl certs show www.kickslife250.com
```

Wait for status to show `Issued` (may take a few minutes).

### 10.4: Redeploy

```bash
flyctl deploy
```

## Step 11: Verify Custom Domain

Wait for DNS propagation (can take up to 48 hours, usually much faster), then visit:

```
https://www.kickslife250.com
```

## Troubleshooting

### View Logs
```bash
flyctl logs
```

### Check App Status
```bash
flyctl status
```

### SSH into App
```bash
flyctl ssh console
```

### Redeploy
```bash
flyctl deploy
```

## Next Steps

1. ✅ Your app is deployed!
2. ✅ Test all functionality
3. ✅ Set up custom domain
4. ⬜ Configure email (if needed)
5. ⬜ Set up monitoring

---

**Need help?** Check `FLYIO_DEPLOYMENT.md` for detailed instructions.


