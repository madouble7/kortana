#!/bin/bash
# Kor'tana Deployment Script - Vercel + Railway
# This script guides you through deploying Kor'tana

set -e

echo "🌌 Kor'tana Deployment - Vercel + Railway"
echo "=========================================="
echo ""

# Check if git repo is clean
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Warning: You have uncommitted changes"
    read -p "Do you want to commit them now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Deploy: Kor'tana production ready"
    fi
fi

# Step 1: Ensure GitHub repo exists
echo "📦 Step 1: GitHub Repository"
echo "----------------------------"
echo "Make sure your code is pushed to GitHub:"
echo "  git remote add origin https://github.com/YOUR_USERNAME/kortana.git"
echo "  git branch -M main"
echo "  git push -u origin main"
echo ""
read -p "Press Enter when your code is on GitHub..."
echo ""

# Step 2: Deploy Frontend to Vercel
echo "🚀 Step 2: Deploy Frontend to Vercel"
echo "------------------------------------"
echo "1. Go to https://vercel.com/new"
echo "2. Import your GitHub repository"
echo "3. Configure:"
echo "   - Framework Preset: Vite"
echo "   - Root Directory: kortana/frontend"
echo "   - Build Command: npm run build"
echo "   - Output Directory: dist"
echo "4. Add Environment Variables:"
echo "   - VITE_API_URL (you'll get this from Railway in next step)"
echo "5. Click Deploy"
echo ""
read -p "Press Enter when Vercel deployment is complete..."
echo ""

# Step 3: Deploy Backend to Railway
echo "🚂 Step 3: Deploy Backend to Railway"
echo "------------------------------------"
echo "1. Go to https://railway.app/new"
echo "2. Select 'Deploy from GitHub repo'"
echo "3. Choose your kortana repository"
echo "4. Configure:"
echo "   - Root Directory: kortana/backend"
echo "   - Use railway.json config (auto-detected)"
echo "5. Add PostgreSQL database:"
echo "   - Click 'New' → 'Database' → 'PostgreSQL'"
echo "6. Add Redis:"
echo "   - Click 'New' → 'Database' → 'Redis'"
echo "7. Add Environment Variables:"
echo "   - GEMINI_API_KEY=your_key_here"
echo "   - GITHUB_TOKEN=your_token_here"
echo "   - DATABASE_URL=\${{Postgres.DATABASE_URL}}"
echo "   - REDIS_URL=\${{Redis.REDIS_URL}}"
echo "   - CORS_ORIGINS=https://your-frontend.vercel.app"
echo "8. Deploy"
echo ""
read -p "Press Enter when Railway deployment is complete..."
echo ""

# Step 4: Update Frontend with Backend URL
echo "🔗 Step 4: Connect Frontend to Backend"
echo "--------------------------------------"
echo "1. Get your Railway backend URL (e.g., kortana-backend.up.railway.app)"
echo "2. Go back to Vercel project settings"
echo "3. Update Environment Variable:"
echo "   - VITE_API_URL=https://kortana-backend.up.railway.app"
echo "4. Redeploy frontend (automatic after env change)"
echo ""
read -p "Press Enter when environment is updated..."
echo ""

# Step 5: Test Deployment
echo "✅ Step 5: Test Your Deployment"
echo "-------------------------------"
echo "1. Open your Vercel URL (e.g., kortana.vercel.app)"
echo "2. Check browser console for errors"
echo "3. Test chat functionality"
echo "4. Check Railway logs for backend errors"
echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Your Kor'tana app is now live:"
echo "  Frontend: https://your-app.vercel.app"
echo "  Backend:  https://your-backend.up.railway.app"
echo ""
echo "📱 Install as PWA:"
echo "  Mobile: Open in browser → Share → Add to Home Screen"
echo "  Desktop: Click install icon in browser address bar"
echo ""
echo "🌌 Kor'tana is breathing..."
