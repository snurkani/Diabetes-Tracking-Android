# Diabetes Tracking System (Python) 🏥

## 🚀 Project Overview
This project is a desktop application developed with Python to assist diabetic patients and doctors. It provides a user-friendly interface for logging health data and includes an automated backend system for critical alerts.

## 🛠️ Technologies Used
* **Language:** Python
* **Database:** SQL / SQLite (`schema.sql`)
* **Modules:** `email_manager` (Automation), `db_manager` (Data Handling)
* **Features:** Scheduled Notifications, Role-Based Login (Doctor/Patient)

## ✨ Key Features
* **Patient Panel:** Allows users to log blood sugar and insulin data.
* **Doctor Panel:** Enables doctors to view patient history remotely.
* **Automated Alerts:** Sends email notifications for critical health values via `email_manager.py`.
* **Secure Login:** Role-based authentication system (`login.py`).

## 📂 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
