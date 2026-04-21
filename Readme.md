# 🎮 QuestLog – Gamified Task Management System

A full-stack **gamified productivity platform** built with Flask.
QuestLog transforms everyday tasks into an RPG-style experience where users complete quests, earn XP, level up, and unlock achievements.

---

## 📌 Overview

QuestLog is a dynamic task management system designed to make productivity engaging and rewarding.

Instead of traditional task lists, users interact with a **progression system** that tracks experience points, levels, and achievements—bringing game mechanics into real-world workflows.

Built with a focus on **backend logic, system design, and user management**, this project demonstrates how gamification can enhance user engagement.

---

## 🚀 Features

* 🎯 **Quest System**

  * Create custom quests with difficulty scaling
  * Random quest generation for variety

* 📈 **Progression Engine**

  * XP-based leveling system
  * Dynamic level calculation

* 🏆 **Achievement System**

  * Automatic trophy unlocking
  * Tracks milestones (XP, levels, completed quests)

* 👤 **Authentication & Security**

  * User registration & login
  * Role-Based Access Control (RBAC)

* 🛠️ **Admin Dashboard**

  * Manage users and quests
  * Monitor platform activity

---

## 🧱 Project Structure

```
QuestLog/
│
├── app.py              # Main app + database models + routes
├── forms.py            # Flask-WTF forms
├── requirements.txt    # Dependencies
├── .env                # Environment variables
│
├── static/             # CSS, JS, assets
├── templates/          # Jinja2 templates
└── instance/           # SQLite database
```

---

## ⚙️ Tech Stack

* **Backend:** Flask (Python)
* **Database:** SQLite (configurable)
* **Frontend:** HTML, CSS, Jinja2
* **Auth:** Flask-Login / JWT concepts
* **Forms:** Flask-WTF

---

## ▶️ Getting Started

### 🔹 Prerequisites

* Python 3.8+
* Git

---

### 🔹 Installation

```bash
git clone https://github.com/Delbani-Ali/Questlog.git
cd Questlog
```

---

### 🔹 Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 🔹 Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 🔹 Environment Setup

Create a `.env` file:

```env
SECRET_KEY=your_random_secret_key
DATABASE_URL=sqlite:///questlog.db
```

---

### 🔹 Initialize Database

```bash
flask init-db
flask create-admin
```

Default admin credentials:

```
Username: admin
Password: changethis
```

---

### 🔹 Run the App

```bash
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

## 🧩 System Breakdown

### 🔹 Quest Management

* Create, update, and track quests
* Difficulty impacts XP rewards

---

### 🔹 Progression Logic

* XP accumulation system
* Level scaling algorithm

---

### 🔹 Achievement Engine

* Event-based tracking
* Automatic milestone detection

---

### 🔹 Admin Suite

* User control
* Quest moderation
* Platform overview

---

## 💡 Future Improvements

* Upgrade to PostgreSQL
* Add real-time features (notifications, updates)
* Enhance gamification (leaderboards, teams)

---

## 🧠 What This Project Shows

* Backend system design (logic-heavy features)
* Implementation of gamification mechanics
* Authentication and role management
* Structured Flask application development
* Ability to build a complete working product

---

## 👤 Author

Ali Delbani

---

## 📄 License

MIT License

---
