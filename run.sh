# run.sh
# Created for OMR Evaluation System
#!/bin/bash

# OMR System Startup Script
echo "🚀 Starting OMR Evaluation & Scoring System..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )[0-9]+\\.[0-9]+')
required_version="3.8"

if [ "$(printf '%s\\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Error: Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads results logs data

# Set environment variables
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true

# Start Streamlit application
echo "🌐 Starting web application on http://localhost:8501"
echo "📊 Access the OMR System at the URL above"
echo "🛑 Press Ctrl+C to stop the application"

streamlit run app/main.py