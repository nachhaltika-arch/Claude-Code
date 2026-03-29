#!/bin/bash

# KOMPAGNON Backend Setup Script
# Usage: bash setup.sh

set -e

echo "🚀 KOMPAGNON Backend Setup"
echo "=========================="

# Check Python version
echo "Checking Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Copy .env file
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✓ .env already exists"
fi

# Initialize database
echo "Initializing database..."
cd backend
python3 -c "
from database import init_db
from seed_checklists import seed_checklists
init_db()
print('✓ Database initialized')
seed_checklists()
print('✓ Checklists seeded')
"
cd ..

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys:"
echo "   - ANTHROPIC_API_KEY"
echo "   - GOOGLE_PAGESPEED_API_KEY (optional)"
echo "   - SMTP settings (optional)"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Open http://localhost:8000/docs for API documentation"
echo ""
