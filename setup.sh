#!/bin/bash

# setup.sh - Setup script for Linux/macOS environments

set -e

echo "================================================"
echo "Setting up Python environment for security audit"
echo "================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Set up environment variables file (create template if not exists)
if [ ! -f ".env" ]; then
    cat > .env.template << 'EOF'
# Environment variables template - Copy to .env and fill in actual values
EXTERNAL_API_KEY="your_api_key_here"
DB_USER="your_db_user_here"
DB_PASS="your_db_password_here"
SERVICE_TOKEN="your_service_token_here"
RSA_PRIVATE_KEY="your_private_key_here"
EOF
    echo "Created .env.template - Copy to .env and fill in actual values"
fi

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Copy .env.template to .env and add your credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: ./run_test.sh"
echo "   or"
echo "4. Run: python auto_test.py"
echo ""
