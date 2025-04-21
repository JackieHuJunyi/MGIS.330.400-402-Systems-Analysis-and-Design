@echo off
REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Set environment variable for Flask
set FLASK_ENV=development

REM Run the application
python app.py
