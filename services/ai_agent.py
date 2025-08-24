"""
AI Agent Service - Minimal Version
This is a minimal version for git commit purposes
"""

import logging

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.logger = logger
        self.logger.info("AI Agent initialized (minimal version)")
    
    def process_message(self, message: str, user_phone: str):
        return {
            'status': 'success',
            'reply_sent': 'AI Agent is working! (minimal version)'
        }

def get_ai_agent():
    return AIAgent()
"""
AI Agent Service with Long-Term Memory
Advanced AI agent that can memorize conversations, remember user details, 
and adapt communication style based on user history
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.config import get_config
from database.models.memory_models import get_memory_models
from database.models import UserModel, DatabaseManager

logger = logging.getLogger(__name__)

class AIAgent:
    """AI Agent with long-term memory capabilities"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv('LUNOS_API_KEY')
        self.base_url = os.getenv('LUNOS_BASE_URL')
        self.model = os.getenv('LUNOS_AGENT_MODEL')
        
        # Setup headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize database models
        self.db_manager = DatabaseManager()
        self.user_model = UserModel(self.db_manager)
        self.memory_model, self.conversation_model = get_memory_models()
        
        # Bot personality
        self.personality = {
            "name": "EcoBot",
            "role": "Asisten virtual pengelolaan sampah",
            "traits": [
                "Ramah dan peduli lingkungan",
                "Responsif terhadap kebutuhan pengguna",
                "Mudah diajak berinteraksi",
                "Memberikan informasi yang akurat dan bermanfaat"
            ]
        }
        
        if not self.api_key:
            logger.warning("Lunos API key not found. AI Agent will not function.")
            self.use_ai = False
        else:
            self.use_ai = True
            logger.info(f"AI Agent initialized with model: {self.model}")
    
    def process_message(self, user_message: str, user_phone: str) -> Dict[str, Any]:
        """Process user message with long-term memory capabilities"""
        if not self.use_ai:
            fallback_response = self._fallback_response(user_message)
            return {
                'status': 'success',
                'reply_sent': fallback_response
            }
        
        try:
            # Get user context and memory
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_history = self.conversation_model.get_recent_conversation(user_phone, 20)
            
            # Build comprehensive context
            context = self._build_context(user_phone, user_context, user_facts, conversation_history)
            
            # Generate response
            response = self._generate_response_with_memory(user_message, context)
            
            # Extract and save facts from the conversation
            self._extract_and_save_facts(user_phone, user_message, response)
            
            # Save conversation to history
            self.conversation_model.add_message(user_phone, 'user', user_message)
            self.conversation_model.add_message(user_phone, 'assistant', response)
            
            return {
                'status': 'success',
                'reply_sent': response
            }
            
        except Exception as e:
            logger.error(f"AI Agent error: {str(e)}")
            fallback_response = self._fallback_response(user_message)
            return {
                'status': 'error',
                'reply_sent': fallback_response,
                'error': str(e)
            }
    
    def _get_user_context(self, user_phone: str) -> Dict[str, Any]:
        """Get user context from database"""
        try:
            user = self.user_model.get_user(user_phone)
            if user:
                return {
                    'phone': user_phone,
                    'name': user['name'],
                    'role': user['role'],
                    'registration_status': user['registration_status'],
                    'points': user['points'],
                    'first_seen': user['first_seen'],
                    'last_active': user['last_active'],
                    'total_messages': user['total_messages'],
                    'total_images': user['total_images']
                }
            else:
                return {'phone': user_phone, 'role': 'warga'}
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {'phone': user_phone, 'role': 'warga'}
    
    def _build_context(self, user_phone: str, user_context: Dict, user_facts: Dict, 
                      conversation_history: List[Dict]) -> Dict[str, Any]:
        """Build comprehensive context for the AI agent"""
        return {
            'user_context': user_context,
            'user_facts': user_facts,
            'conversation_history': conversation_history,
            'personality': self.personality,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_response_with_memory(self, user_message: str, context: Dict) -> str:
        """Generate AI response using long-term memory"""
        system_prompt = self._build_system_prompt(context)
        
        # Prepare conversation history for the API
        messages = []
        
        # Add system prompt
        messages.append({'role': 'system', 'content': system_prompt})
        
        # Add recent conversation history
        for msg in context['conversation_history']:
            messages.append({'role': msg['role'], 'content': msg['content']})
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})
        
        data = {
            'model': self.model,
            'messages': messages,
            'max_tokens': 800,
            'temperature': 0.7,
            'presence_penalty': 0.5,
            'frequency_penalty': 0.3
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
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build comprehensive system prompt with memory context"""
        user_context = context['user_context']
        user_facts = context['user_facts']
        conversation_history = context['conversation_history']
        personality = context['personality']
        
        # Analyze user communication style from history
        communication_style = self._analyze_user_style(conversation_history)
        
        prompt = f"""Kamu adalah {personality['name']}, {personality['role']} yang sangat personal dan adaptif.

KEPRIBADIAN INTI:"""
        for trait in personality['traits']:
            prompt += f"\n- {trait}"
        
        prompt += f"""

INFORMASI USER LENGKAP:
- Nomor telepon: {user_context.get('phone', 'Tidak diketahui')}
- Nama: {user_context.get('name', 'Belum dikenali')}
- Role: {user_context.get('role', 'warga')}
- Status registrasi: {user_context.get('registration_status', 'unknown')}
- Poin yang dimiliki: {user_context.get('points', 0)}
- Total interaksi pesan: {user_context.get('total_messages', 0)}
- Total gambar yang dikirim: {user_context.get('total_images', 0)}
- Pertama kali bertemu: {user_context.get('first_seen', 'Hari ini')}
- Terakhir aktif: {user_context.get('last_active', 'Sekarang')}

FAKTA PERSONAL YANG KAMU KETAHUI:"""
        if user_facts:
            for key, value in user_facts.items():
                prompt += f"\n- {key}: {value}"
        else:
            prompt += "\n- Belum ada fakta personal yang diketahui tentang user ini"
        
        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}
- Waktu aktif: {communication_style.get('active_times', 'Belum dianalisis')}

KEMAMPUAN UTAMA & TUGAS:
✅ MEMORY SISTEM:
- Ingat SEMUA detail personal yang user bagikan (nama, alamat, kebiasaan, preferensi, dll)
- Referensikan percakapan sebelumnya secara natural
- Adaptasi respons berdasarkan pola komunikasi user
- Pelajari dan ingat kebiasaan user seputar sampah dan lingkungan

✅ PERSONALISASI:
- Sesuaikan gaya bahasa dengan preferensi user (formal/informal)
- Gunakan nama user jika sudah diketahui
- Berikan saran yang spesifik berdasarkan lokasi/situasi user
- Ingat konteks percakapan sebelumnya

✅ PENGEMBANGAN RELASI:
- Bangun rapport yang natural, bukan seperti customer service
- Tunjukkan ketertarikan genuine pada kehidupan user
- Ajukan pertanyaan follow-up yang relevan
- Celebrasi progress dan achievement user

✅ EXPERTISE LINGKUNGAN:
- Berikan advice pengelolaan sampah yang actionable
- Sesuaikan tips dengan kondisi spesifik user
- Edukasi dengan cara yang engaging dan mudah diingat
- Motivasi user untuk konsisten menerapkan pola hidup ramah lingkungan

PRINSIP KOMUNIKASI WAJIB:
1. 🎯 SELALU referensikan informasi dari percakapan sebelumnya jika relevan
2. 🧠 Tunjukkan bahwa kamu MENGINGAT user dengan menyebut detail yang pernah mereka bagikan
3. 🎨 Adaptasi gaya komunikasi sesuai preferensi user (emoji, formal/informal, panjang respon)
4. 💡 Berikan saran yang PERSONAL dan spesifik, bukan generic
5. 🌱 Fokus pada progress dan improvement yang berkelanjutan
6. ❤️ Tunjukkan empati dan genuine care terhadap user
7. 🎯 Maksimal 4-5 kalimat agar mudah dibaca di WhatsApp
8. 🔄 Selalu akhiri dengan pertanyaan atau ajakan interaksi untuk menjaga engagement

CONTOH PERSONALISASI:
- Jika user pernah menyebut nama → "Halo [Nama], apa kabar?"
- Jika user pernah cerita masalah sampah → "Gimana progress dengan [masalah specific]?"
- Jika user sering kirim foto sampah → "Wah kamu rajin banget klasifikasi sampah!"
- Jika user jarang aktif → "Udah lama gak ngobrol nih, gimana kabarnya?"

PENTING: Kamu bukan bot kaku! Kamu adalah AI companion yang genuinely peduli dengan user dan lingkungan. Tunjukkan personality yang warm, helpful, dan memorable."""
        
        return prompt
    
    def _analyze_user_style(self, conversation_history: List[Dict]) -> Dict[str, str]:
        """Analyze user communication style from conversation history"""
        if not conversation_history:
            return {
                'formality': 'Netral',
                'emoji_usage': 'Jarang',
                'message_length': 'Sedang',
                'preferred_topics': 'Belum teridentifikasi',
                'active_times': 'Belum dianalisis'
            }
        
        user_messages = [msg for msg in conversation_history if msg['role'] == 'user']
        
        # Analyze formality
        formal_indicators = ['terima kasih', 'mohon', 'silakan', 'bapak', 'ibu']
        informal_indicators = ['hai', 'halo', 'gimana', 'oke', 'thanks', 'makasih']
        
        formal_count = sum(1 for msg in user_messages 
                          for indicator in formal_indicators 
                          if indicator in msg['content'].lower())
        informal_count = sum(1 for msg in user_messages 
                            for indicator in informal_indicators 
                            if indicator in msg['content'].lower())
        
        if formal_count > informal_count:
            formality = 'Formal'
        elif informal_count > formal_count:
            formality = 'Informal'
        else:
            formality = 'Netral'
        
        # Analyze emoji usage
        emoji_count = sum(1 for msg in user_messages 
                         if any(ord(char) > 127 for char in msg['content']))
        if emoji_count > len(user_messages) * 0.7:
            emoji_usage = 'Sering'
        elif emoji_count > len(user_messages) * 0.3:
            emoji_usage = 'Sedang'
        else:
            emoji_usage = 'Jarang'
        
        # Analyze message length
        avg_length = sum(len(msg['content']) for msg in user_messages) / max(len(user_messages), 1)
        if avg_length > 100:
            message_length = 'Panjang'
        elif avg_length > 30:
            message_length = 'Sedang'
        else:
            message_length = 'Pendek'
        
        # Identify preferred topics
        environmental_keywords = ['sampah', 'lingkungan', 'daur ulang', 'kompos', 'organik']
        topic_mentions = sum(1 for msg in user_messages 
                           for keyword in environmental_keywords 
                           if keyword in msg['content'].lower())
        
        if topic_mentions > len(user_messages) * 0.5:
            preferred_topics = 'Lingkungan dan sampah'
        else:
            preferred_topics = 'Umum'
        
        return {
            'formality': formality,
            'emoji_usage': emoji_usage,
            'message_length': message_length,
            'preferred_topics': preferred_topics,
            'active_times': 'Belum dianalisis'  # Could be enhanced later
        }
    
    def _extract_and_save_facts(self, user_phone: str, user_message: str, ai_response: str):
        """Extract and save user facts from conversation"""
        try:
            # Create a prompt to extract facts
            extraction_prompt = f"""
Pesan pengguna: "{user_message}"
Respon AI: "{ai_response}"

Berdasarkan percakapan di atas, identifikasi fakta-fakta penting tentang pengguna yang perlu diingat.
Fakta-fakta ini bisa berupa:
- Nama pengguna
- Kebiasaan atau rutinitas
- Preferensi pribadi
- Lokasi spesifik
- Informasi kontak
- Topik yang menarik bagi pengguna

Format output dalam JSON dengan struktur berikut:
{{
    "facts_to_save": {{
        "key1": "value1",
        "key2": "value2"
    }}
}}

Jika tidak ada fakta baru yang perlu disimpan, kembalikan:
{{
    "facts_to_save": {{}}
}}

Hanya kembalikan JSON, tidak perlu penjelasan tambahan.
"""
            
            # Call AI to extract facts
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': 'Kamu adalah sistem ekstraksi fakta. Tugas kamu adalah mengidentifikasi informasi penting tentang pengguna dari percakapan dan mengembalikannya dalam format JSON yang ditentukan.'},
                    {'role': 'user', 'content': extraction_prompt}
                ],
                'max_tokens': 300,
                'temperature': 0.3
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=20
            )
            response.raise_for_status()
            
            result = response.json()
            extracted_json = result['choices'][0]['message']['content'].strip()
            
            # Parse the JSON response
            try:
                # Handle potential markdown code blocks
                if extracted_json.startswith('```'):
                    extracted_json = extracted_json.split('\n', 1)[1].rsplit('\n', 1)[0]
                
                facts_data = json.loads(extracted_json)
                facts_to_save = facts_data.get('facts_to_save', {})
                
                # Save extracted facts
                for key, value in facts_to_save.items():
                    self.memory_model.save_user_fact(user_phone, key, str(value))
                    
            except json.JSONDecodeError:
                logger.warning(f"Could not parse extracted facts JSON: {extracted_json}")
                
        except Exception as e:
            logger.error(f"Error extracting and saving facts: {str(e)}")
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback response when AI is not available"""
        responses = [
            "Maaf, saya sedang sibuk sekarang. Bisakah Anda mencoba lagi nanti?",
            "Saat ini saya tidak dapat memproses permintaan Anda. Silakan coba beberapa saat lagi.",
            "Terjadi kesalahan dalam sistem saya. Mohon maaf atas ketidaknyamanannya."
        ]
        
        import random
        return random.choice(responses)
    
    def get_user_profile(self, user_phone: str) -> Dict[str, Any]:
        """Get comprehensive user profile including memory and conversation history"""
        try:
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_history = self.conversation_model.get_recent_conversation(user_phone, 50)
            
            return {
                'user_info': user_context,
                'known_facts': user_facts,
                'recent_conversations': conversation_history,
                'total_conversations': len(conversation_history)
            }
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {}

# Initialize the AI agent
ai_agent = AIAgent()

def get_ai_agent():
    """Get the global AI agent instance"""
    return ai_agent

class AIAgent:
    """AI Agent with long-term memory capabilities"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv('LUNOS_API_KEY')
        self.base_url = os.getenv('LUNOS_BASE_URL')
        self.model = os.getenv('LUNOS_AGENT_MODEL')
        
        # Setup headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize database models
        self.db_manager = DatabaseManager()
        self.user_model = UserModel(self.db_manager)
        self.memory_model, self.conversation_model = get_memory_models()
        
        # Bot personality
        self.personality = {
            "name": "EcoBot",
            "role": "Asisten virtual pengelolaan sampah",
            "traits": [
                "Ramah dan peduli lingkungan",
                "Responsif terhadap kebutuhan pengguna",
                "Mudah diajak berinteraksi",
                "Memberikan informasi yang akurat dan bermanfaat"
            ]
        }
        
        if not self.api_key:
            logger.warning("Lunos API key not found. AI Agent will not function.")
            self.use_ai = False
        else:
            self.use_ai = True
            logger.info(f"AI Agent initialized with model: {self.model}")
    
    def process_message(self, user_message: str, user_phone: str) -> Dict[str, Any]:
        """Process user message with long-term memory capabilities"""
        if not self.use_ai:
            fallback_response = self._fallback_response(user_message)
            return {
                'status': 'success',
                'reply_sent': fallback_response
            }
        
        try:
            # Get user context and memory
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_history = self.conversation_model.get_recent_conversation(user_phone, 20)
            
            # Build comprehensive context
            context = self._build_context(user_phone, user_context, user_facts, conversation_history)
            
            # Generate response
            response = self._generate_response_with_memory(user_message, context)
            
            # Extract and save facts from the conversation
            self._extract_and_save_facts(user_phone, user_message, response)
            
            # Save conversation to history
            self.conversation_model.add_message(user_phone, 'user', user_message)
            self.conversation_model.add_message(user_phone, 'assistant', response)
            
            return {
                'status': 'success',
                'reply_sent': response
            }
            
        except Exception as e:
            logger.error(f"AI Agent error: {str(e)}")
            fallback_response = self._fallback_response(user_message)
            return {
                'status': 'error',
                'reply_sent': fallback_response,
                'error': str(e)
            }
    
    def _get_user_context(self, user_phone: str) -> Dict[str, Any]:
        """Get user context from database"""
        try:
            user = self.user_model.get_user(user_phone)
            if user:
                return {
                    'phone': user_phone,
                    'name': user['name'],
                    'role': user['role'],
                    'registration_status': user['registration_status'],
                    'points': user['points'],
                    'first_seen': user['first_seen'],
                    'last_active': user['last_active'],
                    'total_messages': user['total_messages'],
                    'total_images': user['total_images']
                }
            else:
                return {'phone': user_phone, 'role': 'warga'}
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {'phone': user_phone, 'role': 'warga'}
    
    def _build_context(self, user_phone: str, user_context: Dict, user_facts: Dict, 
                      conversation_history: List[Dict]) -> Dict[str, Any]:
        """Build comprehensive context for the AI agent"""
        return {
            'user_context': user_context,
            'user_facts': user_facts,
            'conversation_history': conversation_history,
            'personality': self.personality,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_response_with_memory(self, user_message: str, context: Dict) -> str:
        """Generate AI response using long-term memory"""
        system_prompt = self._build_system_prompt(context)
        
        # Prepare conversation history for the API
        messages = []
        
        # Add system prompt
        messages.append({'role': 'system', 'content': system_prompt})
        
        # Add recent conversation history
        for msg in context['conversation_history']:
            messages.append({'role': msg['role'], 'content': msg['content']})
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})
        
        data = {
            'model': self.model,
            'messages': messages,
            'max_tokens': 800,
            'temperature': 0.7,
            'presence_penalty': 0.5,
            'frequency_penalty': 0.3
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
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build comprehensive system prompt with memory context"""
        user_context = context['user_context']
        user_facts = context['user_facts']
        conversation_history = context['conversation_history']
        personality = context['personality']
        
        # Analyze user communication style from history
        communication_style = self._analyze_user_style(conversation_history)
        
        prompt = f"""Kamu adalah {personality['name']}, {personality['role']} yang sangat personal dan adaptif.

KEPRIBADIAN INTI:"""
        for trait in personality['traits']:
            prompt += f"\n- {trait}"
        
        prompt += f"""

INFORMASI USER LENGKAP:
- Nomor telepon: {user_context.get('phone', 'Tidak diketahui')}
- Nama: {user_context.get('name', 'Belum dikenali')}
- Role: {user_context.get('role', 'warga')}
- Status registrasi: {user_context.get('registration_status', 'unknown')}
- Poin yang dimiliki: {user_context.get('points', 0)}
- Total interaksi pesan: {user_context.get('total_messages', 0)}
- Total gambar yang dikirim: {user_context.get('total_images', 0)}
- Pertama kali bertemu: {user_context.get('first_seen', 'Hari ini')}
- Terakhir aktif: {user_context.get('last_active', 'Sekarang')}

FAKTA PERSONAL YANG KAMU KETAHUI:"""
        if user_facts:
            for key, value in user_facts.items():
                prompt += f"\n- {key}: {value}"
        else:
            prompt += "\n- Belum ada fakta personal yang diketahui tentang user ini"
        
        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}
- Waktu aktif: {communication_style.get('active_times', 'Belum dianalisis')}

KEMAMPUAN UTAMA & TUGAS:
✅ MEMORY SISTEM:
- Ingat SEMUA detail personal yang user bagikan (nama, alamat, kebiasaan, preferensi, dll)
- Referensikan percakapan sebelumnya secara natural
- Adaptasi respons berdasarkan pola komunikasi user
- Pelajari dan ingat kebiasaan user seputar sampah dan lingkungan

✅ PERSONALISASI:
- Sesuaikan gaya bahasa dengan preferensi user (formal/informal)
- Gunakan nama user jika sudah diketahui
- Berikan saran yang spesifik berdasarkan lokasi/situasi user
- Ingat konteks percakapan sebelumnya

✅ PENGEMBANGAN RELASI:
- Bangun rapport yang natural, bukan seperti customer service
- Tunjukkan ketertarikan genuine pada kehidupan user
- Ajukan pertanyaan follow-up yang relevan
- Celebrasi progress dan achievement user

✅ EXPERTISE LINGKUNGAN:
- Berikan advice pengelolaan sampah yang actionable
- Sesuaikan tips dengan kondisi spesifik user
- Edukasi dengan cara yang engaging dan mudah diingat
- Motivasi user untuk konsisten menerapkan pola hidup ramah lingkungan

PRINSIP KOMUNIKASI WAJIB:
1. 🎯 SELALU referensikan informasi dari percakapan sebelumnya jika relevan
2. 🧠 Tunjukkan bahwa kamu MENGINGAT user dengan menyebut detail yang pernah mereka bagikan
3. 🎨 Adaptasi gaya komunikasi sesuai preferensi user (emoji, formal/informal, panjang respon)
4. 💡 Berikan saran yang PERSONAL dan spesifik, bukan generic
5. 🌱 Fokus pada progress dan improvement yang berkelanjutan
6. ❤️ Tunjukkan empati dan genuine care terhadap user
7. 🎯 Maksimal 4-5 kalimat agar mudah dibaca di WhatsApp
8. 🔄 Selalu akhiri dengan pertanyaan atau ajakan interaksi untuk menjaga engagement

CONTOH PERSONALISASI:
- Jika user pernah menyebut nama → "Halo [Nama], apa kabar?"
- Jika user pernah cerita masalah sampah → "Gimana progress dengan [masalah specific]?"
- Jika user sering kirim foto sampah → "Wah kamu rajin banget klasifikasi sampah!"
- Jika user jarang aktif → "Udah lama gak ngobrol nih, gimana kabarnya?"

PENTING: Kamu bukan bot kaku! Kamu adalah AI companion yang genuinely peduli dengan user dan lingkungan. Tunjukkan personality yang warm, helpful, dan memorable."""
        
        return prompt
    
    def _analyze_user_style(self, conversation_history: List[Dict]) -> Dict[str, str]:
        """Analyze user communication style from conversation history"""
        if not conversation_history:
            return {
                'formality': 'Netral',
                'emoji_usage': 'Jarang',
                'message_length': 'Sedang',
                'preferred_topics': 'Belum teridentifikasi',
                'active_times': 'Belum dianalisis'
            }
        
        user_messages = [msg for msg in conversation_history if msg['role'] == 'user']
        
        # Analyze formality
        formal_indicators = ['terima kasih', 'mohon', 'silakan', 'bapak', 'ibu']
        informal_indicators = ['hai', 'halo', 'gimana', 'oke', 'thanks', 'makasih']
        
        formal_count = sum(1 for msg in user_messages 
                          for indicator in formal_indicators 
                          if indicator in msg['content'].lower())
        informal_count = sum(1 for msg in user_messages 
                            for indicator in informal_indicators 
                            if indicator in msg['content'].lower())
        
        if formal_count > informal_count:
            formality = 'Formal'
        elif informal_count > formal_count:
            formality = 'Informal'
        else:
            formality = 'Netral'
        
        # Analyze emoji usage
        emoji_count = sum(1 for msg in user_messages 
                         if any(ord(char) > 127 for char in msg['content']))
        if emoji_count > len(user_messages) * 0.7:
            emoji_usage = 'Sering'
        elif emoji_count > len(user_messages) * 0.3:
            emoji_usage = 'Sedang'
        else:
            emoji_usage = 'Jarang'
        
        # Analyze message length
        avg_length = sum(len(msg['content']) for msg in user_messages) / max(len(user_messages), 1)
        if avg_length > 100:
            message_length = 'Panjang'
        elif avg_length > 30:
            message_length = 'Sedang'
        else:
            message_length = 'Pendek'
        
        # Identify preferred topics
        environmental_keywords = ['sampah', 'lingkungan', 'daur ulang', 'kompos', 'organik']
        topic_mentions = sum(1 for msg in user_messages 
                           for keyword in environmental_keywords 
                           if keyword in msg['content'].lower())
        
        if topic_mentions > len(user_messages) * 0.5:
            preferred_topics = 'Lingkungan dan sampah'
        else:
            preferred_topics = 'Umum'
        
        return {
            'formality': formality,
            'emoji_usage': emoji_usage,
            'message_length': message_length,
            'preferred_topics': preferred_topics,
            'active_times': 'Belum dianalisis'  # Could be enhanced later
        }
    
    def _extract_and_save_facts(self, user_phone: str, user_message: str, ai_response: str):
        """Extract and save user facts from conversation"""
        try:
            # Create a prompt to extract facts
            extraction_prompt = f"""
Pesan pengguna: "{user_message}"
Respon AI: "{ai_response}"

Berdasarkan percakapan di atas, identifikasi fakta-fakta penting tentang pengguna yang perlu diingat.
Fakta-fakta ini bisa berupa:
- Nama pengguna
- Kebiasaan atau rutinitas
- Preferensi pribadi
- Lokasi spesifik
- Informasi kontak
- Topik yang menarik bagi pengguna

Format output dalam JSON dengan struktur berikut:
{{
    "facts_to_save": {{
        "key1": "value1",
        "key2": "value2"
    }}
}}

Jika tidak ada fakta baru yang perlu disimpan, kembalikan:
{{
    "facts_to_save": {{}}
}}

Hanya kembalikan JSON, tidak perlu penjelasan tambahan.
"""
            
            # Call AI to extract facts
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': 'Kamu adalah sistem ekstraksi fakta. Tugas kamu adalah mengidentifikasi informasi penting tentang pengguna dari percakapan dan mengembalikannya dalam format JSON yang ditentukan.'},
                    {'role': 'user', 'content': extraction_prompt}
                ],
                'max_tokens': 300,
                'temperature': 0.3
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=20
            )
            response.raise_for_status()
            
            result = response.json()
            extracted_json = result['choices'][0]['message']['content'].strip()
            
            # Parse the JSON response
            try:
                # Handle potential markdown code blocks
                if extracted_json.startswith('```'):
                    extracted_json = extracted_json.split('\n', 1)[1].rsplit('\n', 1)[0]
                
                facts_data = json.loads(extracted_json)
                facts_to_save = facts_data.get('facts_to_save', {})
                
                # Save extracted facts
                for key, value in facts_to_save.items():
                    self.memory_model.save_user_fact(user_phone, key, str(value))
                    
            except json.JSONDecodeError:
                logger.warning(f"Could not parse extracted facts JSON: {extracted_json}")
                
        except Exception as e:
            logger.error(f"Error extracting and saving facts: {str(e)}")
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback response when AI is not available"""
        responses = [
            "Maaf, saya sedang sibuk sekarang. Bisakah Anda mencoba lagi nanti?",
            "Saat ini saya tidak dapat memproses permintaan Anda. Silakan coba beberapa saat lagi.",
            "Terjadi kesalahan dalam sistem saya. Mohon maaf atas ketidaknyamanannya."
        ]
        
        import random
        return random.choice(responses)
    
    def get_user_profile(self, user_phone: str) -> Dict[str, Any]:
        """Get comprehensive user profile including memory and conversation history"""
        try:
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_history = self.conversation_model.get_recent_conversation(user_phone, 50)
            
            return {
                'user_info': user_context,
                'known_facts': user_facts,
                'recent_conversations': conversation_history,
                'total_conversations': len(conversation_history)
            }
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {}

# Initialize the AI agent
ai_agent = AIAgent()

def get_ai_agent():
    """Get the global AI agent instance"""
    return ai_agent