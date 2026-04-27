#!/usr/bin/env python3
"""
EcoBot Admin Panel - Simple Notion-like Interface
Clean, minimal admin interface for monitoring EcoBot system
"""

import hmac
import os
import sys
from datetime import datetime, timedelta
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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

# Initialise settings & database pool once
from src.config import init_settings, get_settings
from src.database.connection import init_db, get_db

init_settings()
init_db()

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

# Session security hardening
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("ENVIRONMENT", "development") == "production"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
app.config["SESSION_PERMANENT"] = True

# CSRF protection
app.config["WTF_CSRF_TIME_LIMIT"] = 28800  # 8 hours
csrf = CSRFProtect(app)

# Rate limiter (in-memory; swap storage_uri to Redis in production)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

# Admin credentials from .env
ADMIN_USERNAME = os.getenv("ADMIN_PANEL_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "admin123")


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
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login():
    """Admin login page"""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user_ok = hmac.compare_digest(username.encode(), ADMIN_USERNAME.encode())
        pass_ok = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())

        if user_ok and pass_ok:
            session.permanent = True
            session["authenticated"] = True
            session["username"] = username
            flash("Welcome to EcoBot Admin Panel", "success")
            return redirect(url_for("dashboard"))
        else:
            logger.warning("Failed admin login attempt from %s", request.remote_addr)
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
        with get_db() as db:
            users = db.fetch_all("SELECT * FROM users")

            total_users = len(users)
            active_users = len([u for u in users if u.get("is_active")])
            total_points = sum(u.get("points") or 0 for u in users)
            total_messages = sum(u.get("total_messages") or 0 for u in users)
            total_images = sum(u.get("total_images") or 0 for u in users)

            roles = {}
            for user in users:
                role = user.get("role") or "warga"
                roles[role] = roles.get(role, 0) + 1

            recent_activity = db.fetch_all(
                """SELECT phone_number, last_active, total_messages, role
                   FROM users WHERE last_active IS NOT NULL
                   ORDER BY last_active DESC LIMIT 15"""
            )

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
        with get_db() as db:
            users_data = db.fetch_all("SELECT * FROM users ORDER BY last_active DESC")
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
            username = request.form.get("username", "").strip() or None
            role = request.form.get("role", "warga")
            points = int(request.form.get("points", 0))

            with get_db() as db:
                db.execute(
                    "INSERT INTO users (phone_number, username, role, points, is_active, first_seen) VALUES (%s, %s, %s, %s, TRUE, NOW())",
                    (phone_number, username, role, points),
                )

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
        with get_db() as db:
            if request.method == "POST":
                username = request.form.get("username", "").strip() or None
                role = request.form.get("role")
                points = int(request.form.get("points", 0))
                is_active = bool(request.form.get("is_active"))

                db.execute(
                    "UPDATE users SET username = %s, role = %s, points = %s, is_active = %s WHERE phone_number = %s",
                    (username, role, points, is_active, phone_number),
                )
                flash("User updated successfully", "success")
                return redirect(url_for("users"))

            user = db.fetch_one("SELECT * FROM users WHERE phone_number = %s", (phone_number,))

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
        with get_db() as db:
            db.execute("DELETE FROM users WHERE phone_number = %s", (phone_number,))
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
        with get_db() as db:
            locations_data = db.fetch_all("SELECT * FROM collection_points ORDER BY name")
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

            with get_db() as db:
                db.execute(
                    """INSERT INTO collection_points
                       (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
                    (location_id, name, location_type, latitude, longitude, waste_types, schedule, contact, description),
                )

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
        with get_db() as db:
            if request.method == "POST":
                name = request.form.get("name")
                location_type = request.form.get("type", "TPS")
                latitude = float(request.form.get("latitude", 0)) if request.form.get("latitude") else None
                longitude = float(request.form.get("longitude", 0)) if request.form.get("longitude") else None
                waste_types = request.form.get("waste_types")
                schedule = request.form.get("schedule")
                contact = request.form.get("contact", "")
                description = request.form.get("description", "")
                is_active = bool(request.form.get("is_active"))

                db.execute(
                    """UPDATE collection_points
                       SET name=%s, type=%s, latitude=%s, longitude=%s,
                           accepted_waste_types=%s, schedule=%s, contact=%s,
                           description=%s, is_active=%s, updated_at=NOW()
                       WHERE id=%s""",
                    (name, location_type, latitude, longitude, waste_types, schedule, contact, description, is_active, location_id),
                )
                flash("Collection point updated successfully", "success")
                return redirect(url_for("locations"))

            location = db.fetch_one("SELECT * FROM collection_points WHERE id = %s", (location_id,))

        if location:
            return render_template("location_form.html", location=location, action="edit")
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
        with get_db() as db:
            db.execute("DELETE FROM collection_points WHERE id = %s", (location_id,))
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
        with get_db() as db:
            rows = db.fetch_all(
                """SELECT * FROM collection_schedules
                   ORDER BY
                       CASE schedule_day
                           WHEN 'Senin' THEN 1 WHEN 'Selasa' THEN 2 WHEN 'Rabu' THEN 3
                           WHEN 'Kamis' THEN 4 WHEN 'Jumat' THEN 5 WHEN 'Sabtu' THEN 6
                           WHEN 'Minggu' THEN 7 ELSE 8
                       END, schedule_time ASC"""
            )

        schedules_list = []
        for row in rows:
            address = row.get("address") or ""
            notes = ""
            if " | Notes: " in address:
                parts = address.split(" | Notes: ", 1)
                address = parts[0]
                notes = parts[1] if len(parts) > 1 else ""
            row_copy = dict(row)
            row_copy["address"] = address
            row_copy["notes"] = notes
            schedules_list.append(row_copy)

        return render_template("schedules.html", schedules=schedules_list)
    except Exception as e:
        logger.error(f"Schedules error: {str(e)}")
        flash("Error loading schedules", "error")
        return render_template("schedules.html", schedules=[])


@app.route("/schedules/debug")
@require_auth
def schedules_debug():
    """Debug schedules data"""
    try:
        with get_db() as db:
            rows = db.fetch_all(
                """SELECT * FROM collection_schedules
                   ORDER BY
                       CASE schedule_day
                           WHEN 'Senin' THEN 1 WHEN 'Selasa' THEN 2 WHEN 'Rabu' THEN 3
                           WHEN 'Kamis' THEN 4 WHEN 'Jumat' THEN 5 WHEN 'Sabtu' THEN 6
                           WHEN 'Minggu' THEN 7 ELSE 8
                       END, schedule_time ASC"""
            )
        return {
            "total_schedules": len(rows),
            "schedules": rows,
            "debug_info": {"sample_schedule": rows[0] if rows else None},
        }
    except Exception as e:
        return {"error": str(e)}


@app.route("/schedules/create", methods=["GET", "POST"])
@require_auth
def create_schedule():
    """Create new collection schedule"""
    if request.method == "POST":
        try:
            location_name = request.form.get("location_name")
            address = request.form.get("address")
            schedule_day = request.form.get("schedule_day")
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            waste_types = request.form.get("waste_types")
            collector = request.form.get("collector", "")
            notes = request.form.get("notes", "")

            # Combine start and end time into schedule_time format
            schedule_time = f"{start_time}-{end_time}"

            # For now, we'll store collector in contact field and notes in address field
            # In the future, we can add these as separate database columns
            contact = collector
            # Combine address and notes for now (since we don't have a separate notes column)
            full_address = address
            if notes:
                full_address = f"{address} | Notes: {notes}"

            with get_db() as db:
                db.execute(
                    """INSERT INTO collection_schedules
                       (location_name, address, schedule_day, schedule_time, waste_types, contact, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, TRUE)""",
                    (location_name, full_address, schedule_day, schedule_time, waste_types, contact),
                )

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
        with get_db() as db:
            if request.method == "POST":
                location_name = request.form.get("location_name")
                address = request.form.get("address")
                schedule_day = request.form.get("schedule_day")
                start_time = request.form.get("start_time")
                end_time = request.form.get("end_time")
                waste_types = request.form.get("waste_types")
                collector = request.form.get("collector", "")
                notes = request.form.get("notes", "")
                is_active = bool(request.form.get("is_active"))

                schedule_time = f"{start_time}-{end_time}"
                contact = collector
                full_address = f"{address} | Notes: {notes}" if notes else address

                db.execute(
                    """UPDATE collection_schedules
                       SET location_name=%s, address=%s, schedule_day=%s, schedule_time=%s,
                           waste_types=%s, contact=%s, is_active=%s, updated_at=NOW()
                       WHERE id=%s""",
                    (location_name, full_address, schedule_day, schedule_time, waste_types, contact, is_active, schedule_id),
                )
                flash("Collection schedule updated successfully", "success")
                return redirect(url_for("schedules"))

            schedule = db.fetch_one("SELECT * FROM collection_schedules WHERE id = %s", (schedule_id,))

        if schedule:
            schedule_time = schedule.get("schedule_time") or ""
            start_time = ""
            end_time = ""
            if "-" in schedule_time:
                parts = schedule_time.split("-")
                if len(parts) == 2:
                    start_time = parts[0].strip()
                    end_time = parts[1].strip()

            address = schedule.get("address") or ""
            notes = ""
            if " | Notes: " in address:
                addr_parts = address.split(" | Notes: ", 1)
                address = addr_parts[0]
                notes = addr_parts[1] if len(addr_parts) > 1 else ""

            schedule_dict = dict(schedule)
            schedule_dict.update({
                "address": address,
                "start_time": start_time,
                "end_time": end_time,
                "collector": schedule.get("contact", ""),
                "notes": notes,
            })

            return render_template("schedule_form.html", schedule=schedule_dict, action="edit")
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
        with get_db() as db:
            db.execute("DELETE FROM collection_schedules WHERE id = %s", (schedule_id,))
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
        with get_db() as db:
            users = db.fetch_all("SELECT * FROM users")

            stats = {
                "total_users": len(users),
                "active_users": len([u for u in users if u.get("is_active")]),
                "total_points": sum(u.get("points") or 0 for u in users),
                "total_messages": sum(u.get("total_messages") or 0 for u in users),
                "total_images": sum(u.get("total_images") or 0 for u in users),
            }

            monthly_stats = db.fetch_all(
                """SELECT TO_CHAR(first_seen, 'YYYY-MM') as month,
                          COUNT(*) as new_users,
                          SUM(total_messages) as messages,
                          SUM(total_images) as images
                   FROM users WHERE first_seen IS NOT NULL
                   GROUP BY TO_CHAR(first_seen, 'YYYY-MM')
                   ORDER BY month DESC LIMIT 12"""
            )

            top_users = db.fetch_all(
                """SELECT phone_number, points, total_messages, role
                   FROM users ORDER BY points DESC LIMIT 10"""
            )

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


@app.route("/broadcast", methods=["GET", "POST"])
@require_auth
def broadcast():
    """Broadcast message to all active users"""
    if request.method == "POST":
        try:
            message_text = request.form.get("message", "").strip()
            target = request.form.get("target", "all")  # all, telegram, whatsapp

            if not message_text or len(message_text) < 5:
                flash("Pesan broadcast minimal 5 karakter", "error")
                return redirect(url_for("broadcast"))

            from src.database.models.user import UserModel
            user_model = UserModel()
            phones = user_model.get_all_active_phones()

            if not phones:
                flash("Tidak ada user aktif", "error")
                return redirect(url_for("broadcast"))

            sent = 0
            cfg_obj = get_settings()

            content = f"\ud83d\udce2 **Pengumuman**\n\n{message_text}"

            if target in ("all", "telegram") and cfg_obj.telegram.enabled:
                from src.channels.telegram import TelegramChannel
                tg = TelegramChannel()
                for phone in phones:
                    if phone.isdigit():
                        if tg.send_message(phone, content):
                            sent += 1

            if target in ("all", "whatsapp") and cfg_obj.whatsapp.enabled:
                from src.channels.whatsapp import WhatsAppChannel
                wa = WhatsAppChannel()
                for phone in phones:
                    if "@" in phone:
                        wa_content = f"\ud83d\udce2 *Pengumuman*\n\n{message_text}"
                        if wa.send_message(phone, wa_content):
                            sent += 1

            flash(f"Broadcast terkirim ke {sent}/{len(phones)} user", "success")
            return redirect(url_for("broadcast"))
        except Exception as e:
            logger.error(f"Broadcast error: {str(e)}")
            flash("Error mengirim broadcast", "error")

    # GET — show form with user count
    try:
        with get_db() as db:
            row = db.fetch_one(
                "SELECT COUNT(*) AS cnt FROM users WHERE is_active = TRUE AND registration_status = 'registered'"
            )
            total_active = row["cnt"] if row else 0
    except Exception:
        total_active = 0

    cfg_obj = get_settings()

    return render_template(
        "broadcast.html",
        total_active=total_active,
        telegram_enabled=cfg_obj.telegram.enabled,
        whatsapp_enabled=cfg_obj.whatsapp.enabled,
    )


@app.route("/settings")
@require_auth
def settings():
    """System settings and configuration"""
    db_url = os.getenv("DATABASE_URL", "")
    db_display = db_url.split("@")[-1] if "@" in db_url else db_url  # hide credentials
    app_info = {
        "name": os.getenv("APP_NAME", "EcoBot"),
        "version": os.getenv("APP_VERSION", "2.0.0"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "database": f"PostgreSQL ({db_display})" if db_display else "Not configured",
        "ai_provider": os.getenv("AI_PROVIDER", "gemini"),
        "village_name": os.getenv("VILLAGE_NAME", "Not set"),
    }
    return render_template("settings.html", app_info=app_info)


@app.route("/api/stats")
@require_auth
def api_stats():
    """API endpoint for real-time statistics"""
    try:
        with get_db() as db:
            users = db.fetch_all("SELECT * FROM users")

        stats = {
            "total_users": len(users),
            "active_users": len([u for u in users if u.get("is_active")]),
            "total_points": sum(u.get("points") or 0 for u in users),
            "total_messages": sum(u.get("total_messages") or 0 for u in users),
            "total_images": sum(u.get("total_images") or 0 for u in users),
            "timestamp": datetime.now().isoformat(),
        }

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
