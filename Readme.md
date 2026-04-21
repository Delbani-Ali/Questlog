## 🎮 QuestLog
QuestLog is a professional, gamified task management system built with Flask. It transforms daily productivity into an RPG-style adventure where users complete quests to earn XP, level up, and unlock achievements.
## ✨ Features

* Gamified Progress: Leveling algorithm based on XP accumulation.
* Quest System: Support for custom quests, difficulty scaling, and random quest generation.
* Trophy Room: Automated achievement tracking for milestones like level reached, XP earned, and quests completed.
* Admin Suite: Robust dashboard for managing users, quest content, and platform statistics.
* Secure Auth: Full user authentication system with role-based access control (RBAC).

## 📂 Project Structure

QuestLog/
├── app.py              # Main application logic & Database models
├── forms.py            # Flask-WTF form definitions
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (Secrets)
├── static/             # CSS, JS, and UI assets
├── template/           # HTML templates (Jinja2)
└── instance/           # Local SQLite database

## 🚀 Getting Started## Prerequisites

* Python 3.8 or higher
* Git

## Installation

   1. Clone the Repository
   
   git clone https://github.com/Delbani-Ali/Questlog.git
   cd Questlog
   
   2. Set Up Virtual Environment
   
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   3. Install Dependencies
   
   pip install -r requirements.txt
   
   4. Configuration

    Create a .env file in the root directory:

    SECRET_KEY=your_random_secret_key
    DATABASE_URL=sqlite:///questlog.db

   5. Initialize Database

   Run the custom CLI commands:
   
   flask init-db        # Creates tables and pre-loads trophies
   flask create-admin   # Creates the initial admin user
   
   6. Run the Application
   
   python app.py
   
   The app will be available at http://127.0.0.1:5000.

## 🛠️ Configuration

* To access the admin dashboard, ensure you have logged in with an account where the role is set to admin. Use the flask create-admin command for the initial setup.
Initially it will create the following admin account -> Username : admin | Password : changethis
* Database: Uses SQLite by default (stored in the /instance folder).

## 📝 License
This project is open-source and available under the MIT License.
------------------------------