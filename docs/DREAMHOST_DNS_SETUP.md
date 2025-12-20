# DreamHost DNS Setup for kickslife250.com

Quick reference guide for configuring `kickslife250.com` DNS records to point to PythonAnywhere.

## Quick Steps

1. **Get PythonAnywhere CNAME Target:**
   - Log in to PythonAnywhere
   - Go to **Web** tab → **Domains** section
   - Add domain `kickslife250.com` if not already added
   - Note the CNAME target shown: `webapp-2877410.pythonanywhere.com`
   - Also note the IP address if needed for root domain (e.g., `23.253.xxx.xxx`)

2. **Configure DNS in DreamHost:**
   - Log in to https://panel.dreamhost.com
   - Go to **Domains** → **DNS**
   - Click on `kickslife250.com`
   - Add these records:

## DNS Records to Add (Recommended: CNAME Method)

| Type | Name | Value | Notes |
|------|------|-------|-------|
| A | (blank or @) | `YOUR_PYTHONANYWHERE_IP` | Root domain (must use A record) |
| CNAME | www | `webapp-2877410.pythonanywhere.com` | www subdomain (CNAME preferred) |

**Important:**
- Replace `YOUR_PYTHONANYWHERE_IP` with the IP address from PythonAnywhere
- Use `webapp-2877410.pythonanywhere.com` as the CNAME target (this is your specific PythonAnywhere webapp)

## Detailed DreamHost Steps

### Step 1: Access DNS Management

1. Log in to DreamHost panel: https://panel.dreamhost.com
2. Click **Domains** in the left sidebar
3. Click **DNS** (or **Manage DNS**)
4. Find `kickslife250.com` in the list and click on it

### Step 2: Add Root Domain A Record

1. Click **Add Record** or the **+** button
2. Fill in:
   - **Type:** `A`
   - **Name:** Leave blank (or enter `@`)
   - **Value:** `23.253.xxx.xxx` (your PythonAnywhere IP from Step 1)
   - **TTL:** `3600` (or leave default)
3. Click **Add Record**

**Note:** Root domain (@) must use A record, not CNAME (DNS standard limitation).

### Step 3: Add www Subdomain CNAME Record

1. Click **Add Record** again
2. Fill in:
   - **Type:** `CNAME`
   - **Name:** `www`
   - **Value:** `webapp-2877410.pythonanywhere.com` (your PythonAnywhere CNAME target)
   - **TTL:** `3600` (or leave default)
3. Click **Add Record**

**Note:** Using CNAME for www is preferred by PythonAnywhere as it's more flexible than A records.

### Step 4: Remove Old Records (if needed)

If there are existing A records pointing to DreamHost IPs:
- You can either delete them or leave them (they won't interfere)
- The new PythonAnywhere A records will take precedence

### Step 5: Verify

1. Wait 15 minutes to 4 hours for DNS propagation
2. Check DNS propagation:
   - Root domain: https://www.whatsmydns.net/#A/kickslife250.com
   - www subdomain: https://www.whatsmydns.net/#CNAME/www.kickslife250.com
3. Verify:
   - Root domain A record shows PythonAnywhere IP
   - www CNAME record resolves to `webapp-2877410.pythonanywhere.com`
4. Check PythonAnywhere: The warning about missing CNAME should disappear once DNS propagates

## Common DreamHost Issues

### Can't Find DNS Settings

- Make sure you're logged into the correct DreamHost account
- The domain must be registered/transferred to DreamHost
- Try: **Domains** → **Manage Domains** → Click domain → **DNS** tab

### Records Not Saving

- Clear browser cache and try again
- Make sure you're using the correct IP format (no spaces, just numbers and dots)
- Check that TTL is a valid number (3600 is standard)

### DNS Not Propagating

- DreamHost DNS typically propagates in 15 minutes to 4 hours
- Use https://www.whatsmydns.net to check global propagation
- If it's been more than 24 hours, double-check the IP address is correct

## Next Steps

After DNS is configured:

1. ✅ Set `CUSTOM_DOMAIN=kickslife250.com` in PythonAnywhere environment variables
2. ✅ Request SSL certificate in PythonAnywhere Web tab
3. ✅ Reload your web app
4. ✅ Test: https://kickslife250.com

See `PYTHONANYWHERE_CUSTOM_DOMAIN.md` for complete setup instructions.

