#!/usr/bin/env python3
"""
EcoBot Admin Panel - Simple Notion-like Interface
Clean, minimal admin interface for monitoring EcoBot system
"""

import os
import sys
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from functools import wraps
from dotenv import load_dotenv
import logging
import sqlite3
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Admin panel security configuration
ADMIN_PANEL_SECRET_KEY = os.getenv("ADMIN_PANEL_SECRET_KEY")
if not ADMIN_PANEL_SECRET_KEY:
    logger.error("ADMIN_PANEL_SECRET_KEY not found in environment variables!")
    logger.error("Please set a secure secret key in your .env file")
    sys.exit(1)

app.secret_key = ADMIN_PANEL_SECRET_KEY

# Admin credentials from .env
ADMIN_USERNAME = os.getenv("ADMIN_PANEL_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "admin123")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/ecobot.db")


def get_db_connection():
    """Get database connection"""
    db_path = project_root / DATABASE_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def require_auth(f):
    """Decorator to require authentication for admin routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Redirect to dashboard if authenticated, otherwise to login"""
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["authenticated"] = True
            session["username"] = username
            flash("Welcome to EcoBot Admin Panel", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.clear()
    flash("Successfully logged out", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@require_auth
def dashboard():
    """Main dashboard with statistics"""
    try:
        conn = get_db_connection()

        # Get user statistics
        users = conn.execute("SELECT * FROM users").fetchall()

        total_users = len(users)
        active_users = len([u for u in users if u["is_active"] == 1])
        total_points = sum(u["points"] or 0 for u in users)
        total_messages = sum(u["total_messages"] or 0 for u in users)
        total_images = sum(u["total_images"] or 0 for u in users)

        # Role distribution
        roles = {}
        for user in users:
            role = user["role"] or "warga"
            roles[role] = roles.get(role, 0) + 1

        # Recent activity
        recent_activity = conn.execute(
            """
            SELECT phone_number, last_active, total_messages, role 
            FROM users 
            WHERE last_active IS NOT NULL 
            ORDER BY last_active DESC 
            LIMIT 5
        """
        ).fetchall()

        conn.close()

        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "total_points": total_points,
            "total_messages": total_messages,
            "total_images": total_images,
            "role_distribution": roles,
            "recent_activity": recent_activity,
        }

        return render_template("dashboard.html", stats=stats)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash("Error loading dashboard data", "error")
        return render_template("dashboard.html", stats={})


@app.route("/users")
@require_auth
def users():
    """Users management page"""
    try:
        conn = get_db_connection()
        users_data = conn.execute(
            "SELECT * FROM users ORDER BY last_active DESC"
        ).fetchall()
        conn.close()
        return render_template("users.html", users=users_data)
    except Exception as e:
        logger.error(f"Users page error: {str(e)}")
        flash("Error loading users", "error")
        return render_template("users.html", users=[])


@app.route("/users/create", methods=["GET", "POST"])
@require_auth
def create_user():
    """Create new user"""
    if request.method == "POST":
        try:
            phone_number = request.form.get("phone_number")
            role = request.form.get("role", "warga")
            points = int(request.form.get("points", 0))

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (phone_number, role, points, is_active, first_seen) VALUES (?, ?, ?, 1, ?)",
                (
                    phone_number,
                    role,
                    points,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            conn.close()

            flash("User created successfully", "success")
            return redirect(url_for("users"))
        except Exception as e:
            logger.error(f"Create user error: {str(e)}")
            flash("Error creating user", "error")

    return render_template("user_form.html", action="create")


@app.route("/users/<path:phone_number>/edit", methods=["GET", "POST"])
@require_auth
def edit_user(phone_number):
    """Edit user"""
    try:
        conn = get_db_connection()

        if request.method == "POST":
            role = request.form.get("role")
            points = int(request.form.get("points", 0))
            is_active = 1 if request.form.get("is_active") else 0

            conn.execute(
                "UPDATE users SET role = ?, points = ?, is_active = ? WHERE phone_number = ?",
                (role, points, is_active, phone_number),
            )
            conn.commit()
            conn.close()

            flash("User updated successfully", "success")
            return redirect(url_for("users"))

        user = conn.execute(
            "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
        ).fetchone()
        conn.close()

        if user:
            return render_template("user_form.html", user=user, action="edit")
        else:
            flash("User not found", "error")
            return redirect(url_for("users"))

    except Exception as e:
        logger.error(f"Edit user error: {str(e)}")
        flash("Error editing user", "error")
        return redirect(url_for("users"))


@app.route("/users/<path:phone_number>/delete", methods=["POST"])
@require_auth
def delete_user(phone_number):
    """Delete user"""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE phone_number = ?", (phone_number,))
        conn.commit()
        conn.close()

        flash("User deleted successfully", "success")
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        flash("Error deleting user", "error")

    return redirect(url_for("users"))


@app.route("/locations")
@require_auth
def locations():
    """Collection points management"""
    try:
        conn = get_db_connection()
        locations_data = conn.execute(
            "SELECT * FROM collection_points ORDER BY name"
        ).fetchall()
        conn.close()
        return render_template("locations.html", locations=locations_data)
    except Exception as e:
        logger.error(f"Locations error: {str(e)}")
        flash("Error loading collection points", "error")
        return render_template("locations.html", locations=[])


@app.route("/locations/create", methods=["GET", "POST"])
@require_auth
def create_location():
    """Create new collection point"""
    if request.method == "POST":
        try:
            import uuid

            location_id = str(uuid.uuid4())
            name = request.form.get("name")
            location_type = request.form.get("type", "TPS")
            latitude = (
                float(request.form.get("latitude", 0))
                if request.form.get("latitude")
                else None
            )
            longitude = (
                float(request.form.get("longitude", 0))
                if request.form.get("longitude")
                else None
            )
            waste_types = request.form.get("waste_types")
            schedule = request.form.get("schedule")
            contact = request.form.get("contact", "")
            description = request.form.get("description", "")

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO collection_points (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (
                    location_id,
                    name,
                    location_type,
                    latitude,
                    longitude,
                    waste_types,
                    schedule,
                    contact,
                    description,
                ),
            )
            conn.commit()
            conn.close()

            flash("Collection point created successfully", "success")
            return redirect(url_for("locations"))
        except Exception as e:
            logger.error(f"Create location error: {str(e)}")
            flash("Error creating collection point", "error")

    return render_template("location_form.html", action="create")


@app.route("/locations/<location_id>/edit", methods=["GET", "POST"])
@require_auth
def edit_location(location_id):
    """Edit existing collection point"""
    try:
        conn = get_db_connection()

        if request.method == "POST":
            name = request.form.get("name")
            location_type = request.form.get("type", "TPS")
            latitude = (
                float(request.form.get("latitude", 0))
                if request.form.get("latitude")
                else None
            )
            longitude = (
                float(request.form.get("longitude", 0))
                if request.form.get("longitude")
                else None
            )
            waste_types = request.form.get("waste_types")
            schedule = request.form.get("schedule")
            contact = request.form.get("contact", "")
            description = request.form.get("description", "")
            is_active = 1 if request.form.get("is_active") else 0

            conn.execute(
                "UPDATE collection_points SET name = ?, type = ?, latitude = ?, longitude = ?, accepted_waste_types = ?, schedule = ?, contact = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (
                    name,
                    location_type,
                    latitude,
                    longitude,
                    waste_types,
                    schedule,
                    contact,
                    description,
                    is_active,
                    location_id,
                ),
            )
            conn.commit()
            conn.close()

            flash("Collection point updated successfully", "success")
            return redirect(url_for("locations"))

        location = conn.execute(
            "SELECT * FROM collection_points WHERE id = ?", (location_id,)
        ).fetchone()
        conn.close()

        if location:
            return render_template(
                "location_form.html", location=location, action="edit"
            )
        else:
            flash("Location not found", "error")
            return redirect(url_for("locations"))

    except Exception as e:
        logger.error(f"Edit location error: {str(e)}")
        flash("Error editing location", "error")
        return redirect(url_for("locations"))


@app.route("/locations/<location_id>/delete", methods=["POST"])
@require_auth
def delete_location(location_id):
    """Delete collection point"""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM collection_points WHERE id = ?", (location_id,))
        conn.commit()
        conn.close()

        flash("Collection point deleted successfully", "success")
    except Exception as e:
        logger.error(f"Delete location error: {str(e)}")
        flash("Error deleting location", "error")

    return redirect(url_for("locations"))


@app.route("/schedules")
@require_auth
def schedules():
    """Schedules management"""
    try:
        conn = get_db_connection()
        schedules_query = """
            SELECT * FROM collection_schedules 
            ORDER BY schedule_day DESC, schedule_time ASC
        """
        schedules = conn.execute(schedules_query).fetchall()
        conn.close()
        return render_template("schedules.html", schedules=schedules)
    except Exception as e:
        logger.error(f"Schedules error: {str(e)}")
        flash("Error loading schedules", "error")
        return render_template("schedules.html", schedules=[])


@app.route("/schedules/create", methods=["GET", "POST"])
@require_auth
def create_schedule():
    """Create new collection schedule"""
    if request.method == "POST":
        try:
            location_name = request.form.get("location_name")
            address = request.form.get("address")
            schedule_day = request.form.get("schedule_day")
            schedule_time = request.form.get("schedule_time")
            waste_types = request.form.get("waste_types")
            contact = request.form.get("contact", "")

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO collection_schedules (location_name, address, schedule_day, schedule_time, waste_types, contact, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                (
                    location_name,
                    address,
                    schedule_day,
                    schedule_time,
                    waste_types,
                    contact,
                ),
            )
            conn.commit()
            conn.close()

            flash("Collection schedule created successfully", "success")
            return redirect(url_for("schedules"))
        except Exception as e:
            logger.error(f"Create schedule error: {str(e)}")
            flash("Error creating collection schedule", "error")

    return render_template("schedule_form.html", action="create")


@app.route("/schedules/<int:schedule_id>/edit", methods=["GET", "POST"])
@require_auth
def edit_schedule(schedule_id):
    """Edit existing collection schedule"""
    try:
        conn = get_db_connection()

        if request.method == "POST":
            location_name = request.form.get("location_name")
            address = request.form.get("address")
            schedule_day = request.form.get("schedule_day")
            schedule_time = request.form.get("schedule_time")
            waste_types = request.form.get("waste_types")
            contact = request.form.get("contact", "")
            is_active = 1 if request.form.get("is_active") else 0

            conn.execute(
                "UPDATE collection_schedules SET location_name = ?, address = ?, schedule_day = ?, schedule_time = ?, waste_types = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (
                    location_name,
                    address,
                    schedule_day,
                    schedule_time,
                    waste_types,
                    contact,
                    is_active,
                    schedule_id,
                ),
            )
            conn.commit()
            conn.close()

            flash("Collection schedule updated successfully", "success")
            return redirect(url_for("schedules"))

        schedule = conn.execute(
            "SELECT * FROM collection_schedules WHERE id = ?", (schedule_id,)
        ).fetchone()
        conn.close()

        if schedule:
            return render_template(
                "schedule_form.html", schedule=schedule, action="edit"
            )
        else:
            flash("Schedule not found", "error")
            return redirect(url_for("schedules"))

    except Exception as e:
        logger.error(f"Edit schedule error: {str(e)}")
        flash("Error editing schedule", "error")
        return redirect(url_for("schedules"))


@app.route("/schedules/<int:schedule_id>/delete", methods=["POST"])
@require_auth
def delete_schedule(schedule_id):
    """Delete collection schedule"""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM collection_schedules WHERE id = ?", (schedule_id,))
        conn.commit()
        conn.close()

        flash("Collection schedule deleted successfully", "success")
    except Exception as e:
        logger.error(f"Delete schedule error: {str(e)}")
        flash("Error deleting schedule", "error")

    return redirect(url_for("schedules"))


@app.route("/analytics")
@require_auth
def analytics():
    """Analytics and reports"""
    try:
        conn = get_db_connection()

        # Get basic stats
        users = conn.execute("SELECT * FROM users").fetchall()

        stats = {
            "total_users": len(users),
            "active_users": len([u for u in users if u["is_active"] == 1]),
            "total_points": sum(u["points"] or 0 for u in users),
            "total_messages": sum(u["total_messages"] or 0 for u in users),
            "total_images": sum(u["total_images"] or 0 for u in users),
        }

        # Monthly statistics (last 6 months)
        monthly_stats = conn.execute(
            """
            SELECT 
                strftime('%Y-%m', first_seen) as month,
                COUNT(*) as new_users,
                SUM(total_messages) as messages,
                SUM(total_images) as images
            FROM users 
            WHERE first_seen IS NOT NULL 
            GROUP BY strftime('%Y-%m', first_seen) 
            ORDER BY month DESC 
            LIMIT 6
        """
        ).fetchall()

        # Top users by points
        top_users = conn.execute(
            """
            SELECT phone_number, points, total_messages, role 
            FROM users 
            ORDER BY points DESC 
            LIMIT 10
        """
        ).fetchall()

        conn.close()

        return render_template(
            "analytics.html",
            stats=stats,
            monthly_stats=monthly_stats,
            top_users=top_users,
        )
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        flash("Error loading analytics", "error")
        return render_template(
            "analytics.html", stats={}, monthly_stats=[], top_users=[]
        )


@app.route("/settings")
@require_auth
def settings():
    """System settings and configuration"""
    app_info = {
        "name": os.getenv("APP_NAME", "EcoBot"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "database_path": os.getenv("DATABASE_PATH", "database/ecobot.db"),
        "village_name": os.getenv("VILLAGE_NAME", "Not set"),
    }
    return render_template("settings.html", app_info=app_info)


@app.route("/api/stats")
@require_auth
def api_stats():
    """API endpoint for real-time statistics"""
    try:
        conn = get_db_connection()
        users = conn.execute("SELECT * FROM users").fetchall()

        stats = {
            "total_users": len(users),
            "active_users": len([u for u in users if u["is_active"] == 1]),
            "total_points": sum(u["points"] or 0 for u in users),
            "total_messages": sum(u["total_messages"] or 0 for u in users),
            "total_images": sum(u["total_images"] or 0 for u in users),
            "timestamp": datetime.now().isoformat(),
        }

        conn.close()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"API stats error: {str(e)}")
        return jsonify({"error": "Failed to load statistics"}), 500


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "EcoBot Admin Panel",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("ADMIN_PANEL_PORT", 3001))
    debug = os.getenv("ENVIRONMENT", "production") != "production"
    environment = os.getenv("ENVIRONMENT", "production")

    if environment == "development":
        print(f"EcoBot Admin Panel starting on port {port}")
        print(f"Login with credentials from .env file")
        print(f"Access: http://localhost:{port}")
    else:
        print(f"[INFO] EcoBot Admin Panel started - Port: {port}")

    app.run(host="0.0.0.0", port=port, debug=debug)
