# NayePankh Foundation - Volunteer Management System

A simple Python (Flask) web application to manage volunteer records for NayePankh Foundation.

## Features

- **Store Data in Database** — Volunteer records stored in SQLite database
- **User Interface** — Clean, responsive web-based UI built with HTML/CSS
- **Generate Reports** — Download volunteer data as CSV reports
- **Search and Filter** — Search by name/email/skills, filter by department and city

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3, Flask |
| Database | SQLite |
| Frontend | HTML5, CSS3, Jinja2 Templates |
| Deployment | Gunicorn + Render |

## How to Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py
```

Then open http://localhost:5000 in your browser.

## Project Structure

```
├── app.py               # Main Flask application (routes, database logic)
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── README.md            # Project documentation
├── templates/
│   └── index.html       # Web UI template
└── volunteers.db        # SQLite database (auto-created on first run)
```

## Deployment

This project is configured for one-click deployment on [Render](https://render.com).

## About NayePankh Foundation

NayePankh Foundation is a student-led NGO working towards education, youth empowerment, skill development, social awareness, and community impact initiatives across India.

---

*Built as part of NayePankh Foundation Technical Internship Application.*
