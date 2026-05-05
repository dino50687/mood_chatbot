# Deployment Guide for AMIS — AI Mood Intelligence System

## 🚀 Deploy to Render

### Prerequisites
- GitHub account with this repo pushed
- Render account (https://render.com)
- Environment variables set up on Render

### Step 1: Connect Repository to Render
1. Go to https://render.com
2. Click **New +** → **Web Service**
3. Select **Deploy existing repository**
4. Search for `dino50687/mood_chatbot` and connect
5. Click **Connect**

### Step 2: Configure Service
- **Name**: `amis-mood-chatbot` (or your preferred name)
- **Runtime**: Python 3.9
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Free (or upgrade as needed)

### Step 3: Add Environment Variables
In Render dashboard, add these under **Environment**:

```
FLASK_ENV=production
PORT=10000
GROQ_API_KEY=your_groq_api_key_here  (optional)
NVIDIA_API_KEY=your_nvidia_api_key_here  (optional)
NVIDIA_API_KEY_2=your_nvidia_api_key_2_here  (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id  (optional)
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret  (optional)
SPOTIFY_REDIRECT_URI=https://your-render-url.onrender.com/spotify_callback
```

**Note**: 
- LLM API keys (Groq, NVIDIA) are optional—app works with fallback responses
- Spotify integration is optional—app provides default playlists
- Get free API keys from:
  - Groq: https://console.groq.com
  - NVIDIA: https://build.nvidia.com
  - Spotify: https://developer.spotify.com/dashboard

### Step 4: Database Setup
The app uses SQLite which runs on the ephemeral file system on Render's free tier:
- **Warning**: Database resets when service restarts
- **For production**: Upgrade to a paid plan and add PostgreSQL service

To use PostgreSQL on Render:
1. Add a PostgreSQL database service
2. Update `app.py` to use the Render PostgreSQL connection string

### Step 5: Deploy
- Click **Create Web Service**
- Render automatically deploys on every push to `main` branch
- View logs in Render dashboard

### Step 6: Access Your App
Once deployment succeeds:
```
https://your-render-url.onrender.com
```

## 🔗 Render.yaml Alternative
Instead of manual configuration, Render can read `render.yaml`:
1. Push the repo with `render.yaml` included
2. Render auto-detects and uses the config

## 🐛 Troubleshooting

### Build Fails
- Check build logs: Render dashboard → Logs
- Ensure `requirements.txt` has all dependencies
- Verify Python version compatibility

### App Won't Start
- Check start command logs
- Ensure `gunicorn` is in requirements
- Port should be `10000` on Render's free tier

### Database Errors
- Free tier uses ephemeral storage (data lost on restart)
- Upgrade to paid plan + add PostgreSQL for persistent data

### Environment Variables Not Loading
- Redeploy after adding env vars: Render dashboard → Manual Deploy

## 📊 Monitoring
- **Logs**: Render dashboard → Logs tab
- **Metrics**: Render dashboard → Metrics tab
- **Alerts**: Set up in Render dashboard

## 🔄 Continuous Deployment
- Auto-deploys on `git push` to `main` branch
- Can be disabled in service settings

## 💾 Database Migration to PostgreSQL (Optional)
For production with persistent data:
```bash
# Render provides PostgreSQL connection string in env var DATABASE_URL
# Update app.py to use it instead of SQLite
import os
db_url = os.environ.get('DATABASE_URL')
# Switch from sqlite3 to psycopg2
```

## 📝 Support
- Render docs: https://render.com/docs
- AMIS repo: https://github.com/dino50687/mood_chatbot
