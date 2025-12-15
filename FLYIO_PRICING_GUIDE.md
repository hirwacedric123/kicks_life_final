# Fly.io Pricing & Payment Guide

This guide explains how Fly.io works, including their pricing model, free tier, and payment system.

## 🎯 How Fly.io Works

Fly.io is a **platform-as-a-service (PaaS)** that runs your applications on virtual machines (VMs) distributed across their global network. Think of it like Heroku, but with more control and better performance.

### Key Concepts:

1. **Apps**: Your Django application
2. **Machines**: Virtual servers that run your app
3. **Regions**: Data centers around the world (US, Europe, Asia, etc.)
4. **Volumes**: Persistent storage for databases/files
5. **Networking**: Automatic SSL, custom domains, load balancing

## 💰 Payment Model: Pay-As-You-Go

Fly.io uses a **pay-as-you-go** billing model. You only pay for what you actually use, billed per second or per hour.

### Important Points:

- ✅ **No upfront costs**
- ✅ **No monthly subscriptions** (unless you want reserved capacity)
- ✅ **Billed monthly** based on actual usage
- ✅ **Pay per second** for compute resources
- ⚠️ **Credit card required** (but won't charge if you stay within free tier)

## 🆓 Free Tier (What's Included)

Fly.io offers a **generous free tier** that includes:

### Free Resources:

1. **3 shared-cpu-1x VMs** (virtual machines)
   - 256MB RAM each
   - Can be used for your app, database, or other services
   - **Value**: ~$1.94/month each if running 24/7

2. **3GB Persistent Volume Storage**
   - For databases or file storage
   - **Value**: ~$0.45/month

3. **160GB Outbound Data Transfer**
   - Data your app sends to users
   - **Value**: ~$3.20/month

4. **10 Free SSL Certificates**
   - For custom domains
   - **Value**: $1/month each (normally)

5. **Unlimited Inbound Data**
   - Data coming into your app (free)

### Free Tier Limitations:

- ⚠️ Machines **auto-sleep** after inactivity (free tier)
- ⚠️ First request after sleep takes a few seconds (cold start)
- ⚠️ Limited to 3 VMs total
- ⚠️ Limited to 3GB storage

## 💵 Pricing Breakdown

### 1. Compute (Virtual Machines)

**Shared CPU Instances:**
- `shared-cpu-1x` (256MB RAM): **$0.0027/hour** ≈ **$1.94/month** (if running 24/7)
- `shared-cpu-2x` (512MB RAM): **$0.0054/hour** ≈ **$3.88/month**
- `shared-cpu-4x` (1GB RAM): **$0.0108/hour** ≈ **$7.76/month**

**Performance Instances:**
- `performance-1x` (2GB RAM): **$0.0135/hour** ≈ **$9.72/month**
- `performance-2x` (4GB RAM): **$0.027/hour** ≈ **$19.44/month**

**Billing:** Per second when machine is running

### 2. Storage (Volumes)

- **$0.15 per GB per month**
- Charged for **provisioned capacity**, not actual usage
- Minimum: 1GB
- Example: 10GB volume = $1.50/month

### 3. Data Transfer (Bandwidth)

**Outbound (Data Leaving Fly.io):**
- North America & Europe: **$0.02 per GB**
- Asia Pacific: **$0.05 per GB**
- Other regions: Varies

**Inbound (Data Coming In):**
- ✅ **FREE** (unlimited)

**Example:** If your app sends 50GB/month:
- Cost: 50GB × $0.02 = **$1.00/month**

### 4. Additional Services

- **SSL Certificates**: 
  - First 10: **FREE**
  - Additional: $0.10/month per certificate
- **Dedicated IPv4**: $2/month (optional)
- **PostgreSQL Database**: Separate pricing (if using Fly Postgres)

## 📊 Real-World Cost Examples

### Example 1: Small Django App (Free Tier)

**Setup:**
- 1 shared-cpu-1x VM for app
- 1 shared-cpu-1x VM for PostgreSQL
- 2GB volume for database
- 10GB/month outbound traffic
- Custom domain with SSL

**Cost Breakdown:**
- Compute: **$0** (within 3 free VMs)
- Storage: **$0** (within 3GB free)
- Bandwidth: **$0** (within 160GB free)
- SSL: **$0** (first 10 free)
- **Total: $0/month** ✅

### Example 2: Medium Traffic App

**Setup:**
- 2 shared-cpu-1x VMs (app + database)
- 5GB volume
- 200GB/month outbound traffic
- Custom domain

**Cost Breakdown:**
- Compute: **$0** (within free tier)
- Storage: 5GB - 3GB free = 2GB × $0.15 = **$0.30/month**
- Bandwidth: 200GB - 160GB free = 40GB × $0.02 = **$0.80/month**
- SSL: **$0** (free)
- **Total: ~$1.10/month** 💰

### Example 3: Production App (Beyond Free Tier)

**Setup:**
- 2 performance-1x VMs (app + database)
- 20GB volume
- 500GB/month outbound traffic

**Cost Breakdown:**
- Compute: 2 × $9.72 = **$19.44/month**
- Storage: 20GB × $0.15 = **$3.00/month**
- Bandwidth: 500GB × $0.02 = **$10.00/month**
- **Total: ~$32.44/month** 💰

## 💳 How Payment Works

### 1. Account Setup

1. **Sign up** at fly.io (free)
2. **Add credit card** (required for billing, but won't charge if you stay free)
3. **Or add credits** (minimum $25) if you don't want to use a card

### 2. Billing Cycle

- **Billed monthly** (at the end of each month)
- **Invoice generated** automatically
- **Charged** to your credit card or deducted from credits

### 3. Usage Tracking

- View usage in **Fly.io dashboard**
- Real-time cost estimates
- Set up **spending alerts** (optional)

### 4. Payment Methods

- ✅ **Credit/Debit Card** (Visa, Mastercard, Amex)
- ✅ **Prepaid Credits** (minimum $25)
- ✅ **Invoicing** (for enterprise accounts)

## 🎯 Free Tier Strategy

### How to Stay Free:

1. **Use shared-cpu-1x VMs** (within 3 free VMs)
2. **Keep storage under 3GB**
3. **Keep bandwidth under 160GB/month**
4. **Use free SSL certificates** (first 10)
5. **Accept cold starts** (machines sleep when inactive)

### When You'll Be Charged:

- ❌ Using more than 3 VMs
- ❌ Using more than 3GB storage
- ❌ Exceeding 160GB outbound bandwidth
- ❌ Using performance VMs (instead of shared-cpu)
- ❌ Using more than 10 SSL certificates

## 📈 Cost Optimization Tips

### 1. Use Auto-Scaling

```bash
# Scale down when not needed
flyctl scale count 1

# Scale up during peak times
flyctl scale count 2
```

### 2. Use Shared-CPU VMs

- Start with `shared-cpu-1x` (free tier)
- Only upgrade if you need more performance

### 3. Monitor Bandwidth

- Optimize images and static files
- Use CDN for static assets (reduces bandwidth)
- Compress responses

### 4. Optimize Storage

- Only provision what you need
- Clean up old files regularly
- Use external storage (S3) for large files

### 5. Use Free SSL

- First 10 certificates are free
- Use subdomains if needed (www, api, etc.)

## 🔔 Spending Alerts

Set up alerts to avoid surprises:

1. Go to **Fly.io Dashboard** → **Billing**
2. Set **spending limits**
3. Get **email notifications** when approaching limits

## 💡 For Your Project (kickslife250.com)

### Estimated Monthly Cost:

**Free Tier Usage:**
- 1 VM for Django app: **FREE**
- 1 VM for PostgreSQL (if using Fly Postgres): **FREE**
- 2GB database storage: **FREE**
- Custom domain SSL: **FREE**
- ~50GB bandwidth (typical for small site): **FREE**

**Total: $0/month** ✅

**If Traffic Grows:**
- 200GB bandwidth: ~$0.80/month
- 5GB storage: ~$0.30/month
- **Total: ~$1.10/month** 💰

## 🆚 Comparison with Other Platforms

| Platform | Free Tier | Custom Domain | Monthly Cost (Small App) |
|----------|-----------|---------------|--------------------------|
| **Fly.io** | ✅ 3 VMs, 3GB, 160GB | ✅ Free | $0-2/month |
| **Render** | ✅ Limited compute | ✅ Free | $0/month |
| **Railway** | ⚠️ $5 credits | ✅ Free | $0-5/month |
| **PythonAnywhere** | ✅ Subdomain only | ❌ $5/month | $5/month |
| **Heroku** | ❌ No free tier | ✅ Free | $5+/month |

## 📝 Important Notes

1. **Credit Card Required**: Fly.io requires a credit card even for free tier (won't charge if you stay free)

2. **Auto-Sleep**: Free tier machines sleep after inactivity (saves money, but causes cold starts)

3. **Per-Second Billing**: You only pay when machines are running

4. **No Hidden Fees**: Transparent pricing, pay only for what you use

5. **Free Tier Generous**: Most small apps can run completely free

## 🎓 Resources

- **Pricing Calculator**: https://fly.io/calculator
- **Official Pricing**: https://fly.io/pricing
- **Billing Docs**: https://fly.io/docs/about/billing
- **Cost Optimization**: https://fly.io/docs/about/pricing/#optimizing-costs

## ✅ Summary

**For your kickslife250.com project:**

- ✅ **Can run completely FREE** on Fly.io free tier
- ✅ **Custom domain support** (free)
- ✅ **SSL certificates** (free)
- ✅ **No credit card charges** if you stay within free limits
- ✅ **Pay-as-you-go** if you exceed free tier
- ✅ **Transparent pricing** - no surprises

**Bottom Line:** Fly.io is an excellent choice for free hosting with custom domain support. You can start free and only pay if your app grows beyond the free tier limits.

---

**Questions?** Check the official Fly.io documentation or their community forum!


