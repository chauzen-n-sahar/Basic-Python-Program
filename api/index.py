"""
NayePankh Foundation - Volunteer Management System
Vercel Serverless Deployment with Neon PostgreSQL

Author: Parash
"""

import os
import sys
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, Response

# Use absolute path for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Fallback: if templates not found at parent level, try current working directory
if not os.path.isdir(TEMPLATE_DIR):
    TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "nayepankh_volunteer_system_2026")

DATABASE_URL = os.environ.get("DATABASE_URL")

# Try importing psycopg2, fall back to pg8000 if not available
try:
    import psycopg2
    import psycopg2.extras
    DB_DRIVER = "psycopg2"
except ImportError:
    psycopg2 = None
    DB_DRIVER = None

import csv
import io
from datetime import datetime


def get_db():
    """Get a PostgreSQL database connection."""
    if DB_DRIVER == "psycopg2":
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        raise Exception("No PostgreSQL driver available. psycopg2-binary not installed.")


def get_dict_cursor(conn):
    """Get a cursor that returns dict-like rows."""
    if DB_DRIVER == "psycopg2":
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS volunteers (
            id SERIAL PRIMARY KEY,
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
    cur.close()
    conn.close()


# Track whether DB has been initialized
_db_initialized = False


@app.before_request
def ensure_db():
    """Initialize DB on first request."""
    global _db_initialized
    if not _db_initialized and DATABASE_URL:
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            print(f"DB init error: {e}", file=sys.stderr)


# ──────────────────────────────────────────────
# Debug route (remove after deployment works)
# ──────────────────────────────────────────────

@app.route("/debug")
def debug_info():
    """Show debug info to diagnose deployment issues."""
    info = []
    info.append(f"Python: {sys.version}")
    info.append(f"CWD: {os.getcwd()}")
    info.append(f"__file__: {os.path.abspath(__file__)}")
    info.append(f"BASE_DIR: {BASE_DIR}")
    info.append(f"TEMPLATE_DIR: {TEMPLATE_DIR}")
    info.append(f"Template dir exists: {os.path.isdir(TEMPLATE_DIR)}")
    info.append(f"DATABASE_URL set: {bool(DATABASE_URL)}")
    info.append(f"DB_DRIVER: {DB_DRIVER}")

    # List files in template dir
    if os.path.isdir(TEMPLATE_DIR):
        info.append(f"Templates: {os.listdir(TEMPLATE_DIR)}")
    else:
        # Try to find templates
        for root, dirs, files in os.walk(os.getcwd()):
            for f in files:
                if f.endswith('.html'):
                    info.append(f"Found HTML: {os.path.join(root, f)}")

    # Test DB connection
    if DATABASE_URL:
        try:
            conn = get_db()
            conn.close()
            info.append("DB Connection: SUCCESS")
        except Exception as e:
            info.append(f"DB Connection: FAILED - {e}")

    return "<br>".join(info)


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Home page - show all volunteers with optional search/filter."""
    conn = get_db()
    cur = get_dict_cursor(conn)

    # Get filter/search parameters
    search = request.args.get("search", "").strip()
    dept_filter = request.args.get("department", "").strip()
    city_filter = request.args.get("city", "").strip()

    query = "SELECT * FROM volunteers WHERE 1=1"
    params = []

    if search:
        query += " AND (name ILIKE %s OR email ILIKE %s OR skills ILIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if dept_filter:
        query += " AND department = %s"
        params.append(dept_filter)

    if city_filter:
        query += " AND city = %s"
        params.append(city_filter)

    query += " ORDER BY id DESC"
    cur.execute(query, params)
    volunteers = cur.fetchall()

    # Get unique departments and cities for filter dropdowns
    cur.execute("SELECT DISTINCT department FROM volunteers ORDER BY department")
    departments = cur.fetchall()

    cur.execute("SELECT DISTINCT city FROM volunteers ORDER BY city")
    cities = cur.fetchall()

    # Stats for the dashboard
    cur.execute("SELECT COUNT(*) AS count FROM volunteers")
    total = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(DISTINCT department) AS count FROM volunteers")
    dept_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(DISTINCT city) AS count FROM volunteers")
    city_count = cur.fetchone()["count"]

    cur.close()
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
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO volunteers 
               (name, email, phone, city, skills, department, experience, date_registered)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, email, phone, city, skills, department, experience,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        flash(f"Volunteer '{name}' added successfully!", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash(f"A volunteer with email '{email}' already exists!", "error")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:vol_id>")
def delete_volunteer(vol_id):
    """Delete a volunteer by ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM volunteers WHERE id = %s", (vol_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Volunteer removed successfully.", "success")
    return redirect(url_for("index"))


@app.route("/report")
def generate_report():
    """Generate and download a CSV report of all volunteers."""
    conn = get_db()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT * FROM volunteers ORDER BY id")
    volunteers = cur.fetchall()
    cur.close()
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
