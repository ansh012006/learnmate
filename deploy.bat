@echo off
chcp 65001 >nul
echo ============================================
echo   LearnMate AI - Deployment Setup
echo ============================================
echo.

:: Check Node.js
echo [1/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed. Please install from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found:
node --version
echo.

:: Install Vercel CLI
echo [2/5] Installing Vercel CLI...
npm install -g vercel 2>&1
echo.

:: Login to Vercel
echo [3/5] Logging into Vercel...
echo Please follow the prompts to authenticate with your Vercel token.
vercel login 2>&1 || (
    echo Using Vercel token directly...
    vercel --token %VERCEL_TOKEN% whoami 2>&1
)
echo.

:: Deploy to Vercel
echo [4/5] Deploying frontend to Vercel...
echo.
echo IMPORTANT: When prompted:
echo   - Set project name to: learnmate-ai
echo   - Link to existing project if asked
echo   - Confirm the frontend directory is the project root
echo.
vercel --token %VERCEL_TOKEN% --prod --yes 2>&1
echo.

:: Store the Vercel URL
echo Vercel deployment complete!
echo.
echo ============================================
echo   NEXT STEP: Deploy Backend to Render
echo ============================================
echo.
echo 1. Go to https://dashboard.render.com
echo 2. Click "New +" and select "Blueprint"
echo 3. Connect your GitHub repository containing this project
echo 4. Render will auto-detect render.yaml
echo 5. Set your GROQ_API_KEY in the environment variables
echo 6. Click "Apply" to deploy
echo.
echo OR manually:
echo   1. Go to https://dashboard.render.com/web/new
echo   2. Select "Build and deploy from a Git repository"
echo   3. Connect your repo
echo   4. Runtime: Python
echo   5. Build Command: pip install -r requirements.txt
echo   6. Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
echo   7. Add env var GROQ_API_KEY with your key
echo   8. Deploy
echo.
pause
