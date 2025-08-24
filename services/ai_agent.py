"""
AI Agent Service with Long-Term Memory and Database Integration
Advanced AI agent that can memorize conversations, remember user details, 
and adapt communication style based on user history and mode
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from core.config import get_config
from database.models.memory_models import get_memory_models
from database.models import UserModel, DatabaseManager
from services.image_analysis_service import ImageAnalysisService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent with long-term memory capabilities and database integration"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv("LUNOS_API_KEY")
        self.base_url = os.getenv("LUNOS_BASE_URL")
        self.model = os.getenv("LUNOS_AGENT_MODEL")
        
        # Setup headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-App-ID": "ecobot-whatsapp-v1.0",
        }
        
        # Initialize database models
        self.db_manager = DatabaseManager()
        self.user_model = UserModel(self.db_manager)
        self.memory_model, self.conversation_model = get_memory_models()
        
        # Initialize image analysis service
        self.image_analyzer = ImageAnalysisService()
        
        # Bot personality
        self.personality = {
            "name": "EcoBot",
            "role": "Asisten virtual pengelolaan sampah",
            "traits": [
                "Ramah dan peduli lingkungan",
                "Responsif terhadap kebutuhan pengguna",
                "Mudah diajak berinteraksi",
                "Memberikan informasi yang akurat dan bermanfaat",
            ],
        }

        # AI Agent modes
        self.modes = {
            "ecobot": {
                "name": "EcoBot Service Mode",
                "description": "Mode khusus untuk layanan EcoBot (database + rules)",
                "scope": "database_only",
                "personality": "Fokus pada data EcoBot, jadwal, lokasi, dan fitur spesifik"
            },
            "general": {
                "name": "General Waste Management Mode", 
                "description": "Mode umum untuk edukasi sampah (AI + internet knowledge)",
                "scope": "general_waste",
                "personality": "Edukasi umum tentang pengelolaan sampah dan lingkungan"
            },
            "hybrid": {
                "name": "Hybrid Mode",
                "description": "Kombinasi database EcoBot + pengetahuan umum",
                "scope": "hybrid",
                "personality": "Memberikan informasi spesifik EcoBot + edukasi umum"
            }
        }
        
        if not self.api_key:
            logger.warning("Lunos API key not found. AI Agent will not function.")
            self.use_ai = False
        else:
            self.use_ai = True
            logger.info(f"AI Agent initialized with model: {self.model}")
    
    def process_message(self, user_message: str, user_phone: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Process user message with specified mode"""
        if not self.use_ai:
            fallback_response = self._fallback_response(user_message, user_phone, mode)
            return {"status": "success", "reply_sent": fallback_response}
        
        try:
            # Get user context and memory
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_history = self.conversation_model.get_recent_conversation(
                user_phone, 20
            )

            # Build comprehensive context based on mode
            context = self._build_context(
                user_phone, user_context, user_facts, conversation_history, mode
            )

            # Generate response based on mode
            if mode == "ecobot":
                response = self._generate_ecobot_response(user_message, context)
            elif mode == "general":
                response = self._generate_general_response(user_message, context)
            else:  # hybrid mode
                response = self._generate_hybrid_response(user_message, context)
            
            # Extract and save facts from the conversation
            try:
                self._extract_and_save_facts(user_phone, user_message, response)
            except Exception as e:
                logger.error(f"Error extracting and saving facts: {str(e)}")
            
            # Save conversation to history
            try:
                self.conversation_model.add_message(user_phone, "user", user_message)
                self.conversation_model.add_message(user_phone, "assistant", response)
            except Exception as e:
                logger.error(f"Error saving conversation history: {str(e)}")

            return {"status": "success", "reply_sent": response}
            
        except Exception as e:
            logger.error(f"AI Agent error: {str(e)}")
            fallback_response = self._fallback_response(user_message, user_phone, mode)
            return {"status": "error", "reply_sent": fallback_response, "error": str(e)}

    def process_image_message(self, image_data: bytes, user_phone: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Process image message with AI agent context and image analysis"""
        try:
            # Get user context for personalized response
            user_context = self._get_user_context(user_phone)
            user_name = user_context.get("name", "Teman")
            user_facts = self.memory_model.get_all_user_facts(user_phone)

            # Analyze the image using image analysis service
            analysis_result = self.image_analyzer.analyze_waste_image(
                image_data, user_phone
            )

            if analysis_result.get("success"):
                waste_type = analysis_result.get("waste_type", "TIDAK_TERIDENTIFIKASI")
                confidence = analysis_result.get("confidence", 0.0)
                description = analysis_result.get("description", "")
                tips = analysis_result.get("tips", "")

                # Create personalized response using AI agent context
                if user_name != "Teman" and user_name != "Belum dikenali":
                    greeting = f"Halo {user_name}! "
                else:
                    greeting = "Halo! "

                # Generate personalized response based on waste type
                if waste_type == "ORGANIK":
                    encouragement = "Bagus sekali! Sampah organik bisa jadi kompos lho! "
                elif waste_type == "ANORGANIK":
                    encouragement = "Perfect! Jangan lupa pisahkan untuk daur ulang ya! "
                elif waste_type == "B3":
                    encouragement = "Hati-hati! Sampah ini perlu penanganan khusus. "
                else:
                    encouragement = "Mari kita pelajari jenis sampah ini bersama! "

                # Format confidence as percentage
                confidence_percent = int(confidence * 100)

                response = f"""{greeting}{encouragement}

**HASIL IDENTIFIKASI:**
• **Jenis Sampah:** {waste_type}
• **Tingkat Keyakinan:** {confidence_percent}%
• **Yang Terdeteksi:** {description}

**Tips Pengelolaan:**
{tips}

Terima kasih sudah peduli lingkungan! Kirim foto sampah lain kalau mau belajar lebih banyak! """

                # Save to conversation history
                try:
                    self.conversation_model.add_message(
                        user_phone, "user", "Mengirim foto sampah untuk dianalisis"
                    )
                    self.conversation_model.add_message(user_phone, "assistant", response)
                except Exception as e:
                    logger.error(f"Error saving image conversation: {str(e)}")

                return {
                    "status": "success",
                    "reply_sent": response,
                    "analysis_result": analysis_result,
                }
            else:
                error_msg = analysis_result.get("error", "Gagal menganalisis gambar")
                response = f"""Maaf, ada kendala saat menganalisis gambar:

{error_msg}

Coba kirim foto yang lebih jelas atau coba lagi nanti ya! """

                return {"status": "error", "reply_sent": response, "error": error_msg}

        except Exception as e:
            logger.error(f"Error in AI agent image processing: {str(e)}")
            response = f"""Maaf, terjadi kesalahan sistem saat menganalisis gambar.

Silakan coba lagi dalam beberapa saat. Jika masalah berlanjut, hubungi admin ya! """

            return {"status": "error", "reply_sent": response, "error": str(e)}

    def get_ai_capabilities(self) -> Dict[str, Any]:
        """Get information about AI capabilities"""
        try:
            return {
                "text_ai": {
                    "available": self.use_ai,
                    "provider": "Lunos.tech",
                    "model": self.model,
                    "modes": list(self.modes.keys()),
                },
                "image_analysis": {
                    "available": True,
                    "provider": "unli.dev",
                    "supported_formats": ["JPEG", "PNG", "GIF"],
                    "max_size_mb": 16,
                    "features": ["waste_classification", "confidence_scoring", "tips_generation"],
                },
                "memory_system": {
                    "available": True,
                    "features": ["user_facts", "conversation_history", "style_analysis"],
                },
                "database_integration": {
                    "available": True,
                    "features": ["locations", "schedules", "statistics", "user_data"],
                },
            }
        except Exception as e:
            logger.error(f"Error getting AI capabilities: {str(e)}")
            return {
                "text_ai": {"available": False},
                "image_analysis": {"available": False},
                "error": str(e),
            }
    
    def _get_user_context(self, user_phone: str) -> Dict[str, Any]:
        """Get user context from database"""
        try:
            user = self.user_model.get_user(user_phone)
            if user:
                return {
                    "phone": user_phone,
                    "name": user["name"],
                    "role": user["role"],
                    "registration_status": user["registration_status"],
                    "points": user["points"],
                    "first_seen": user["first_seen"],
                    "last_active": user["last_active"],
                    "total_messages": user["total_messages"],
                    "total_images": user["total_images"],
                }
            else:
                return {"phone": user_phone, "role": "warga"}
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {"phone": user_phone, "role": "warga"}
    
    def _build_context(self, user_phone: str, user_context: Dict, user_facts: Dict, 
                      conversation_history: List[Dict], mode: str) -> Dict[str, Any]:
        """Build comprehensive context for the AI agent"""
        return {
            "user_context": user_context,
            "user_facts": user_facts,
            "conversation_history": conversation_history,
            "personality": self.personality,
            "mode": self.modes.get(mode, self.modes["hybrid"]),
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_ecobot_response(self, user_message: str, context: Dict) -> str:
        """Generate response for EcoBot service mode (database-focused)"""
        # Get database data for specific queries
        db_data = self._get_database_data(user_message)
        
        system_prompt = self._build_ecobot_system_prompt(context, db_data)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return self._call_lunos_api(messages)

    def _generate_general_response(self, user_message: str, context: Dict) -> str:
        """Generate response for general waste management mode"""
        system_prompt = self._build_general_system_prompt(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return self._call_lunos_api(messages)

    def _generate_hybrid_response(self, user_message: str, context: Dict) -> str:
        """Generate response for hybrid mode (database + general knowledge)"""
        # Get database data for specific queries
        db_data = self._get_database_data(user_message)
        
        system_prompt = self._build_hybrid_system_prompt(context, db_data)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return self._call_lunos_api(messages)

    def _get_database_data(self, user_message: str) -> Dict[str, Any]:
        """Extract relevant data from database based on user message"""
        data = {}
        
        try:
            # Check for location queries
            if any(word in user_message.lower() for word in ["lokasi", "bank sampah", "tempat sampah", "dimana", "mana"]):
                result = self.db_manager.execute_query(
                    "SELECT name, type, latitude, longitude, description FROM collection_points WHERE is_active = 1"
                )
                data["collection_points"] = result

            # Check for schedule queries
            if any(word in user_message.lower() for word in ["jadwal", "kapan", "waktu", "pengumpulan"]):
                result = self.db_manager.execute_query(
                    "SELECT location_name, schedule_day, schedule_time, waste_types FROM collection_schedules WHERE is_active = 1"
                )
                data["schedules"] = result

            # Check for user statistics
            if any(word in user_message.lower() for word in ["statistik", "data", "aktivitas", "report"]):
                result = self.db_manager.execute_query(
                    "SELECT COUNT(*) as total_users, SUM(points) as total_points FROM users WHERE is_active = 1"
                )
                data["statistics"] = result[0] if result else None

            # Check for waste classification data
            if any(word in user_message.lower() for word in ["klasifikasi", "jenis sampah", "analisis"]):
                result = self.db_manager.execute_query(
                    "SELECT waste_type, COUNT(*) as count FROM waste_classifications GROUP BY waste_type"
                )
                data["waste_analysis"] = result

        except Exception as e:
            logger.error(f"Error getting database data: {str(e)}")
            
        return data

    def _call_lunos_api(self, messages: List[Dict]) -> str:
        """Call Lunos API for response generation"""
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.7,
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    def _build_ecobot_system_prompt(self, context: Dict, db_data: Dict) -> str:
        """Build system prompt for EcoBot service mode"""
        user_context = context["user_context"]
        user_facts = context["user_facts"]
        mode_info = context["mode"]
        conversation_history = context["conversation_history"]
        
        # Analyze user communication style from history
        communication_style = self._analyze_user_style(conversation_history)
        
        prompt = f"""Kamu adalah {self.personality['name']} dalam mode {mode_info['name']}.

{mode_info['description']}
        
INFORMASI USER:
- Nama: {user_context.get('name', 'Belum dikenali')}
- Role: {user_context.get('role', 'warga')}
- Poin: {user_context.get('points', 0)}

FAKTA USER:"""
        if user_facts:
            for key, value in user_facts.items():
                prompt += f"\n- {key}: {value}"
        else:
            prompt += "\n- Belum ada fakta personal yang diketahui"

        prompt += f"""

DATA ECOBOT YANG TERSEDIA:"""
        
        if db_data.get("collection_points"):
            prompt += "\n\nLOKASI BANK SAMPAH:"
            for point in db_data["collection_points"]:
                prompt += f"\n- {point[0]} di {point[1]} (Jadwal: {point[2]})"

        if db_data.get("schedules"):
            prompt += "\n\nJADWAL PENGUMPULAN:"
            for schedule in db_data["schedules"]:
                prompt += f"\n- {schedule[0]} ({schedule[1]} {schedule[2]}) untuk {schedule[3]}"

        if db_data.get("statistics"):
            prompt += f"\n\nSTATISTIK: Total {db_data['statistics'][0]} user aktif dengan {db_data['statistics'][1]} total poin"
        
        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}

INSTRUKSI KHUSUS:
1. HANYA gunakan data dari database EcoBot yang tersedia
2. Jika user bertanya tentang lokasi/jadwal yang tidak ada di database, katakan data tidak tersedia
3. Fokus pada fitur EcoBot: lokasi, jadwal, poin, statistik
4. Jangan berikan informasi umum tentang sampah, hanya data spesifik EcoBot
5. Gunakan nama user jika tersedia
6. Respons maksimal 3-4 kalimat, fokus pada data yang diminta

CONTOH RESPONS:
- "Berdasarkan database EcoBot, ada 5 lokasi bank sampah aktif di Kampung Hijau"
- "Jadwal pengumpulan sampah di RT 05 setiap Selasa 14:00-18:00"
- "Maaf, data tersebut tidak tersedia di database EcoBot saat ini"

PENGEMBANGAN RELASI:
- Bangun rapport yang natural, bukan seperti customer service
- Tunjukkan ketertarikan genuine pada kebutuhan user
- Ajukan pertanyaan follow-up yang relevan
- Celebrasi progress dan achievement user

 PERSONALISASI:
- Sesuaikan gaya bahasa dengan preferensi user (formal/informal)
- Gunakan nama user jika sudah diketahui
- Berikan saran yang spesifik berdasarkan data EcoBot
- Ingat konteks percakapan sebelumnya

PENTING: Kamu adalah asisten EcoBot yang memberikan informasi spesifik dari database dengan personalisasi tinggi."""

        return prompt

    def _build_general_system_prompt(self, context: Dict) -> str:
        """Build system prompt for general waste management mode"""
        user_context = context["user_context"]
        user_facts = context["user_facts"]
        conversation_history = context["conversation_history"]

        # Analyze user communication style from history
        communication_style = self._analyze_user_style(conversation_history)

        prompt = f"""Kamu adalah {self.personality['name']} dalam mode General Waste Management.

Mode ini fokus pada edukasi umum tentang pengelolaan sampah dan lingkungan.

INFORMASI USER:
- Nama: {user_context.get('name', 'Belum dikenali')}
- Role: {user_context.get('role', 'warga')}

FAKTA USER:"""
        if user_facts:
            for key, value in user_facts.items():
                prompt += f"\n- {key}: {value}"
        else:
            prompt += "\n- Belum ada fakta personal yang diketahui"

        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}

INSTRUKSI KHUSUS:
1. Berikan edukasi umum tentang pengelolaan sampah
2. Gunakan pengetahuan umum tentang lingkungan dan sampah
3. Jangan berikan informasi spesifik EcoBot (lokasi, jadwal, dll)
4. Fokus pada tips, edukasi, dan pengetahuan umum
5. Gunakan nama user jika tersedia
6. Respons natural dan edukatif

CONTOH TOPIK:
- Cara memilah sampah organik dan anorganik
- Manfaat daur ulang sampah
- Tips mengurangi sampah plastik
- Pentingnya menjaga lingkungan
- Jenis-jenis sampah dan cara penanganannya

PENGEMBANGAN RELASI:
- Bangun rapport yang natural dan friendly
- Tunjukkan empati terhadap kepedulian user pada lingkungan
- Ajukan pertanyaan follow-up untuk engagement
- Berikan motivasi dan encouragement

PERSONALISASI:
- Sesuaikan gaya bahasa dengan preferensi user
- Gunakan nama user jika sudah diketahui
- Berikan contoh yang relevan dengan situasi user
- Ingat topik yang pernah dibahas sebelumnya

PENTING: Kamu adalah asisten edukasi sampah umum dengan personalisasi tinggi."""

        return prompt

    def _build_hybrid_system_prompt(self, context: Dict, db_data: Dict) -> str:
        """Build system prompt for hybrid mode"""
        user_context = context["user_context"]
        user_facts = context["user_facts"]
        mode_info = context["mode"]
        conversation_history = context["conversation_history"]

        # Analyze user communication style from history
        communication_style = self._analyze_user_style(conversation_history)

        prompt = f"""Kamu adalah {self.personality['name']} dalam mode {mode_info['name']}.

{mode_info['description']}

INFORMASI USER:
- Nama: {user_context.get('name', 'Belum dikenali')}
- Role: {user_context.get('role', 'warga')}
- Poin: {user_context.get('points', 0)}

FAKTA USER:"""
        if user_facts:
            for key, value in user_facts.items():
                prompt += f"\n- {key}: {value}"
        else:
            prompt += "\n- Belum ada fakta personal yang diketahui"

        prompt += f"""

DATA ECOBOT YANG TERSEDIA:"""
        
        if db_data.get("collection_points"):
            prompt += "\n\nLOKASI BANK SAMPAH:"
            for point in db_data["collection_points"]:
                prompt += f"\n- {point[0]} di {point[1]} (Jadwal: {point[2]})"

        if db_data.get("schedules"):
            prompt += "\n\nJADWAL PENGUMPULAN:"
            for schedule in db_data["schedules"]:
                prompt += f"\n- {schedule[0]} ({schedule[1]} {schedule[2]}) untuk {schedule[3]}"

        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}

INSTRUKSI KHUSUS:
1. Gunakan data EcoBot jika tersedia dan relevan
2. Berikan edukasi umum jika tidak ada data spesifik
3. Kombinasikan informasi database + pengetahuan umum
4. Fokus pada pengelolaan sampah dan lingkungan
5. Gunakan nama user jika tersedia
6. Respons natural dan informatif

STRATEGI:
- Jika ada data EcoBot yang relevan, gunakan itu
- Jika tidak ada data spesifik, berikan edukasi umum
- Kombinasikan keduanya untuk respons yang lengkap
- Prioritaskan data EcoBot untuk pertanyaan spesifik

 PENGEMBANGAN RELASI:
- Bangun rapport yang natural, bukan seperti customer service
- Tunjukkan ketertarikan genuine pada kebutuhan user
- Ajukan pertanyaan follow-up yang relevan
- Celebrasi progress dan achievement user

PERSONALISASI:
- Sesuaikan gaya bahasa dengan preferensi user (formal/informal)
- Gunakan nama user jika sudah diketahui
- Berikan saran yang spesifik berdasarkan data EcoBot
- Ingat konteks percakapan sebelumnya

PENTING: Kamu adalah asisten hybrid yang memberikan informasi EcoBot + edukasi umum dengan personalisasi tinggi."""
        
        return prompt
    
    def _analyze_user_style(self, conversation_history: List[Dict]) -> Dict[str, str]:
        """Analyze user communication style from conversation history"""
        if not conversation_history:
            return {
                "formality": "Netral",
                "emoji_usage": "Jarang",
                "message_length": "Sedang",
                "preferred_topics": "Belum teridentifikasi",
            }

        user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
        
        # Analyze formality
        formal_indicators = ["terima kasih", "mohon", "silakan", "bapak", "ibu"]
        informal_indicators = ["hai", "halo", "gimana", "oke", "thanks", "makasih"]
        
        formal_count = sum(
            1
            for msg in user_messages
                          for indicator in formal_indicators 
            if indicator in msg["content"].lower()
        )
        informal_count = sum(
            1
            for msg in user_messages
                            for indicator in informal_indicators 
            if indicator in msg["content"].lower()
        )
        
        if formal_count > informal_count:
            formality = "Formal"
        elif informal_count > formal_count:
            formality = "Informal"
        else:
            formality = "Netral"
        
        # Analyze emoji usage
        emoji_count = sum(
            1
            for msg in user_messages
            if any(ord(char) > 127 for char in msg["content"])
        )
        if emoji_count > len(user_messages) * 0.7:
            emoji_usage = "Sering"
        elif emoji_count > len(user_messages) * 0.3:
            emoji_usage = "Sedang"
        else:
            emoji_usage = "Jarang"
        
        # Analyze message length
        avg_length = sum(len(msg["content"]) for msg in user_messages) / max(
            len(user_messages), 1
        )
        if avg_length > 100:
            message_length = "Panjang"
        elif avg_length > 30:
            message_length = "Sedang"
        else:
            message_length = "Pendek"
        
        # Identify preferred topics
        environmental_keywords = [
            "sampah",
            "lingkungan",
            "daur ulang",
            "kompos",
            "organik",
        ]
        topic_mentions = sum(
            1
            for msg in user_messages
                           for keyword in environmental_keywords 
            if keyword in msg["content"].lower()
        )
        
        if topic_mentions > len(user_messages) * 0.5:
            preferred_topics = "Lingkungan dan sampah"
        else:
            preferred_topics = "Umum"
        
        return {
            "formality": formality,
            "emoji_usage": emoji_usage,
            "message_length": message_length,
            "preferred_topics": preferred_topics,
        }
    
    def _extract_and_save_facts(self, user_phone: str, user_message: str, ai_response: str):
        """Extract and save user facts from conversation"""
        try:
            # Extract user name if mentioned
            if "nama saya" in user_message.lower() or "saya" in user_message.lower():
                # Simple name extraction
                words = user_message.split()
                for i, word in enumerate(words):
                    if word.lower() in ["nama", "saya"] and i + 1 < len(words):
                        name = words[i + 1]
                        if name not in ["adalah", "itu", "ini"]:
                            self.memory_model.save_user_fact(user_phone, "user_name", name)
                            break

            # Extract other facts based on context
            if "tinggal" in user_message.lower() or "lokasi" in user_message.lower():
                if "kampung hijau" in user_message.lower():
                    self.memory_model.save_user_fact(user_phone, "location", "Kampung Hijau")
                elif "rt" in user_message.lower():
                    # Extract RT number
                    import re
                    rt_match = re.search(r'rt\s*(\d+)', user_message.lower())
                    if rt_match:
                        rt_number = rt_match.group(1)
                        self.memory_model.save_user_fact(user_phone, "rt", f"RT {rt_number}")
                
        except Exception as e:
            logger.error(f"Error extracting facts: {str(e)}")
    
    def _fallback_response(self, user_message: str, user_phone: str, mode: str = "hybrid") -> str:
        """Fallback response when AI is not available"""
        try:
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            user_name = user_facts.get("user_name", {}).get("value", "Teman") if user_facts else "Teman"
            
            if mode == "ecobot":
                return f"Halo {user_name}! Maaf, layanan AI EcoBot sedang tidak tersedia. Silakan gunakan command /help untuk melihat fitur yang tersedia."
            elif mode == "general":
                return f"Halo {user_name}! Maaf, layanan AI edukasi sampah sedang tidak tersedia. Silakan gunakan command /help untuk melihat fitur yang tersedia."
            else:
                return f"Halo {user_name}! Maaf, layanan AI sedang tidak tersedia. Silakan gunakan command /help untuk melihat fitur yang tersedia."
        except:
            return "Halo! Maaf, layanan AI sedang tidak tersedia. Silakan gunakan command /help untuk melihat fitur yang tersedia."

    def get_available_modes(self) -> Dict[str, Dict]:
        """Get available AI Agent modes"""
        return self.modes

    def switch_mode(self, user_phone: str, new_mode: str) -> str:
        """Switch AI Agent mode for user"""
        if new_mode in self.modes:
            self.memory_model.save_user_fact(user_phone, "ai_mode", new_mode)
            return f"Mode AI Agent berhasil diubah ke: {self.modes[new_mode]['name']}"
        else:
            return f"Mode '{new_mode}' tidak tersedia. Mode yang tersedia: {', '.join(self.modes.keys())}"
