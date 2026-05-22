# PowerShell startup script for Luxury Stylist Concierge
# Run: powershell -ExecutionPolicy Bypass -File startup.ps1

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "🎨 LUXURY STYLIST CONCIERGE - Startup Script" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔍 Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion) {
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Installation Steps:" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install dependencies
Write-Host "1️⃣  Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Install Playwright
Write-Host "2️⃣  Installing Playwright browsers..." -ForegroundColor Yellow
playwright install chromium
Write-Host "✅ Playwright ready" -ForegroundColor Green
Write-Host ""

# Step 3: Check catalog
Write-Host "3️⃣  Checking for catalog..." -ForegroundColor Yellow
if (Test-Path "data/catalog.json") {
    Write-Host "✅ Catalog exists (data/catalog.json)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Catalog not found. You need to run the scraper first:" -ForegroundColor Yellow
    Write-Host "   cd scrapers && python run_scrapers.py && cd .." -ForegroundColor White
}
Write-Host ""

# Step 4: Check embeddings
Write-Host "4️⃣  Checking for embeddings..." -ForegroundColor Yellow
if (Test-Path "chromadb_data") {
    Write-Host "✅ Embeddings exist (ChromaDB)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Embeddings not found. You need to embed the catalog:" -ForegroundColor Yellow
    Write-Host "   python -c `"from rag.embedder import EmbedderService; EmbedderService().embed_catalog()`"" -ForegroundColor White
}
Write-Host ""

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "🚀 READY TO RUN!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📌 To run the application, use these commands in separate terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 (FastAPI Server):" -ForegroundColor White
Write-Host "  python api/main.py" -ForegroundColor Green
Write-Host ""
Write-Host "Terminal 2 (Streamlit UI):" -ForegroundColor White
Write-Host "  streamlit run ui/app.py" -ForegroundColor Green
Write-Host ""
Write-Host "Then open your browser:" -ForegroundColor White
Write-Host "  http://localhost:8501" -ForegroundColor Green
Write-Host ""

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "📝 First Time Setup (if no catalog):" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Scrape fashion data (2-3 minutes):" -ForegroundColor White
Write-Host "   cd scrapers && python run_scrapers.py && cd .." -ForegroundColor Green
Write-Host ""
Write-Host "2. Embed catalog (1-2 minutes):" -ForegroundColor White
Write-Host "   python -c `"from rag.embedder import EmbedderService; EmbedderService().embed_catalog()`"" -ForegroundColor Green
Write-Host ""
Write-Host "3. Start API:" -ForegroundColor White
Write-Host "   python api/main.py" -ForegroundColor Green
Write-Host ""
Write-Host "4. Start Streamlit UI (new terminal):" -ForegroundColor White
Write-Host "   streamlit run ui/app.py" -ForegroundColor Green
Write-Host ""

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "✨ Happy Styling! 🎨" -ForegroundColor Magenta
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
