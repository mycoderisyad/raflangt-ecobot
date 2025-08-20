"""
Admin Command Handler
Menangani perintah admin untuk operasi CRUD via WhatsApp
"""

import logging
import json
from typing import Dict, List, Any, Optional
from database.models import (
    get_user_model,
    get_waste_classification_model,
    get_collection_point_model,
    get_collection_schedule_model,
    get_system_log_model
)

logger = logging.getLogger(__name__)

class AdminCommandHandler:
    """Handle admin commands for CRUD operations via WhatsApp"""
    
    def __init__(self):
        self.user_model = get_user_model()
        self.waste_model = get_waste_classification_model()
        self.collection_model = get_collection_point_model()
        self.schedule_model = get_collection_schedule_model()
        self.log_model = get_system_log_model()
    
    def handle_admin_command(self, command: str, args: List[str], admin_phone: str) -> str:
        """Route admin command to appropriate handler"""
        if not self.user_model.is_admin(admin_phone):
            return "❌ *Akses Ditolak*\nAnda tidak memiliki izin admin."
        
        command = command.lower()
        
        # User management commands
        if command == 'user_list':
            return self._handle_user_list()
        elif command == 'user_role':
            return self._handle_user_role_change(args, admin_phone)
        elif command == 'user_add':
            return self._handle_user_add(args, admin_phone)
        elif command == 'user_stats':
            return self._handle_user_stats(args)
        
        # Collection point commands
        elif command == 'point_add':
            return self._handle_point_add(args, admin_phone)
        elif command == 'point_list':
            return self._handle_point_list()
        elif command == 'point_update':
            return self._handle_point_update(args, admin_phone)
        elif command == 'point_delete':
            return self._handle_point_delete(args, admin_phone)
        
        # Schedule commands
        elif command == 'schedule_add':
            return "🚧 *Fitur Dalam Pengembangan*\nPenjadwalan akan segera tersedia."
        elif command == 'schedule_list':
            return "🚧 *Fitur Dalam Pengembangan*\nDaftar jadwal akan segera tersedia."
        elif command == 'schedule_update':
            return "🚧 *Fitur Dalam Pengembangan*\nUpdate jadwal akan segera tersedia."
        
        # Statistics and logs
        elif command == 'stats':
            return self._handle_system_stats()
        elif command == 'logs':
            return self._handle_system_logs(args)
        
        # Help
        elif command == 'help':
            return self._handle_admin_help()
        
        else:
            return f"❌ *Perintah Tidak Dikenal*\nGunakan '/admin help' untuk melihat daftar perintah."
    
    def _handle_user_list(self) -> str:
        """List all users"""
        try:
            users = self.user_model.get_all_users()
            if not users:
                return "📋 *Daftar Pengguna*\nTidak ada pengguna terdaftar."
            
            response = "📋 *Daftar Pengguna*\n\n"
            for user in users[:20]:  # Limit to 20 users
                status = "🟢" if user.get('is_active') else "🔴"
                response += f"{status} *{user['phone_number']}*\n"
                response += f"   Role: {user['role']}\n"
                response += f"   Pesan: {user['total_messages']}\n"
                response += f"   Gambar: {user['total_images']}\n"
                response += f"   Poin: {user['points']}\n\n"
            
            if len(users) > 20:
                response += f"... dan {len(users) - 20} pengguna lainnya"
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return "❌ *Error*\nGagal mengambil daftar pengguna."
    
    def _handle_user_role_change(self, args: List[str], admin_phone: str) -> str:
        """Change user role"""
        if len(args) < 2:
            return "❌ *Format Salah*\nGunakan: /admin user_role <nomor_hp> <role>\nRole: warga, koordinator, admin"
        
        phone_number = args[0]
        new_role = args[1].lower()
        
        if new_role not in ['warga', 'koordinator', 'admin']:
            return "❌ *Role Tidak Valid*\nRole yang valid: warga, koordinator, admin"
        
        try:
            success = self.user_model.update_user_role(phone_number, new_role, admin_phone)
            if success:
                return f"✅ *Role Berhasil Diubah*\n{phone_number} → {new_role}"
            else:
                return "❌ *Gagal Mengubah Role*\nPastikan nomor HP sudah terdaftar."
                
        except Exception as e:
            logger.error(f"Error changing user role: {str(e)}")
            return "❌ *Error*\nGagal mengubah role pengguna."
    
    def _handle_user_add(self, args: List[str], admin_phone: str) -> str:
        """Add new user"""
        if len(args) < 1:
            return "❌ *Format Salah*\nGunakan: /admin user_add <nomor_hp> [role] [nama]"
        
        phone_number = args[0]
        role = args[1] if len(args) > 1 else 'warga'
        name = args[2] if len(args) > 2 else None
        
        try:
            success = self.user_model.create_user(phone_number, name)
            if success and role != 'warga':
                self.user_model.update_user_role(phone_number, role, admin_phone)
            
            if success:
                return f"✅ *User Berhasil Ditambahkan*\n{phone_number} sebagai {role}"
            else:
                return "❌ *Gagal Menambahkan User*\nUser mungkin sudah exist."
                
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            return "❌ *Error*\nGagal menambahkan user."
    
    def _handle_user_stats(self, args: List[str]) -> str:
        """Get user statistics"""
        if len(args) < 1:
            # Overall stats
            try:
                role_counts = self.user_model.get_user_count_by_role()
                response = "📊 *Statistik Pengguna*\n\n"
                for role, count in role_counts.items():
                    response += f"• {role.title()}: {count}\n"
                return response
                
            except Exception as e:
                logger.error(f"Error getting user stats: {str(e)}")
                return "❌ *Error*\nGagal mengambil statistik pengguna."
        else:
            # Specific user stats
            phone_number = args[0]
            try:
                user = self.user_model.get_user(phone_number)
                if not user:
                    return f"❌ *User Tidak Ditemukan*\n{phone_number} tidak terdaftar."
                
                response = f"📊 *Statistik User: {phone_number}*\n\n"
                response += f"• Role: {user['role']}\n"
                response += f"• Total Pesan: {user['total_messages']}\n"
                response += f"• Total Gambar: {user['total_images']}\n"
                response += f"• Poin: {user['points']}\n"
                response += f"• Status: {'Aktif' if user['is_active'] else 'Nonaktif'}\n"
                response += f"• Bergabung: {user['first_seen']}\n"
                response += f"• Aktif Terakhir: {user['last_active']}\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error getting specific user stats: {str(e)}")
                return "❌ *Error*\nGagal mengambil statistik user."
    
    def _handle_point_add(self, args: List[str], admin_phone: str) -> str:
        """Add collection point"""
        if len(args) < 4:
            return "❌ *Format Salah*\nGunakan: /admin point_add <nama> <alamat> <jenis_sampah> <jam_operasi>"
        
        name = args[0]
        address = args[1]
        waste_types = [w.strip() for w in args[2].split(',')]
        operating_hours = args[3]
        
        try:
            success = self.collection_model.add_collection_point(
                name, address, waste_types, operating_hours=operating_hours, admin_phone=admin_phone
            )
            if success:
                return f"✅ *Titik Pengumpulan Ditambahkan*\n{name} berhasil ditambahkan."
            else:
                return "❌ *Gagal Menambahkan Titik*\nTerjadi kesalahan."
                
        except Exception as e:
            logger.error(f"Error adding collection point: {str(e)}")
            return "❌ *Error*\nGagal menambahkan titik pengumpulan."
    
    def _handle_point_list(self) -> str:
        """List collection points"""
        try:
            points = self.collection_model.get_collection_points()
            if not points:
                return "📍 *Titik Pengumpulan*\nTidak ada titik pengumpulan terdaftar."
            
            response = "📍 *Daftar Titik Pengumpulan*\n\n"
            for point in points[:10]:  # Limit to 10
                status = "🟢" if point.get('is_active') else "🔴"
                response += f"{status} *{point['name']}*\n"
                response += f"   📍 {point['address']}\n"
                if point.get('operating_hours'):
                    response += f"   🕒 {point['operating_hours']}\n"
                
                # Parse waste types
                try:
                    waste_types = json.loads(point.get('accepted_waste_types', '[]'))
                    response += f"   🗑️ {', '.join(waste_types)}\n\n"
                except:
                    response += f"   🗑️ Data tidak valid\n\n"
            
            if len(points) > 10:
                response += f"... dan {len(points) - 10} titik lainnya"
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing collection points: {str(e)}")
            return "❌ *Error*\nGagal mengambil daftar titik pengumpulan."
    
    def _handle_system_stats(self) -> str:
        """Get system statistics"""
        try:
            # Get basic counts
            role_counts = self.user_model.get_user_count_by_role()
            points = self.collection_model.get_collection_points()
            
            # Get classification stats
            classification_stats = self.waste_model.get_classification_stats(days=7)
            
            response = "📊 *Statistik Sistem*\n\n"
            response += "*👥 Pengguna:*\n"
            for role, count in role_counts.items():
                response += f"• {role.title()}: {count}\n"
            
            response += f"\n*📍 Titik Pengumpulan:* {len(points)}\n"
            
            response += "\n*🗑️ Klasifikasi (7 hari):*\n"
            total_classifications = sum(classification_stats.values())
            response += f"• Total: {total_classifications}\n"
            for waste_type, count in classification_stats.items():
                response += f"• {waste_type}: {count}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return "❌ *Error*\nGagal mengambil statistik sistem."
    
    def _handle_system_logs(self, args: List[str]) -> str:
        """Get system logs"""
        try:
            level = args[0] if args else None
            logs = self.log_model.get_logs(level=level, limit=10)
            
            if not logs:
                return "📝 *Log Sistem*\nTidak ada log ditemukan."
            
            response = f"📝 *Log Sistem*\n"
            if level:
                response += f"Level: {level}\n"
            response += "\n"
            
            for log in logs:
                response += f"• *{log['level']}* | {log['module']}\n"
                response += f"  {log['message']}\n"
                response += f"  {log['created_at']}\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting system logs: {str(e)}")
            return "❌ *Error*\nGagal mengambil log sistem."
    
    def _handle_admin_help(self) -> str:
        """Show admin help"""
        return """🔧 *Perintah Admin*

*👥 Manajemen User:*
• `/admin user_list` - Daftar semua user
• `/admin user_role <hp> <role>` - Ubah role user
• `/admin user_add <hp> [role] [nama]` - Tambah user
• `/admin user_stats [hp]` - Statistik user

*📍 Titik Pengumpulan:*
• `/admin point_add <nama> <alamat> <jenis> <jam>` - Tambah titik
• `/admin point_list` - Daftar titik pengumpulan

*📊 Sistem:*
• `/admin stats` - Statistik sistem
• `/admin logs [level]` - Log sistem

*Role yang valid:* warga, koordinator, admin
*Level log:* INFO, WARNING, ERROR, CRITICAL"""

    def parse_admin_command(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse admin command from message"""
        message = message.strip()
        
        # Check if it's an admin command
        if not message.startswith('/admin'):
            return None
        
        # Remove /admin prefix and split
        parts = message[6:].strip().split()
        if not parts:
            return {'command': 'help', 'args': []}
        
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return {
            'command': command,
            'args': args
        }
