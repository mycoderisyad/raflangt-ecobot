"""
User Model
Mengelola data pengguna dan role management
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base import DatabaseManager

logger = logging.getLogger(__name__)


class UserModel:
    """User model for database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._admin_phones = self._load_admin_phones()
        self._koordinator_phones = self._load_koordinator_phones()

    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number by removing +, @c.us, and whitespace"""
        if not phone_number:
            return ""

        # Remove @c.us suffix if present
        if "@c.us" in phone_number:
            phone_number = phone_number.replace("@c.us", "")

        # Remove + prefix if present
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]

        # Remove any whitespace
        return phone_number.strip()

    def _load_admin_phones(self) -> List[str]:
        """Load admin phone numbers from environment"""
        admin_phones = os.getenv("ADMIN_PHONE_NUMBERS", "")
        if admin_phones:
            return [
                self._normalize_phone_number(phone)
                for phone in admin_phones.split(",")
                if phone.strip()
            ]
        return []

    def _load_koordinator_phones(self) -> List[str]:
        """Load koordinator phone numbers from environment"""
        koordinator_phones = os.getenv("KOORDINATOR_PHONE_NUMBERS", "")
        if koordinator_phones:
            return [
                self._normalize_phone_number(phone)
                for phone in koordinator_phones.split(",")
                if phone.strip()
            ]
        return []

    def get_user_registration_status(self, phone_number: str) -> str:
        """Get user registration status"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT registration_status FROM users WHERE phone_number = ?",
                    (phone_number,),
                )
                result = cursor.fetchone()
                return result["registration_status"] if result else "new"
        except Exception as e:
            logger.error(f"Error getting registration status: {str(e)}")
            return "new"

    def get_user(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user details by phone number"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    def create_pending_user(self, phone_number: str) -> bool:
        """Create user with registered status (no manual registration needed)"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute(
                    "SELECT phone_number FROM users WHERE phone_number = ?",
                    (phone_number,),
                )
                if cursor.fetchone():
                    return False  # User already exists

                # Determine initial role based on environment configuration
                initial_role = self._determine_initial_role(phone_number)

                # Create new user with registered status
                cursor.execute(
                    """
                    INSERT INTO users (phone_number, role, registration_status, first_seen, last_active) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                    (phone_number, initial_role, "registered"),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def complete_user_registration(
        self, phone_number: str, name: str, address: str
    ) -> bool:
        """Complete user registration with name and address"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Update user with registration info
                cursor.execute(
                    """
                    UPDATE users 
                    SET name = ?, address = ?, registration_status = ?, last_active = CURRENT_TIMESTAMP
                    WHERE phone_number = ?
                """,
                    (name, address, "registered", phone_number),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                else:
                    return False

        except Exception as e:
            logger.error(f"Error completing registration: {str(e)}")
            return False

    def is_user_registered(self, phone_number: str) -> bool:
        """Check if user is fully registered"""
        status = self.get_user_registration_status(phone_number)
        return status == "registered"

    def create_user(self, phone_number: str, name: str = None) -> bool:
        """Create new user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute(
                    "SELECT phone_number FROM users WHERE phone_number = ?",
                    (phone_number,),
                )
                if cursor.fetchone():
                    return False  # User already exists

                # Determine initial role based on environment configuration
                initial_role = self._determine_initial_role(phone_number)

                # Create new user with registered status
                cursor.execute(
                    """
                    INSERT INTO users (phone_number, role, registration_status, first_seen, last_active) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                    (phone_number, initial_role, "registered"),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def create_or_update_user(self, phone_number: str) -> Dict[str, Any]:
        """Create new user or update existing user's last_active"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Check if user exists
                cursor.execute(
                    "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
                )
                user = cursor.fetchone()

                if user:
                    # Update last_active
                    cursor.execute(
                        """
                        UPDATE users 
                        SET last_active = CURRENT_TIMESTAMP 
                        WHERE phone_number = ?
                    """,
                        (phone_number,),
                    )

                    # Get updated user
                    cursor.execute(
                        "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
                    )
                    user = cursor.fetchone()
                else:
                    # Determine initial role based on environment variables
                    initial_role = self._determine_initial_role(phone_number)

                    # Create new user with registered status (no manual registration needed)
                    cursor.execute(
                        """
                        INSERT INTO users (phone_number, role, registration_status, first_seen, last_active) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (phone_number, initial_role, "registered"),
                    )

                    # Get created user
                    cursor.execute(
                        "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
                    )
                    user = cursor.fetchone()

                conn.commit()
                return dict(user) if user else None

        except Exception as e:
            logger.error(f"Error creating/updating user: {str(e)}")
            return None

    def _determine_initial_role(self, phone_number: str) -> str:
        """Determine initial role based on environment configuration"""
        normalized_phone = self._normalize_phone_number(phone_number)
        if normalized_phone in self._admin_phones:
            return "admin"
        elif normalized_phone in self._koordinator_phones:
            return "koordinator"
        else:
            return "warga"

    def increment_user_stats(self, phone_number: str, stat_type: str):
        """Increment user statistics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if stat_type == "message":
                    cursor.execute(
                        """
                        UPDATE users 
                        SET total_messages = total_messages + 1,
                            last_active = CURRENT_TIMESTAMP
                        WHERE phone_number = ?
                    """,
                        (phone_number,),
                    )
                elif stat_type == "image":
                    cursor.execute(
                        """
                        UPDATE users 
                        SET total_images = total_images + 1,
                            last_active = CURRENT_TIMESTAMP
                        WHERE phone_number = ?
                    """,
                        (phone_number,),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")

    def get_user_stats(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user statistics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE phone_number = ?", (phone_number,)
                )
                user = cursor.fetchone()
                return dict(user) if user else None

        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return None

    def get_user_role(self, phone_number: str) -> str:
        """Get user role"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role FROM users WHERE phone_number = ?", (phone_number,)
                )
                result = cursor.fetchone()
                return (
                    result["role"]
                    if result
                    else self._determine_initial_role(phone_number)
                )

        except Exception as e:
            logger.error(f"Error getting user role: {str(e)}")
            return self._determine_initial_role(phone_number)

    def update_user_role(
        self, phone_number: str, role: str, admin_phone: str = None
    ) -> bool:
        """Update user role (with permission check)"""
        try:
            # Check if admin_phone has permission to change roles
            if admin_phone and not self.is_admin(admin_phone):
                logger.warning(f"Unauthorized role change attempt by {admin_phone}")
                return False

            valid_roles = ["warga", "koordinator", "admin"]
            if role not in valid_roles:
                logger.error(f"Invalid role: {role}")
                return False

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Ensure user exists first
                self.create_or_update_user(phone_number)

                cursor.execute(
                    """
                    UPDATE users 
                    SET role = ? 
                    WHERE phone_number = ?
                """,
                    (role, phone_number),
                )

                conn.commit()

                # Log the role change
                if admin_phone:
                    self._log_role_change(admin_phone, phone_number, role)

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            return False

    def add_user_points(self, phone_number: str, points: int) -> bool:
        """Add points to user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users 
                    SET points = points + ? 
                    WHERE phone_number = ?
                """,
                    (points, phone_number),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error adding user points: {str(e)}")
            return False

    def is_admin(self, phone_number: str) -> bool:
        """Check if user is admin"""
        role = self.get_user_role(phone_number)
        return role == "admin"

    def is_koordinator_or_admin(self, phone_number: str) -> bool:
        """Check if user is koordinator or admin"""
        role = self.get_user_role(phone_number)
        return role in ["koordinator", "admin"]

    def get_all_users(self, admin_phone: str = None) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        if admin_phone and not self.is_admin(admin_phone):
            return []

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT phone_number, role, total_messages, total_images, 
                           points, last_active, first_seen, is_active
                    FROM users 
                    ORDER BY first_seen DESC
                """
                )
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []

    def get_users_by_role(
        self, role: str, admin_phone: str = None
    ) -> List[Dict[str, Any]]:
        """Get users by role (admin/koordinator only)"""
        if admin_phone and not self.is_koordinator_or_admin(admin_phone):
            return []

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT phone_number, role, total_messages, total_images, 
                           points, last_active, first_seen, is_active
                    FROM users 
                    WHERE role = ?
                    ORDER BY first_seen DESC
                """,
                    (role,),
                )
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting users by role: {str(e)}")
            return []

    def deactivate_user(self, phone_number: str, admin_phone: str = None) -> bool:
        """Deactivate user (admin only)"""
        if admin_phone and not self.is_admin(admin_phone):
            return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users 
                    SET is_active = 0 
                    WHERE phone_number = ?
                """,
                    (phone_number,),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            return False

    def _log_role_change(self, admin_phone: str, target_phone: str, new_role: str):
        """Log role change for audit"""
        try:
            from .system import SystemLogModel

            log_model = SystemLogModel(self.db)
            log_model.log_event(
                "INFO",
                f"Role changed: {target_phone} -> {new_role}",
                "UserModel",
                admin_phone,
                {"target_phone": target_phone, "new_role": new_role},
            )
        except Exception as e:
            logger.error(f"Error logging role change: {str(e)}")

    def get_user_count_by_role(self) -> Dict[str, int]:
        """Get count of users by role"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT role, COUNT() as count 
                    FROM users 
                    WHERE is_active = 1
                    GROUP BY role
                """
                )
                result = {}
                for row in cursor.fetchall():
                    result[row["role"]] = row["count"]
                return result

        except Exception as e:
            logger.error(f"Error getting user count by role: {str(e)}")
            return {}

    def increment_message_count(self, phone_number: str) -> bool:
        """Increment user message count"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users 
                    SET total_messages = total_messages + 1,
                        last_active = CURRENT_TIMESTAMP
                    WHERE phone_number = ?
                """,
                    (phone_number,),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error incrementing message count: {str(e)}")
            return False

    def increment_image_count(self, phone_number: str) -> bool:
        """Increment user image count"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users 
                    SET total_images = total_images + 1,
                        last_active = CURRENT_TIMESTAMP
                    WHERE phone_number = ?
                """,
                    (phone_number,),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error incrementing image count: {str(e)}")
            return False

    def add_points(self, phone_number: str, points: int) -> bool:
        """Add points to user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users 
                    SET points = points + ? 
                    WHERE phone_number = ?
                """,
                    (points, phone_number),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error adding user points: {str(e)}")
            return False

    # ========== ADMIN CRUD METHODS ==========

    def delete_user(self, phone_number: str) -> bool:
        """Delete user from database"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM users WHERE phone_number = ?", (phone_number,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    def get_user_statistics(self) -> Dict[str, int]:
        """Get comprehensive user statistics for admin"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Total users
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()["total"]

                # Users by role
                cursor.execute(
                    "SELECT role, COUNT(*) as count FROM users GROUP BY role"
                )
                role_counts = {row["role"]: row["count"] for row in cursor.fetchall()}

                # Active users today (based on last_active)
                cursor.execute(
                    """
                    SELECT COUNT(*) as active_today 
                    FROM users 
                    WHERE DATE(last_active) = DATE('now')
                """
                )
                active_today = cursor.fetchone()["active_today"]

                # Total messages and images
                cursor.execute(
                    "SELECT SUM(total_messages) as total_messages, SUM(total_images) as total_images FROM users"
                )
                activity = cursor.fetchone()

                # Get interactions today from user_interactions table
                cursor.execute(
                    """
                    SELECT COUNT(*) as interactions_today 
                    FROM user_interactions 
                    WHERE DATE(created_at) = DATE('now')
                """
                )
                interactions_today = cursor.fetchone()["interactions_today"]

                return {
                    "total_users": total_users,
                    "admin_count": role_counts.get("admin", 0),
                    "koordinator_count": role_counts.get("koordinator", 0),
                    "warga_count": role_counts.get("warga", 0),
                    "active_today": active_today,
                    "total_messages": activity["total_messages"] or 0,
                    "total_images": activity["total_images"] or 0,
                    "interactions_today": interactions_today,
                }

        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {
                "total_users": 0,
                "admin_count": 0,
                "koordinator_count": 0,
                "warga_count": 0,
                "active_today": 0,
                "total_messages": 0,
                "total_images": 0,
                "interactions_today": 0,
            }
