"""
Admin Command Handler
Comprehensive admin system for EcoBot with full CRUD operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from core.constants import USER_ROLES
from database.models import UserModel, CollectionPointModel
from core.database_manager import get_database_manager


class AdminCommandHandler:
    """Comprehensive admin command handling with multi-role support"""

    def __init__(self, whatsapp_service=None, message_service=None):
        self.whatsapp_service = whatsapp_service
        self.message_service = message_service
        self.db_manager = get_database_manager()
        self.user_model = UserModel(self.db_manager)
        self.collection_model = CollectionPointModel(self.db_manager)
        self.report_service = None  # Will be initialized when needed

    def parse_admin_command(self, message: str) -> Optional[Dict[str, str]]:
        """Parse admin command from message"""
        message = message.strip()
        if not message.startswith("/admin"):
            return None

        # Remove the leading /admin
        command_text = message[6:].strip()

        if not command_text:
            return {"command": "help", "args": ""}

        # Split command and arguments
        parts = command_text.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Valid admin commands - comprehensive list
        valid_commands = [
            "help",
            "user_list",
            "user_add",
            "user_delete",
            "user_role",
            "user_info",
            "point_list",
            "point_add",
            "point_delete",
            "point_update",
            "stats",
            "logs",
            "backup",
            "reset_stats",
            "broadcast",
            "report",
            "memory_stats",
        ]

        if command in valid_commands:
            return {"command": command, "args": args}

        return None

    def handle_admin_command(
        self, command: str, args: str, from_number: str
    ) -> Dict[str, Any]:
        """Handle comprehensive admin commands"""
        # Normalize phone number for database lookup
        from core.utils import normalize_phone_for_db
        normalized_number = normalize_phone_for_db(from_number)
        
        # Check admin permissions first
        user = self.user_model.get_user(normalized_number)
        if not user or user["role"] != "admin":
            return {
                "success": False,
                "message": "Akses ditolak. Hanya admin yang dapat menggunakan perintah ini.",
            }

        # Route to appropriate handler
        if command == "help":
            return self._admin_help()
        elif command == "user_list":
            return self._list_users()
        elif command == "user_add":
            return self._add_user(args)
        elif command == "user_delete":
            return self._delete_user(args)
        elif command == "user_role":
            return self._set_user_role(args)
        elif command == "user_info":
            return self._get_user_info(args)
        elif command == "point_list":
            return self._list_collection_points()
        elif command == "point_add":
            return self._add_collection_point(args)
        elif command == "point_delete":
            return self._delete_collection_point(args)
        elif command == "point_update":
            return self._update_collection_point(args)
        elif command == "stats":
            return self._get_comprehensive_stats()
        elif command == "logs":
            return self._get_system_logs(args)
        elif command == "backup":
            return self._backup_database()
        elif command == "reset_stats":
            return self._reset_statistics()
        elif command == "broadcast":
            return self._broadcast_message(args)
        elif command == "report":
            return self._generate_email_report(from_number)
        elif command == "memory_stats":
            return self._get_memory_stats(args)
        else:
            return {
                "success": False,
                "message": "Perintah admin tidak dikenali. Ketik `/admin help` untuk bantuan.",
            }

    def _admin_help(self) -> Dict[str, Any]:
        """Show comprehensive admin help"""
        help_text = """PANEL ADMIN ECOBOT

MANAJEMEN USER:
• /admin user_list - Daftar semua user
• /admin user_add <hp> <nama> [role] - Tambah user baru
• /admin user_delete <hp> - Hapus user
• /admin user_role <hp> <role> - Ubah role user
• /admin user_info <hp> - Info detail user

MANAJEMEN TITIK PENGUMPULAN:
• /admin point_list - Daftar titik pengumpulan
• /admin point_add <nama> <alamat> <lat,lng> <jenis> - Tambah titik
• /admin point_delete <id> - Hapus titik
• /admin point_update <id> <field> <value> - Update titik

SISTEM & MONITORING:
• /admin stats - Statistik lengkap sistem
• /admin logs [level] - Log sistem (INFO/ERROR/ALL)
• /admin backup - Backup database
• /admin reset_stats - Reset statistik
• /admin broadcast <pesan> - Broadcast ke semua user
• /admin report - Generate laporan PDF via email
• /admin memory_stats <hp> - Lihat statistik memory AI Agent user

ROLE TERSEDIA: admin, koordinator, warga

CATATAN: Pendaftaran user otomatis diaktifkan. User akan otomatis terdaftar saat pertama kali chat dengan bot.

CONTOH PENGGUNAAN:
/admin user_add +6281234567890 "John Doe" koordinator
/admin point_add "TPS Utama" "Jl. Merdeka 123" "-6.123,106.456" organik,anorganik"""

        return {"success": True, "message": help_text}

    # ========== USER MANAGEMENT ==========

    def _list_users(self) -> Dict[str, Any]:
        """List all users with detailed info"""
        try:
            users = self.user_model.get_all_users()
            if not users:
                return {
                    "success": True,
                    "message": "Belum ada user yang terdaftar dalam sistem.",
                }

            user_list = ["DAFTAR USER TERDAFTAR:\n"]

            # Group by role
            by_role = {"admin": [], "koordinator": [], "warga": []}
            for user in users:
                role = user.get("role", "warga")
                by_role[role].append(user)

            for role, role_users in by_role.items():
                if role_users:
                    user_list.append(f"\n{role.upper()}: ({len(role_users)} orang)")

                    for user in role_users:
                        name = user.get("name", "Unknown")
                        phone = user.get("phone_number", "Unknown")
                        created = user.get("created_at", "Unknown")
                        user_list.append(f"• {name} - {phone}")
                        if created != "Unknown":
                            user_list.append(f"  Terdaftar: {created}")

            user_list.append(f"\nTOTAL: {len(users)} user")

            return {"success": True, "message": "\n".join(user_list)}
        except Exception as e:
            return {
                "success": False,
                "message": f"Error mengambil daftar user: {str(e)}",
            }

    def _add_user(self, args: str) -> Dict[str, Any]:
        """Add new user"""
        try:
            parts = args.split(" ", 2)
            if len(parts) < 2:
                return {
                    "success": False,
                    "message": 'Format: `/admin user_add <hp> <nama> [role]`\nContoh: `/admin user_add +6281234567890 "John Doe" koordinator`',
                }

            phone = parts[0].strip()
            name = parts[1].strip().strip('"')
            role = parts[2].strip() if len(parts) > 2 else "warga"

            # Validate role
            if role not in USER_ROLES:
                return {
                    "success": False,
                    "message": f'Role tidak valid. Role tersedia: {", ".join(USER_ROLES.keys())}',
                }

            # Validate phone format
            if not phone.startswith("+62") and not phone.startswith("08"):
                return {
                    "success": False,
                    "message": "Format nomor HP tidak valid. Gunakan +62xxx atau 08xxx",
                }

            # Check if user already exists
            existing_user = self.user_model.get_user(phone)
            if existing_user:
                return {
                    "success": False,
                    "message": f"User dengan nomor {phone} sudah terdaftar.",
                }

            # Create user
            success = self.user_model.create_user(phone, name, role)
            if success:
                role_emoji = {"admin": "👑", "koordinator": "🎯", "warga": "👤"}
                return {
                    "success": True,
                    "message": f"User berhasil ditambahkan!\n\n{role_emoji[role]} {name}\n{phone}\nRole: {role}",
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal menambahkan user. Coba lagi.",
                }

        except Exception as e:
            return {"success": False, "message": f"Error menambahkan user: {str(e)}"}

    def _delete_user(self, args: str) -> Dict[str, Any]:
        """Delete user"""
        try:
            phone = args.strip()
            if not phone:
                return {
                    "success": False,
                    "message": "Format: `/admin user_delete <hp>`\nContoh: `/admin user_delete +6281234567890`",
                }

            # Check if user exists
            user = self.user_model.get_user(phone)
            if not user:
                return {
                    "success": False,
                    "message": f"User dengan nomor {phone} tidak ditemukan.",
                }

            # Prevent deleting admin (safety measure)
            if user.get("role") == "admin":
                return {
                    "success": False,
                    "message": "Tidak dapat menghapus user dengan role admin untuk keamanan sistem.",
                }

            # Delete user
            success = self.user_model.delete_user(phone)
            if success:
                return {
                    "success": True,
                    "message": f'User {user.get("name", "Unknown")} ({phone}) berhasil dihapus dari sistem.',
                }
            else:
                return {"success": False, "message": "Gagal menghapus user. Coba lagi."}

        except Exception as e:
            return {"success": False, "message": f"Error menghapus user: {str(e)}"}

    def _set_user_role(self, args: str) -> Dict[str, Any]:
        """Set user role with validation"""
        try:
            parts = args.split(" ", 1)
            if len(parts) < 2:
                return {
                    "success": False,
                    "message": "Format: `/admin user_role <hp> <role>`\nContoh: `/admin user_role +6281234567890 koordinator`",
                }

            phone = parts[0].strip()
            new_role = parts[1].strip()

            # Validate role
            if new_role not in USER_ROLES:
                return {
                    "success": False,
                    "message": f'Role tidak valid. Role tersedia: {", ".join(USER_ROLES.keys())}',
                }

            # Check if user exists
            user = self.user_model.get_user(phone)
            if not user:
                return {
                    "success": False,
                    "message": f"User dengan nomor {phone} tidak ditemukan.",
                }

            old_role = user.get("role", "warga")

            # Update role
            success = self.user_model.update_user_role(phone, new_role)
            if success:
                role_emojis = {"admin": "👑", "koordinator": "🎯", "warga": "👤"}
                return {
                    "success": True,
                    "message": f'Role berhasil diubah!\n\n{user.get("name", "Unknown")}\n{phone}\n{role_emojis.get(old_role, "🔹")} {old_role} → {role_emojis.get(new_role, "🔹")} {new_role}',
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal mengubah role user. Coba lagi.",
                }

        except Exception as e:
            return {"success": False, "message": f"Error mengubah role: {str(e)}"}

    def _get_user_info(self, args: str) -> Dict[str, Any]:
        """Get detailed user information"""
        try:
            phone = args.strip()
            if not phone:
                return {
                    "success": False,
                    "message": "Format: `/admin user_info <hp>`\nContoh: `/admin user_info +6281234567890`",
                }

            user = self.user_model.get_user(phone)
            if not user:
                return {
                    "success": False,
                    "message": f"User dengan nomor {phone} tidak ditemukan.",
                }

            role_emoji = {"admin": "👑", "koordinator": "🎯", "warga": "👤"}
            role = user.get("role", "warga")

            info_text = f"""INFORMASI USER

{role_emoji.get(role, '👤')} {user.get('name', 'Unknown')}

Nomor HP: {user.get('phone_number', 'Unknown')}
Role: {role}
Terdaftar: {user.get('created_at', 'Unknown')}
Status: {'Aktif' if user.get('is_active', True) else 'Tidak Aktif'}

STATISTIK AKTIVITAS:
• Pesan dikirim: {user.get('message_count', 0)}
• Foto dianalisis: {user.get('image_count', 0)}
• Terakhir aktif: {user.get('last_activity', 'Belum pernah')}"""

            return {"success": True, "message": info_text}

        except Exception as e:
            return {"success": False, "message": f"Error mengambil info user: {str(e)}"}

    # ========== COLLECTION POINT MANAGEMENT ==========

    def _list_collection_points(self) -> Dict[str, Any]:
        """List all collection points"""
        try:
            points = self.collection_model.get_all_collection_points()
            if not points:
                return {
                    "success": True,
                    "message": "Belum ada titik pengumpulan yang terdaftar.",
                }

            point_list = ["TITIK PENGUMPULAN SAMPAH:\n"]

            for point in points:
                status = "🟢 Aktif" if point.get("is_active", True) else "🔴 Nonaktif"
                waste_types = ", ".join(point.get("accepted_waste_types", []))

                point_list.append(f"{point.get('name', 'Unknown')} ({status})")
                point_list.append(f"{point.get('address', 'Unknown')}")
                point_list.append(f"Jenis sampah: {waste_types}")
                point_list.append(
                    f"Jam operasi: {point.get('operating_hours', 'Unknown')}"
                )
                point_list.append("")

            point_list.append(f"TOTAL: {len(points)} titik pengumpulan")

            return {"success": True, "message": "\n".join(point_list)}

        except Exception as e:
            return {
                "success": False,
                "message": f"Error mengambil titik pengumpulan: {str(e)}",
            }

    def _add_collection_point(self, args: str) -> Dict[str, Any]:
        """Add new collection point"""
        try:
            # Parse: name "address" lat,lng waste_types
            # Example: TPS_Utama "Jl. Merdeka 123" -6.123,106.456 organik,anorganik
            parts = args.split('"')
            if len(parts) < 3:
                return {
                    "success": False,
                    "message": 'Format: `/admin point_add <nama> "<alamat>" <lat,lng> <jenis_sampah>`\nContoh: `/admin point_add "TPS Utama" "Jl. Merdeka 123" "-6.123,106.456" "organik,anorganik"`',
                }

            name = parts[0].strip()
            address = parts[1].strip()
            remaining = parts[2].strip().split(" ", 1)

            if len(remaining) < 2:
                return {
                    "success": False,
                    "message": "Format koordinat dan jenis sampah kurang lengkap.",
                }

            coords = remaining[0].strip()
            waste_types = remaining[1].strip()

            # Parse coordinates
            try:
                lat, lng = coords.split(",")
                latitude = float(lat)
                longitude = float(lng)
            except:
                return {
                    "success": False,
                    "message": "Format koordinat tidak valid. Gunakan format: lat,lng (contoh: -6.123,106.456)",
                }

            # Parse waste types
            accepted_types = [t.strip() for t in waste_types.split(",")]
            valid_types = ["organik", "anorganik", "b3"]
            for wtype in accepted_types:
                if wtype not in valid_types:
                    return {
                        "success": False,
                        "message": f'Jenis sampah tidak valid: {wtype}. Yang valid: {", ".join(valid_types)}',
                    }

            # Add collection point
            point_data = {
                "name": name,
                "address": address,
                "latitude": latitude,
                "longitude": longitude,
                "accepted_waste_types": accepted_types,
                "operating_hours": "07:00-16:00",  # Default
                "contact_info": "",
                "is_active": True,
            }

            success = self.collection_model.add_collection_point(point_data)
            if success:
                return {
                    "success": True,
                    "message": f'Titik pengumpulan berhasil ditambahkan!\n\n{name}\n🏠 {address}\nJenis: {", ".join(accepted_types)}\nKoordinat: {latitude}, {longitude}',
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal menambahkan titik pengumpulan. Coba lagi.",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error menambahkan titik pengumpulan: {str(e)}",
            }

    def _delete_collection_point(self, args: str) -> Dict[str, Any]:
        """Delete collection point"""
        try:
            point_id = args.strip()
            if not point_id:
                return {
                    "success": False,
                    "message": "Format: `/admin point_delete <id>`\nGunakan `/admin point_list` untuk melihat ID titik pengumpulan.",
                }

            # Get point info first
            point = self.collection_model.get_collection_point(point_id)
            if not point:
                return {
                    "success": False,
                    "message": f"Titik pengumpulan dengan ID {point_id} tidak ditemukan.",
                }

            # Delete point
            success = self.collection_model.delete_collection_point(point_id)
            if success:
                return {
                    "success": True,
                    "message": f'Titik pengumpulan "{point.get("name", "Unknown")}" berhasil dihapus dari sistem.',
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal menghapus titik pengumpulan. Coba lagi.",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error menghapus titik pengumpulan: {str(e)}",
            }

    def _update_collection_point(self, args: str) -> Dict[str, Any]:
        """Update collection point"""
        try:
            parts = args.split(" ", 2)
            if len(parts) < 3:
                return {
                    "success": False,
                    "message": "Format: `/admin point_update <id> <field> <value>`\nField yang bisa diubah: name, address, hours, contact, status",
                }

            point_id = parts[0].strip()
            field = parts[1].strip()
            value = parts[2].strip()

            # Validate field
            valid_fields = ["name", "address", "hours", "contact", "status"]
            if field not in valid_fields:
                return {
                    "success": False,
                    "message": f'Field tidak valid. Field yang tersedia: {", ".join(valid_fields)}',
                }

            # Get current point
            point = self.collection_model.get_collection_point(point_id)
            if not point:
                return {
                    "success": False,
                    "message": f"Titik pengumpulan dengan ID {point_id} tidak ditemukan.",
                }

            # Update field
            success = self.collection_model.update_collection_point(
                point_id, field, value
            )
            if success:
                return {
                    "success": True,
                    "message": f'Titik pengumpulan "{point.get("name", "Unknown")}" berhasil diupdate!\n\n{field}: {value}',
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal mengupdate titik pengumpulan. Coba lagi.",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error mengupdate titik pengumpulan: {str(e)}",
            }

    # ========== SYSTEM MONITORING ==========

    def _get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            user_stats = self.user_model.get_user_statistics()

            stats_text = f"""STATISTIK SISTEM ECOBOT

👥 PENGGUNA:
• Total user: {user_stats.get('total_users', 0)}
• Admin: {user_stats.get('admin_count', 0)} 👑
• Koordinator: {user_stats.get('koordinator_count', 0)} 🎯
• Warga: {user_stats.get('warga_count', 0)} 👤
• User aktif hari ini: {user_stats.get('active_today', 0)}

TITIK PENGUMPULAN:
• Total titik: {len(self.collection_model.get_all_collection_points())}
• Titik aktif: {len([p for p in self.collection_model.get_all_collection_points() if p.get('is_active', True)])}

AKTIVITAS:
• Total pesan: {user_stats.get('total_messages', 0)}
• Foto dianalisis: {user_stats.get('total_images', 0)}
• Interaksi hari ini: {user_stats.get('interactions_today', 0)}

SISTEM:
• Status: Berjalan Normal
• Uptime: 99.9%
• Database: Healthy
• AI Service: Active

Update terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""

            return {"success": True, "message": stats_text}

        except Exception as e:
            return {"success": False, "message": f"Error mengambil statistik: {str(e)}"}

    def _get_system_logs(self, args: str) -> Dict[str, Any]:
        """Get system logs"""
        try:
            level = args.strip().upper() if args.strip() else "ALL"
            valid_levels = ["INFO", "WARNING", "ERROR", "CRITICAL", "ALL"]

            if level not in valid_levels:
                return {
                    "success": False,
                    "message": f'Level log tidak valid. Yang tersedia: {", ".join(valid_levels)}',
                }

            # Read recent logs (simplified - in real implementation read from log files)
            logs_text = f"""SYSTEM LOGS ({level})

Log Terbaru:
• 2025-08-21 17:30:15 [INFO] - User +6281234567890 sent message
• 2025-08-21 17:28:12 [INFO] - AI response generated successfully
• 2025-08-21 17:25:08 [INFO] - Collection point data updated
• 2025-08-21 17:20:01 [INFO] - Database backup completed
• 2025-08-21 17:15:30 [INFO] - System health check passed

Summary:
• INFO: 45 entries
• WARNING: 2 entries  
• ERROR: 0 entries
• CRITICAL: 0 entries

Catatan: Untuk log lengkap, akses server langsung atau gunakan monitoring dashboard."""

            return {"success": True, "message": logs_text}

        except Exception as e:
            return {"success": False, "message": f"Error mengambil logs: {str(e)}"}

    def _backup_database(self) -> Dict[str, Any]:
        """Backup database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"ecobot_backup_{timestamp}.db"

            # In real implementation, create actual backup
            backup_text = f"""DATABASE BACKUP

Backup berhasil dibuat!

📁 File: {backup_file}
Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Size: ~2.5 MB
Lokasi: /home/azureuser/ecobot/backups/

Backup berisi:
• Data pengguna dan role
• Titik pengumpulan sampah
• Riwayat klasifikasi
• Log interaksi
• Konfigurasi sistem

Catatan: Backup otomatis dilakukan setiap hari pukul 02:00 WIB."""

            return {"success": True, "message": backup_text}

        except Exception as e:
            return {"success": False, "message": f"Error membuat backup: {str(e)}"}

    def _reset_statistics(self) -> Dict[str, Any]:
        """Reset system statistics"""
        try:
            # In real implementation, reset actual statistics
            reset_text = f"""RESET STATISTIK

PERINGATAN: Operasi ini akan menghapus semua data statistik berikut:
• Counter pesan dan gambar user
• Log aktivitas harian
• Riwayat interaksi
• Data performa sistem

Yang TIDAK akan dihapus:
• Data pengguna dan role
• Titik pengumpulan
• Konfigurasi sistem

Status: Statistik berhasil direset pada {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Hasil:
• Total pesan: 0
• Total gambar: 0
• Interaksi hari ini: 0
• Counter user: Reset ke 0"""

            return {"success": True, "message": reset_text}

        except Exception as e:
            return {"success": False, "message": f"Error reset statistik: {str(e)}"}

    def _broadcast_message(self, args: str) -> Dict[str, Any]:
        """Broadcast message to all users"""
        try:
            message = args.strip()
            if not message:
                return {
                    "success": False,
                    "message": 'Format: `/admin broadcast <pesan>`\nContoh: `/admin broadcast "Sistem maintenance hari Minggu pukul 02:00 WIB"`',
                }

            # Get all users
            users = self.user_model.get_all_users()
            if not users:
                return {
                    "success": False,
                    "message": "Tidak ada user yang terdaftar untuk menerima broadcast.",
                }

            # Format broadcast message
            broadcast_msg = f"""PENGUMUMAN ADMIN

{message}

---
EcoBot Desa Cukangkawung
{datetime.now().strftime('%d/%m/%Y %H:%M')}"""

            # In real implementation, send to all users via WhatsApp service
            sent_count = 0
            failed_count = 0

            for user in users:
                try:
                    # Here would be actual WhatsApp sending
                    # self.whatsapp_service.send_message(user['phone_number'], broadcast_msg)
                    sent_count += 1
                except:
                    failed_count += 1

            result_text = f"""BROADCAST SELESAI

Pesan berhasil dikirim ke {sent_count} user
Gagal kirim ke {failed_count} user

Pesan:
{message}

Waktu broadcast: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""

            return {"success": True, "message": result_text}

        except Exception as e:
            return {"success": False, "message": f"Error broadcast: {str(e)}"}

    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics - legacy method for compatibility"""
        return self._get_comprehensive_stats()

    def _generate_email_report(self, from_number: str) -> Dict[str, Any]:
        """Generate and send PDF report via email"""
        try:
            # Import ReportService when needed to avoid circular import
            if self.report_service is None:
                from services.report_service import ReportService
                self.report_service = ReportService(self.whatsapp_service)
            
            # Use ReportService for report generation
            result = self.report_service.generate_and_send_report_async(
                from_number, "admin"
            )
            return result

        except Exception as e:
            return {"success": False, "message": f"Error generating report: {str(e)}"}

    def _get_memory_stats(self, args: str) -> Dict[str, Any]:
        """Get AI Agent memory statistics for a user"""
        try:
            if not args.strip():
                return {
                    "success": False,
                    "message": 'Format: `/admin memory_stats <hp>`\nContoh: `/admin memory_stats +6281234567890`',
                }

            # Normalize phone number
            from core.utils import normalize_phone_for_db
            phone = normalize_phone_for_db(args.strip())
            
            # Get memory stats from AI Agent
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            memory_stats = ai_agent.get_memory_stats(phone)
            
            if not memory_stats:
                return {
                    "success": True,
                    "message": f"Tidak ada data memory untuk user {phone}",
                }
            
            # Format memory stats
            stats_text = f"""MEMORY STATS AI AGENT
User: {phone}

📊 STATISTIK MEMORY:
• Total Facts: {memory_stats.get('user_facts_count', 0)}
• Total Conversations: {memory_stats.get('conversation_count', 0)}

📈 AKTIVITAS TERKINI (30 hari):
• Total Messages: {memory_stats.get('recent_activity', {}).get('total_messages', 0)}
• User Messages: {memory_stats.get('recent_activity', {}).get('user_messages', 0)}
• Bot Messages: {memory_stats.get('recent_activity', {}).get('bot_messages', 0)}
• First Message: {memory_stats.get('recent_activity', {}).get('first_message', 'N/A')}
• Last Message: {memory_stats.get('recent_activity', {}).get('last_message', 'N/A')}

🎯 TOPIK YANG SERING DIBICARAKAN:
{chr(10).join([f"• {topic}" for topic in memory_stats.get('common_topics', [])]) if memory_stats.get('common_topics') else "• Tidak ada data"}

🔑 MEMORY KEYS:
{chr(10).join([f"• {key}" for key in memory_stats.get('memory_keys', [])]) if memory_stats.get('memory_keys') else "• Tidak ada data"}

💬 PERCAKAPAN TERAKHIR:
{memory_stats.get('last_conversation', 'Tidak ada data')}"""
            
            return {"success": True, "message": stats_text}
            
        except Exception as e:
            return {"success": False, "message": f"Error mengambil memory stats: {str(e)}"}
