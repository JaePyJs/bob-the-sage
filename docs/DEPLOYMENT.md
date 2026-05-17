# SAGE Deployment Guide

Complete deployment instructions for local development, WSL2, and production web hosting.

## Table of Contents

1. [Local Development](#local-development)
2. [WSL2 Setup (Windows)](#wsl2-setup-windows)
3. [Web Deployment](#web-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/sage.git
cd sage

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running Locally (Two Terminals)

**Terminal 1 - Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit: `http://localhost:3000`

---

## WSL2 Setup (Windows)

### Why WSL2?

SAGE is optimized for Linux environments. WSL2 provides:
- Native Linux performance
- Full Python/Node.js compatibility
- Seamless Windows integration
- Access from Windows browsers

### Installation

**1. Enable WSL2 (PowerShell as Administrator)**
```powershell
wsl --install
# Restart computer
```

**2. Install Ubuntu**
```powershell
wsl --install -d Ubuntu
# Set username and password when prompted
```

**3. Update Ubuntu**
```bash
sudo apt update && sudo apt upgrade -y
```

**4. Install Python 3.11+**
```bash
sudo apt install python3.11 python3.11-venv python3-pip -y
```

**5. Install Node.js 18+**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

### Clone and Setup SAGE in WSL2

```bash
# Navigate to your home directory
cd ~

# Clone repository
git clone https://github.com/yourusername/sage.git
cd sage

# Install Python dependencies
pip3 install -r requirements.txt

# Setup frontend
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
nano .env  # Edit with your API keys
```

### Running SAGE in WSL2

**Option 1: Two Terminals (Recommended)**

Terminal 1 - Backend:
```bash
cd ~/sage
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:
```bash
cd ~/sage/frontend
npm run dev
```

**Option 2: Background Processes**

```bash
cd ~/sage

# Start backend in background
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start frontend in background
cd frontend && npm run dev &

# View logs
tail -f nohup.out
```

### Accessing from Windows

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### WSL2 File Access

**From Windows Explorer:**
```
\\wsl$\Ubuntu\home\yourusername\sage
```

**From WSL2 to Windows:**
```bash
cd /mnt/c/Users/YourWindowsUsername/
```

### Stopping Services

```bash
# Find process IDs
ps aux | grep uvicorn
ps aux | grep node

# Kill processes
kill <PID>

# Or kill all
pkill -f uvicorn
pkill -f node
```

---

## Web Deployment

### Architecture Overview

```
┌─────────────────┐
│   Vercel        │  Frontend (Next.js)
│   (Frontend)    │  - Static hosting
│                 │  - Edge functions
└────────┬────────┘  - Auto SSL
         │
         │ HTTPS
         │
┌────────▼────────┐
│   Railway       │  Backend (FastAPI)
│   (Backend)     │  - Python runtime
│                 │  - Auto scaling
└─────────────────┘  - Environment vars
```

### 1. Backend Deployment (Railway)

**Step 1: Prepare Repository**
```bash
# Ensure .gitignore excludes sensitive files
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# Commit and push
git add .
git commit -m "Prepare for deployment"
git push origin main
```

**Step 2: Deploy to Railway**

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `sage` repository
4. Railway will auto-detect Python project

**Step 3: Configure Environment Variables**

In Railway dashboard, add:
```bash
# Required
SEMANTIC_SCHOLAR_API_KEY=your_s2_key_here
DEEPL_API_KEY=your_deepl_key_here

# CORS (update after frontend deployment)
ALLOWED_ORIGINS_RAW=https://your-frontend.vercel.app,http://localhost:3000

# Rate Limiting
ARXIV_DELAY_SECONDS=3
S2_REQUESTS_PER_SECOND=1
```

**Step 4: Set Start Command**

In Railway Settings → Deploy:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Step 5: Deploy**

Railway will automatically deploy. You'll get a URL like:
```
https://sage-backend-production.up.railway.app
```

### 2. Frontend Deployment (Vercel)

**Step 1: Prepare Frontend**

```bash
cd frontend

# Ensure build works locally
npm run build

# Test production build
npm start
```

**Step 2: Deploy to Vercel**

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project" → "Import Git Repository"
3. Select your `sage` repository
4. **Important**: Set Root Directory to `frontend/`

**Step 3: Configure Environment Variables**

In Vercel dashboard, add:
```bash
NEXT_PUBLIC_API_URL=https://sage-backend-production.up.railway.app
```

**Step 4: Deploy**

Vercel will automatically build and deploy. You'll get a URL like:
```
https://sage-research.vercel.app
```

**Step 5: Update Backend CORS**

Go back to Railway and update `ALLOWED_ORIGINS_RAW`:
```bash
ALLOWED_ORIGINS_RAW=https://sage-research.vercel.app,http://localhost:3000
```

### 3. Custom Domain (Optional)

**Vercel Custom Domain:**
1. Go to Project Settings → Domains
2. Add your domain (e.g., `sage.yourdomain.com`)
3. Update DNS records as instructed
4. SSL certificate auto-provisioned

**Railway Custom Domain:**
1. Go to Project Settings → Domains
2. Add your domain (e.g., `api.yourdomain.com`)
3. Update DNS records as instructed
4. Update Vercel `NEXT_PUBLIC_API_URL` to new domain

---

## Environment Configuration

### Backend (.env)

```bash
# Literature API Keys (obtain your own)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
DEEPL_API_KEY=your_key_here

# CORS Configuration
ALLOWED_ORIGINS_RAW=http://localhost:3000,https://your-frontend.vercel.app

# Rate Limiting
ARXIV_DELAY_SECONDS=5
S2_REQUESTS_PER_SECOND=1
```

### Frontend (.env.local)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production
# NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

### API Keys

**Semantic Scholar API Key:**
1. Visit [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api)
2. Sign up for free API access
3. Copy API key to `.env`

**DeepL API Key (Optional):**
1. Visit [deepl.com/pro-api](https://www.deepl.com/pro-api)
2. Sign up for free tier (500,000 chars/month)
3. Copy API key to `.env`

---

## Troubleshooting

### WSL2 Issues

**Problem: Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Problem: Cannot access from Windows**
```bash
# Ensure binding to 0.0.0.0, not 127.0.0.1
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Problem: Slow file access**
```bash
# Move project to WSL2 filesystem (not /mnt/c/)
cd ~
git clone https://github.com/yourusername/sage.git
```

### Deployment Issues

**Problem: Railway build fails**
```bash
# Check Python version in railway.toml
[build]
builder = "NIXPACKS"

[build.nixpacksPlan]
providers = ["python"]
```

**Problem: Vercel build fails**
```bash
# Ensure root directory is set to frontend/
# Check build logs for missing dependencies
npm install
```

**Problem: CORS errors**
```bash
# Verify ALLOWED_ORIGINS_RAW includes frontend URL
# Check Railway logs for CORS errors
railway logs
```

**Problem: API key errors**
```bash
# Verify environment variables are set in Railway
railway variables

# Test API keys locally
python -c "import os; print(os.getenv('SEMANTIC_SCHOLAR_API_KEY'))"
```

### Performance Issues

**Problem: Slow queries**
```bash
# Check rate limiting settings
# Increase S2_REQUESTS_PER_SECOND if you have paid API
S2_REQUESTS_PER_SECOND=5
```

**Problem: Memory issues**
```bash
# Railway: Upgrade to higher tier
# Or reduce max_papers in queries
```

### Database/State Issues

**Problem: Session not found**
```bash
# SAGE uses in-memory storage
# Sessions expire after inactivity
# Restart backend to clear all sessions
```

---

## Monitoring & Logs

### Railway Logs

```bash
# View live logs
railway logs

# View specific service
railway logs --service backend
```

### Vercel Logs

```bash
# Install Vercel CLI
npm i -g vercel

# View logs
vercel logs
```

### Health Checks

```bash
# Backend health
curl https://your-backend.up.railway.app/health

# Frontend health
curl https://your-frontend.vercel.app
```

---

## Scaling Considerations

### Backend Scaling

**Railway Auto-Scaling:**
- Automatically scales based on traffic
- Configure in Project Settings → Resources
- Monitor usage in dashboard

**Rate Limiting:**
```python
# Adjust in backend/config.py
S2_REQUESTS_PER_SECOND=5  # Paid API tier
ARXIV_DELAY_SECONDS=3     # Faster queries
```

### Frontend Scaling

**Vercel Edge Functions:**
- Automatically distributed globally
- No configuration needed
- Scales to millions of requests

### Database (Future)

For persistent storage:
- Railway PostgreSQL addon
- Supabase (PostgreSQL + Auth)
- MongoDB Atlas

---

## Security Checklist

- [ ] API keys in environment variables (not code)
- [ ] CORS configured with specific origins
- [ ] HTTPS enabled (automatic on Vercel/Railway)
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose sensitive data
- [ ] Dependencies updated regularly
- [ ] Security audit reviewed

---

## Backup & Recovery

### Code Backup

```bash
# GitHub is primary backup
git push origin main

# Create release tags
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

### Environment Variables Backup

```bash
# Export Railway variables
railway variables > railway-vars.txt

# Export Vercel variables (manual backup)
# Copy from Vercel dashboard to secure location
```

### Database Backup (Future)

```bash
# Railway PostgreSQL
railway pg:dump > backup.sql

# Restore
railway pg:restore < backup.sql
```

---

## Cost Estimates

### Free Tier Limits

**Railway:**
- $5 free credit/month
- ~500 hours runtime
- 512MB RAM
- 1GB disk

**Vercel:**
- 100GB bandwidth/month
- Unlimited deployments
- Automatic SSL
- Edge functions included

**Semantic Scholar:**
- 1 request/second
- 5,000 requests/day
- Free tier

### Paid Tier Costs

**Railway Pro ($20/month):**
- 8GB RAM
- 100GB disk
- Priority support

**Vercel Pro ($20/month):**
- 1TB bandwidth
- Advanced analytics
- Team collaboration

**Semantic Scholar Paid:**
- Contact for pricing
- Higher rate limits
- Priority support

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. ✅ Configure environment variables
4. ✅ Test production deployment
5. ✅ Set up custom domain (optional)
6. ✅ Configure monitoring
7. ✅ Document deployment for team

---

**Deployment Status**: Ready for production ✅

For questions or issues, see [GitHub Issues](https://github.com/yourusername/sage/issues)