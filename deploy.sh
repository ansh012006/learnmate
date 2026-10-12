#!/bin/bash
set -e
echo "============================================"
echo "  LearnMate AI - Deployment Setup"
echo "============================================"
echo ""

# Check Node.js
echo "[1/5] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install from https://nodejs.org/"
    exit 1
fi
echo "Node.js: $(node --version)"
echo ""

# Install Vercel CLI
echo "[2/5] Installing Vercel CLI..."
npm install -g vercel 2>&1 | tail -3
echo ""

# Deploy frontend to Vercel
echo "[3/5] Deploying frontend to Vercel..."
cd "$(dirname "$0")"
vercel --token "$VERCEL_TOKEN" --prod --yes 2>&1
echo ""

echo "============================================"
echo "  NEXT STEP: Deploy Backend to Render"
echo "============================================"
echo ""
echo "Option A - Blueprint (recommended):"
echo "  1. Push this project to GitHub"
echo "  2. Go to https://dashboard.render.com"
echo "  3. Click 'New +' > 'Blueprint'"
echo "  4. Connect your GitHub repo"
echo "  5. Render will use render.yaml automatically"
echo "  6. Set GROQ_API_KEY in environment"
echo "  7. Click Apply"
echo ""
echo "Option B - Manual:"
echo "  1. Go to https://dashboard.render.com/web/new"
echo "  2. Select 'Build and deploy from a Git repository'"
echo "  3. Connect your repo"
echo "  4. Runtime: Python"
echo "  5. Build: pip install -r requirements.txt"
echo "  6. Start: uvicorn backend.main:app --host 0.0.0.0 --port \$PORT"
echo "  7. Add env: GROQ_API_KEY=your_key"
echo "  8. Deploy"
echo ""
