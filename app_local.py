"""
NayePankh Foundation - Volunteer Management System
A simple Python project to manage volunteer records with:
- SQLite Database for data storage
- Web-based User Interface (Flask)
- Search and Filter features
- Report generation (CSV export)

Author: Parash
"""

from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nayepankh_volunteer_system_2026"

DATABASE = "volunteers.db"


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            skills TEXT NOT NULL,
            department TEXT NOT NULL,
            experience TEXT NOT NULL DEFAULT 'Beginner',
            date_registered TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Home page - show all volunteers with optional search/filter."""
    conn = get_db()

    # Get filter/search parameters
    search = request.args.get("search", "").strip()
    dept_filter = request.args.get("department", "").strip()
    city_filter = request.args.get("city", "").strip()

    query = "SELECT * FROM volunteers WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR email LIKE ? OR skills LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if dept_filter:
        query += " AND department = ?"
        params.append(dept_filter)

    if city_filter:
        query += " AND city = ?"
        params.append(city_filter)

    query += " ORDER BY id DESC"
    volunteers = conn.execute(query, params).fetchall()

    # Get unique departments and cities for filter dropdowns
    departments = conn.execute(
        "SELECT DISTINCT department FROM volunteers ORDER BY department"
    ).fetchall()
    cities = conn.execute(
        "SELECT DISTINCT city FROM volunteers ORDER BY city"
    ).fetchall()

    # Stats for the dashboard
    total = conn.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0]
    dept_count = conn.execute(
        "SELECT COUNT(DISTINCT department) FROM volunteers"
    ).fetchone()[0]
    city_count = conn.execute(
        "SELECT COUNT(DISTINCT city) FROM volunteers"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        volunteers=volunteers,
        departments=departments,
        cities=cities,
        search=search,
        dept_filter=dept_filter,
        city_filter=city_filter,
        total=total,
        dept_count=dept_count,
        city_count=city_count,
    )


@app.route("/add", methods=["POST"])
def add_volunteer():
    """Add a new volunteer to the database."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    city = request.form.get("city", "").strip()
    skills = request.form.get("skills", "").strip()
    department = request.form.get("department", "").strip()
    experience = request.form.get("experience", "Beginner").strip()

    # Validation
    if not all([name, email, phone, city, skills, department]):
        flash("All fields are required!", "error")
        return redirect(url_for("index"))

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO volunteers 
               (name, email, phone, city, skills, department, experience, date_registered)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, email, phone, city, skills, department, experience,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        flash(f"Volunteer '{name}' added successfully!", "success")
    except sqlite3.IntegrityError:
        flash(f"A volunteer with email '{email}' already exists!", "error")
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:vol_id>")
def delete_volunteer(vol_id):
    """Delete a volunteer by ID."""
    conn = get_db()
    conn.execute("DELETE FROM volunteers WHERE id = ?", (vol_id,))
    conn.commit()
    conn.close()
    flash("Volunteer removed successfully.", "success")
    return redirect(url_for("index"))


@app.route("/report")
def generate_report():
    """Generate and download a CSV report of all volunteers."""
    conn = get_db()
    volunteers = conn.execute("SELECT * FROM volunteers ORDER BY id").fetchall()
    conn.close()

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Name", "Email", "Phone", "City",
        "Skills", "Department", "Experience", "Date Registered"
    ])
    for v in volunteers:
        writer.writerow([
            v["id"], v["name"], v["email"], v["phone"], v["city"],
            v["skills"], v["department"], v["experience"], v["date_registered"]
        ])

    csv_data = output.getvalue()
    output.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nayepankh_volunteers_report_{timestamp}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ──────────────────────────────────────────────
# Initialize DB on import (works with gunicorn too)
# ──────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
