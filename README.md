# 🍕 Kaoshan Pizza Management System

> **Final Project for MGIS.330.400-402 - Systems Analysis and Design**  
> **Team Developers**: Hu Junyi, Wang Peiyu, Lv Yinzhen  
> **Instructor**: Dr. Blaine Garfolo

A full-featured restaurant management system designed for Kaoshan Pizza. Built with **Flask**, **Bootstrap 5**, **Chart.js**, and **SQLite**, it enables end-to-end digital management of pizza business operations including sales, inventory, staff, customers, vendors, and financial reports.

---

## 🌟 Features

- 🔐 User Login & Welcome Page  
- 📊 Sales Dashboard with KPIs and Trend Analysis  
- 🧾 Order Management (Create, Update, Filter)  
- 📦 Inventory Monitoring and Low Stock Alerts  
- 🛠️ Item & Product Management with Analytics  
- 🧑‍💼 Customer Profiles, Membership Tiers & Feedback  
- 🧑‍🍳 Staff Management with Performance Charts  
- 🏪 Vendor Records & Food Supplier Integration  
- 💰 Financial Reporting (Revenue, Profit, AR/AP)  
- 🎁 Senior Social Welfare Discounts Report  
- 📥 Data Export to Excel (using SheetJS)  
- 🌍 ngrok Tunnel Support for Public Access  

---

## 🖥️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite + SQLAlchemy ORM
- **Frontend**: HTML5 + Bootstrap 5 + Chart.js
- **Visualization**: Chart.js
- **Export**: SheetJS (JavaScript Excel Export)
- **Deployment**: Localhost or Public Access via ngrok

---

## 🚀 Getting Started

Follow the instructions below based on your operating system.

### 1. Clone the repository

```bash
git clone https://github.com/JackieHuJunyi/System-Analysis-Assignment.git
cd System-Analysis-Assignment
```

---

### 2. Create and activate virtual environment

#### 🔵 macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 🟢 Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> ⚠️ If you get an error about script execution being disabled, run the following:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

#### 🟡 Windows (CMD)

```cmd
python -m venv venv
.venv\Scripts\activate.bat
```

---

### 3. Install required dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Initialize the database (optional)

```bash
flask init-db
flask seed-db
```

---

### 5. Run the application

#### 🔵 macOS / Linux

```bash
export FLASK_ENV=development
python app.py
```

#### 🟢 Windows (PowerShell or CMD)

```powershell
$env:FLASK_ENV="development"
python app.py
```

> The app will be available at `http://localhost:5000`(For details, see Terminal Running on http://XXX.X.X.X:XXXX/ (Press CTRL+C to quit)).

---

### 🔑 Login Credentials

Once the application is running, use the following credentials to log in:

- **Username**: `admin`  
- **Password**: `admin123`

---

## ⚡️ One-Step Quick Start

### For macOS / Linux users

```bash
chmod +x run_app.sh
./run_app.sh
```

### For Windows users

Double-click `run_app.bat`  
or run in CMD / PowerShell:

```cmd
.\run_app.bat
```

---

## 📁 Project Structure

```
System-Analysis-Assignment/
├── app.py
├── db_init.py
├── models.py
├── requirements.txt
├── start_ngrok.py
├── templates/
├── static/
├── blueprints/
└── ...
```

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute for educational or commercial purposes.

---

## 🤝 Contributing

Pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

---

## 📬 Contact

Maintained by [Hu Junyi](https://github.com/JackieHuJunyi).