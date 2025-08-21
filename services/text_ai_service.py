"""
Text AI Service
Service untuk percakapan natural language menggunakan API Lunos.tech
Specialized untuk conversation, education, dan Q&A
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from core.config import get_config
from database.models import CollectionPointModel, UserInteractionModel, UserModel, DatabaseManager

logger = logging.getLogger(__name__)

class TextAIService:
    """Service untuk percakapan AI menggunakan Lunos.tech API"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv('LUNOS_API_KEY')
        self.base_url = os.getenv('LUNOS_BASE_URL', 'https://api.lunos.tech/v1')
        self.model = os.getenv('LUNOS_TEXT_MODEL', 'google/gemini-2.0-flash')
        
        # Setup headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize database models
        self.db_manager = DatabaseManager()
        self.collection_model = CollectionPointModel(self.db_manager)
        self.interaction_model = UserInteractionModel(self.db_manager)
        self.user_model = UserModel(self.db_manager)
        
        # Bot context
        self.context = self._load_bot_context()
        
        if not self.api_key:
            logger.warning("Lunos API key not found. Using template responses.")
            self.use_ai = False
        else:
            self.use_ai = True
            logger.info(f"Text AI service initialized with model: {self.model}")
    
    def _load_bot_context(self) -> Dict[str, Any]:
        """Load bot personality and comprehensive context"""
        return {
            "name": "EcoBot",
            "role": "Asisten virtual pengelolaan sampah untuk Desa Cukangkawung",
            "personality": "Ramah, informatif, dan peduli lingkungan",
            "capabilities": [
                "Memberikan tips pengelolaan sampah",
                "Menunjukkan lokasi titik pengumpulan sampah",
                "Edukasi tentang daur ulang",
                "Informasi jadwal pengumpulan",
                "Menjawab pertanyaan seputar lingkungan"
            ],
            "knowledge_base": {
                "village": "Desa Cukangkawung",
                "waste_types": ["organik", "anorganik", "B3"],
                "services": ["edukasi", "peta lokasi", "tips", "jadwal"]
            }
        }
    
    def generate_response(self, user_message: str, user_phone: str = None) -> Optional[str]:
        """Generate natural AI response using Lunos.tech"""
        if not self.use_ai:
            return self._fallback_response(user_message, user_phone)
        
        try:
            # Get user and data context
            user_context = self._get_user_context(user_phone) if user_phone else {}
            data_context = self._get_data_context(user_message)
            
            system_prompt = self._build_system_prompt(user_context, data_context)
            response = self._call_lunos_api(system_prompt, user_message)
            
            # Log successful interaction
            if user_phone:
                self.interaction_model.log_interaction(
                    user_phone, 'ai_conversation', 
                    user_message, response, True
                )
            
            return response
        except Exception as e:
            logger.error(f"Lunos API error: {str(e)}")
            return self._fallback_response(user_message, user_phone)
    
    def _call_lunos_api(self, system_prompt: str, user_message: str) -> str:
        """Call Lunos chat completion API"""
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 400,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _build_system_prompt(self, user_context: Dict, data_context: Dict) -> str:
        """Build comprehensive system prompt with bot context"""
        prompt = f"""Kamu adalah {self.context['name']}, {self.context['role']}.

KEPRIBADIAN: {self.context['personality']}

KEMAMPUAN UTAMA:
"""
        for capability in self.context['capabilities']:
            prompt += f"- {capability}\n"
        
        prompt += f"""
KONTEKS LOKASI: {self.context['knowledge_base']['village']}

JENIS SAMPAH YANG DAPAT DIIDENTIFIKASI:
- Organik: sisa makanan, daun, ranting, kulit buah
- Anorganik: plastik, kaleng, kertas, kaca, logam
- B3 (Berbahaya): baterai, lampu, obat kadaluarsa, cat, pestisida

LAYANAN YANG TERSEDIA:
- Kirim foto sampah untuk identifikasi otomatis dan tips pengelolaan
- Ketik 'lokasi' untuk melihat titik pengumpulan terdekat
- Ketik 'edukasi' untuk tips pengelolaan sampah dan daur ulang
- Ketik 'jadwal' untuk info jadwal pengumpulan sampah

INSTRUKSI PERILAKU:
1. Selalu ramah, informatif, dan tidak kaku seperti customer service profesional
2. Gunakan bahasa Indonesia yang natural dan mudah dipahami warga desa
3. Jika ditanya tentang layanan di luar kemampuan, arahkan ke layanan yang tersedia
4. Berikan respon yang personal dan praktis
5. Selalu akhiri dengan ajakan menggunakan layanan lain atau bertanya lebih lanjut
6. Fokus pada advice yang helpful dan bisa langsung diterapkan

CATATAN: Respon maksimal 4-5 kalimat agar mudah dibaca di WhatsApp.
"""
        
        # Add user context
        if user_context:
            prompt += f"\nKONTEKS USER: Role {user_context.get('role', 'warga')} dengan {user_context.get('recent_interactions', 0)} interaksi sebelumnya."
        
        # Add data context
        if data_context:
            if 'collection_points' in data_context:
                prompt += f"\nDATA TERSEDIA: {len(data_context['collection_points'])} titik pengumpulan sampah aktif."
                for point in data_context['collection_points'][:2]:  # Show first 2 points
                    prompt += f"\n- {point['name']}: {point.get('contact', 'No contact')} ({point.get('schedule', 'No schedule')})"
        
        return prompt
    
    def _get_user_context(self, user_phone: str) -> Dict[str, Any]:
        """Get user context from database"""
        if not user_phone:
            return {}
        
        try:
            user_role = self.user_model.get_user_role(user_phone)
            recent_interactions = self.interaction_model.get_user_interactions(user_phone, 5)
            
            return {
                'phone': user_phone,
                'role': user_role,
                'recent_interactions': len(recent_interactions),
                'last_interaction': recent_interactions[0] if recent_interactions else None
            }
        except:
            return {'phone': user_phone, 'role': 'warga'}
    
    def _get_data_context(self, message: str) -> Dict[str, Any]:
        """Get relevant data context based on message"""
        context = {}
        message_lower = message.lower()
        
        try:
            # Check if asking about locations
            if any(word in message_lower for word in ['lokasi', 'tempat', 'dimana', 'peta']):
                collection_points = self.collection_model.get_all_collection_points()
                context['collection_points'] = collection_points
            
            # Check if asking about schedule
            if any(word in message_lower for word in ['jadwal', 'kapan', 'waktu']):
                # Get schedule from collection points
                schedule_info = "Senin, Rabu, Jumat (07:00-16:00)"
                context['schedule_info'] = schedule_info
                
        except Exception as e:
            logger.error(f"Error getting data context: {e}")
        
        return context
    
    def _fallback_response(self, user_message: str, user_phone: str = None) -> str:
        """Enhanced fallback to template responses when AI is not available"""
        message_lower = user_message.lower()
        
        # Get data context for enhanced fallback
        data_context = self._get_data_context(user_message)
        
        # Response berdasarkan konteks yang diperbaiki dengan data real
        if any(word in message_lower for word in ['lokasi', 'tempat', 'dimana', 'peta']):
            collection_points = data_context.get('collection_points', [])
            if collection_points:
                response = "Titik Pengumpulan Sampah di Desa Cukangkawung:\n\n"
                for i, point in enumerate(collection_points[:3], 1):
                    response += f"{i}. {point['name']}\n"
                    response += f"   {point.get('contact', 'Kontak tidak tersedia')}\n"
                    response += f"   ⏰ {point.get('schedule', 'Jadwal belum tersedia')}\n"
                    if point.get('accepted_waste_types'):
                        try:
                            waste_types = json.loads(point['accepted_waste_types']) if isinstance(point['accepted_waste_types'], str) else point['accepted_waste_types']
                            response += f"   {', '.join(waste_types)}\n"
                        except:
                            response += f"   Semua jenis sampah\n"
                    response += "\n"
                response += "Butuh info lebih detail? Tanya aja! 🗺️"
                return response
            else:
                return "Ada beberapa titik pengumpulan sampah di desa kita! Mau tahu yang mana yang terdekat dengan rumah?"
        
        elif any(word in message_lower for word in ['jadwal', 'kapan', 'waktu']):
            if collection_points := data_context.get('collection_points', []):
                response = "Jadwal Pengumpulan Sampah:\n\n"
                for point in collection_points:
                    if point.get('schedule'):
                        response += f"{point['name']}\n   ⏰ {point['schedule']}\n\n"
                response += "Jangan lupa pisahkan sampah sebelum disetor ya! ♻️"
                return response
            else:
                return "Jadwal pengumpulan sampah rutin: Senin, Rabu, Jumat pukul 07.00-16.00 WIB. Sampah B3 khusus Sabtu terakhir setiap bulan! ⏰"
        
        elif any(keyword in message_lower for keyword in ['halo', 'hai', 'hello', 'selamat']):
            return "Halo! Saya EcoBot, asisten pengelolaan sampah Desa Cukangkawung. Ada yang bisa saya bantu? Kirim foto sampah untuk identifikasi atau ketik 'help' untuk bantuan. 🌱"
        
        elif any(keyword in message_lower for keyword in ['terima kasih', 'thanks', 'makasih']):
            return "Sama-sama! Senang bisa membantu. Jangan lupa untuk selalu pilah sampah ya. Ada lagi yang ingin ditanyakan? 😊"
        
        elif any(word in message_lower for word in ['help', 'bantuan', 'tolong', 'fitur']):
            return """Saya EcoBot, siap membantu! 🤖 

Layanan yang tersedia:
📸 Kirim foto sampah untuk identifikasi
Ketik 'lokasi' untuk titik pengumpulan
Ketik 'jadwal' untuk waktu pengumpulan  
🎓 Ketik 'edukasi' untuk tips pengelolaan

Ada yang mau ditanyakan? 😊"""
        
        elif any(word in message_lower for word in ['sampah', 'limbah', 'buang']):
            return "Saya siap bantu mengelola sampah! Kirim foto sampahnya atau tanya tentang cara memilah yang benar yuk!"
        
        elif any(word in message_lower for word in ['organik', 'kompos', 'makanan']):
            return "Sampah organik terbaik untuk kompos! Sisa sayur, buah, dan daun bisa jadi pupuk alami. Mau cara bikinnya?"
        
        elif any(word in message_lower for word in ['plastik', 'anorganik', 'kaleng', 'botol']):
            return "Plastik dan kaleng punya nilai ekonomi tinggi lho! 💰 Pisahkan yang bersih, bisa dijual ke pengepul atau bank sampah."
        
        else:
            return "Maaf, saya tidak sepenuhnya memahami pertanyaan Anda. Saya bisa membantu dengan informasi tentang pengelolaan sampah, lokasi pengumpulan, atau tips lingkungan. Coba kirim foto sampah atau ketik 'help' untuk bantuan! 🌱"
    
    def enhance_response(self, service_type: str, base_response: str, user_context: Dict = None) -> str:
        """Enhance service responses with AI to make them more natural"""
        if not self.use_ai:
            return base_response
        
        try:
            enhancement_prompt = f"""Berdasarkan respon layanan berikut, buatlah versi yang lebih natural dan personal sebagai customer service yang ramah:

LAYANAN: {service_type}
RESPON ASLI: {base_response}

Instruksi:
1. Buat lebih natural dan ramah seperti customer service desa yang dekat dengan warga
2. Tambahkan sedikit personal touch dan empati
3. Tetap informatif dan akurat
4. Jangan ubah informasi teknis yang penting (seperti koordinat, alamat, jadwal)
5. Maksimal sama panjang dengan respon asli
6. Gunakan bahasa yang mudah dipahami warga desa

Respon yang lebih natural:"""
            
            enhanced = self._call_lunos_api(enhancement_prompt, "Tolong buat lebih natural")
            return enhanced if enhanced else base_response
        except:
            return base_response
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about text AI capabilities"""
        return {
            'provider': 'Lunos.tech',
            'model': self.model,
            'capabilities': self.context['capabilities'],
            'supported_languages': ['Indonesian'],
            'response_types': [
                'Informational',
                'Educational', 
                'Conversational',
                'Location-based',
                'Schedule-based'
            ],
            'max_tokens': 400,
            'use_ai': self.use_ai
        }
