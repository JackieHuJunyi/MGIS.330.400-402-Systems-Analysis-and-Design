#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export FLASK_ENV=development

# Run the application
python app.py
