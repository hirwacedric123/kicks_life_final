# Setting Up Custom Domain on PythonAnywhere (Hacker Plan)

This guide will help you configure a custom domain (e.g., `kickslife250.com`) for your Django application on PythonAnywhere's **Hacker plan** ($5/month).

## Prerequisites

1. ✅ **Hacker plan account** on PythonAnywhere ($5/month) - Custom domains are not available on the free plan
2. ✅ Domain name registered: **`kickslife250.com`** (purchased from DreamHost)
3. ✅ Access to DreamHost control panel for DNS management
4. ✅ Django application already deployed on PythonAnywhere

## Step 1: Configure Custom Domain in PythonAnywhere

1. Log in to your PythonAnywhere account
2. Go to the **Web** tab
3. Scroll down to the **Domains** section
4. Click **Add a new domain**
5. Enter your custom domain (e.g., `kickslife250.com`)
6. Click **Add**
7. PythonAnywhere will show you the IP address to point your domain to (usually something like `23.253.xxx.xxx`)

**Important:** Note down the IP address shown - you'll need it for DNS configuration.

## Step 2: Configure DNS Records at DreamHost

Since your domain `kickslife250.com` is registered with DreamHost, follow these specific steps:

**Important:** PythonAnywhere recommends using CNAME records. Your PythonAnywhere CNAME target is: `webapp-2877410.pythonanywhere.com`

### DreamHost DNS Configuration (Recommended: CNAME Method)

1. **Log in to DreamHost:**
   - Go to https://panel.dreamhost.com
   - Log in with your DreamHost account credentials

2. **Navigate to DNS Management:**
   - Click on **Domains** in the left sidebar
   - Click on **DNS** (or **Manage DNS**)
   - Find and click on `kickslife250.com` in the domain list

3. **Add CNAME Record for www:**
   - Click **Add Record** or **+ Add**
   - **Type:** Select `CNAME`
   - **Name:** Enter `www`
   - **Value:** Enter `webapp-2877410.pythonanywhere.com` (your PythonAnywhere CNAME target)
   - **TTL:** `3600` (or leave default)
   - Click **Add Record**

4. **Add Root Domain Record:**
   
   **Option A: Using ALIAS/ANAME (if DreamHost supports it):**
   - Some DNS providers support ALIAS/ANAME records for root domains
   - Check if DreamHost offers this option
   - If available, use ALIAS pointing to `webapp-2877410.pythonanywhere.com`
   
   **Option B: Using A Record (Standard method):**
   - Click **Add Record** or **+ Add**
   - **Type:** Select `A`
   - **Name:** Leave blank or enter `@` (this represents the root domain)
   - **Value:** Enter the PythonAnywhere IP address shown in Step 1
   - **TTL:** `3600` (or leave default)
   - Click **Add Record**
   
   **Note:** The root domain (@) cannot use CNAME due to DNS standards, so you must use an A record or ALIAS if available.

5. **Remove Conflicting Records (if any):**
   - If there are existing A or CNAME records pointing to DreamHost IPs, you may want to remove or update them
   - Look for any records with DreamHost IP addresses and either delete them or update to PythonAnywhere values

6. **Verify Records:**
   - You should see:
     - `@` (or blank) → A record with PythonAnywhere IP (or ALIAS if available)
     - `www` → CNAME record pointing to `webapp-2877410.pythonanywhere.com`

**Important:** 
- The CNAME target `webapp-2877410.pythonanywhere.com` is specific to your PythonAnywhere account
- DreamHost DNS changes typically propagate within 15 minutes to 4 hours
- You can verify DNS propagation at https://www.whatsmydns.net
- After adding records, PythonAnywhere should detect the CNAME and the warning will disappear

### Alternative: Using A Records Only

If you prefer using A records for both root and www:

   | Type | Name | Value | TTL |
   |------|------|-------|-----|
   | A | @ (or blank) | `YOUR_PYTHONANYWHERE_IP` | 3600 |
   | A | www | `YOUR_PYTHONANYWHERE_IP` | 3600 |

**Note:** Replace `YOUR_PYTHONANYWHERE_IP` with the IP address shown in PythonAnywhere. However, CNAME is preferred by PythonAnywhere as it's more flexible.

### DNS Propagation

- DNS changes can take **15 minutes to 48 hours** to propagate
- You can check DNS propagation using tools like:
  - https://www.whatsmydns.net
  - https://dnschecker.org

## Step 3: Configure Django Settings

Your Django settings are already configured to support custom domains! You just need to set the environment variable.

### In PythonAnywhere Web Tab:

1. Go to the **Web** tab
2. Scroll down to **Environment variables**
3. Add or update the `CUSTOM_DOMAIN` variable:

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `CUSTOM_DOMAIN` | `kickslife250.com` | Your custom domain (without www or protocol) |

   **Important:** 
   - Enter the domain **without** `www` prefix
   - Enter the domain **without** `http://` or `https://`
   - Example: `kickslife250.com` (not `www.kickslife250.com` or `https://kickslife250.com`)

The Django settings will automatically:
- ✅ Add `kickslife250.com` and `www.kickslife250.com` to `ALLOWED_HOSTS`
- ✅ Add both domains to `CSRF_TRUSTED_ORIGINS`
- ✅ Add both domains to `CORS_ALLOWED_ORIGINS`

## Step 4: Set Up SSL Certificate

1. In the **Web** tab, scroll to **Security** section
2. Click the pencil icon next to **HTTPS certificate**
3. Select **Auto-renewed Let's Encrypt certificate**
4. Enter your custom domain: `kickslife250.com`
5. Click **Save**
6. PythonAnywhere will automatically obtain and renew the SSL certificate

**Note:** You may need to wait for DNS propagation before the SSL certificate can be issued.

## Step 5: Reload Web App

1. In the **Web** tab, click the green **Reload** button
2. Wait for the reload to complete (usually takes 10-30 seconds)

## Step 6: Verify Custom Domain

1. Wait for DNS propagation (check with https://www.whatsmydns.net)
2. Visit your custom domain: `https://kickslife250.com`
3. Also test with www: `https://www.kickslife250.com`
4. Verify that:
   - ✅ Site loads correctly
   - ✅ SSL certificate is valid (green padlock in browser)
   - ✅ Static files load
   - ✅ All pages function correctly
   - ✅ Admin panel works: `https://kickslife250.com/admin`

## Troubleshooting

### Domain Not Resolving

1. **Check DNS propagation:**
   - Use https://www.whatsmydns.net to check if DNS has propagated
   - Wait up to 48 hours for full propagation

2. **Verify DNS records:**
   - Ensure A record points to the correct PythonAnywhere IP
   - Check that both root (@) and www records are configured

3. **Check PythonAnywhere domain configuration:**
   - Go to **Web** tab → **Domains** section
   - Verify your domain is listed and active

### SSL Certificate Not Issuing

1. **Wait for DNS propagation:**
   - SSL certificates can only be issued after DNS is fully propagated
   - This can take up to 48 hours

2. **Check domain in PythonAnywhere:**
   - Ensure domain is correctly added in **Web** tab → **Domains**
   - Verify the domain matches exactly (no typos)

3. **Retry SSL certificate:**
   - Delete the existing certificate attempt
   - Wait 24 hours
   - Try again

### Django "DisallowedHost" Error

1. **Check environment variable:**
   - Verify `CUSTOM_DOMAIN` is set in **Web** tab → **Environment variables**
   - Ensure it's set to just the domain (e.g., `kickslife250.com`)

2. **Check ALLOWED_HOSTS:**
   - In PythonAnywhere Bash console, run:
     ```bash
     cd ~/kicks_life_final
     source venv/bin/activate
     python manage.py shell
     ```
   - Then in Python shell:
     ```python
     from django.conf import settings
     print(settings.ALLOWED_HOSTS)
     ```
   - Verify your domain is in the list

3. **Reload web app:**
   - Click **Reload** in the **Web** tab after making changes

### Site Shows PythonAnywhere Default Page

1. **Check domain mapping:**
   - In **Web** tab, ensure your custom domain is mapped to your web app
   - Click on your domain in the **Domains** section
   - Verify it's pointing to the correct web app

### Mixed Content Warnings (HTTP/HTTPS)

1. **Ensure SSL is enabled:**
   - Check that SSL certificate is active in **Web** tab → **Security**

2. **Update CSRF_TRUSTED_ORIGINS:**
   - The settings automatically add HTTPS origins
   - Verify `CUSTOM_DOMAIN` environment variable is set correctly

## Environment Variables Summary

For custom domain setup, ensure these are set in **Web** tab → **Environment variables**:

| Variable | Value | Required |
|----------|-------|----------|
| `SECRET_KEY` | (Your Django secret key) | Yes |
| `DEBUG` | `False` | Yes |
| `PYTHONANYWHERE_USERNAME` | `yourusername` | Yes |
| `CUSTOM_DOMAIN` | `kickslife250.com` | Yes (for custom domain) |

## Complete Configuration Checklist

- [ ] Domain added in PythonAnywhere **Web** tab → **Domains**
- [ ] DNS A records configured at domain registrar
- [ ] DNS propagation verified (using whatsmydns.net)
- [ ] `CUSTOM_DOMAIN` environment variable set in PythonAnywhere
- [ ] SSL certificate requested and active
- [ ] Web app reloaded
- [ ] Custom domain accessible via HTTPS
- [ ] www subdomain accessible via HTTPS
- [ ] All static files loading correctly
- [ ] Admin panel accessible

## Testing Your Setup

After configuration, test these URLs:

1. `https://kickslife250.com` - Should load your site
2. `https://www.kickslife250.com` - Should load your site
3. `https://kickslife250.com/admin` - Should load admin login
4. `https://kickslife250.com/static/css/login.css` - Should load static files

## Additional Notes

- **Both domains work:** Your site will be accessible at both `kickslife250.com` and `www.kickslife250.com`
- **SSL is automatic:** PythonAnywhere automatically renews Let's Encrypt certificates
- **No code changes needed:** The Django settings automatically handle custom domains via the `CUSTOM_DOMAIN` environment variable
- **Keep PythonAnywhere subdomain:** Your site will still work at `yourusername.pythonanywhere.com` as a backup

## DreamHost-Specific Resources

- DreamHost DNS Management: https://help.dreamhost.com/hc/en-us/articles/214694348-Basic-DNS-records
- DreamHost A Record Setup: https://help.dreamhost.com/hc/en-us/articles/360035516812-Adding-custom-DNS-records
- DreamHost Control Panel: https://panel.dreamhost.com

## Support Resources

- PythonAnywhere Custom Domain Help: https://help.pythonanywhere.com/pages/CustomDomains/
- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- DNS Propagation Checker: https://www.whatsmydns.net
- Let's Encrypt Documentation: https://letsencrypt.org/docs/

---

**Your custom domain should now be live! 🎉**

Visit `https://kickslife250.com` to see your site.

