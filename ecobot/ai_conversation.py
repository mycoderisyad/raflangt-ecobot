"""
AI Conversation Module
Natural language processing untuk chatbot menggunakan Lunos.tech unified API
"""

import os
import logging
import json
import requests
import base64
from datetime import datetime
from utils.message_loader import message_loader

logger = logging.getLogger(__name__)

class AIConversation:
    """AI-powered natural conversation handler using Lunos.tech"""
    
    def __init__(self):
        # Lunos.tech configuration
        self.api_key = os.getenv('LUNOS_API_KEY')
        self.base_url = os.getenv('LUNOS_BASE_URL', 'https://api.lunos.tech/v1')
        self.app_id = os.getenv('LUNOS_APP_ID', 'ecobot-whatsapp-v1.0')
        
        # Model configuration
        self.text_model = os.getenv('LUNOS_TEXT_MODEL', 'openai/gpt-4o-mini')
        self.vision_model = os.getenv('LUNOS_VISION_MODEL', 'openai/gpt-4o')
        
        # Load conversation templates
        self.templates = message_loader.get_whatsapp_messages()
        self.context = self._load_bot_context()
        
        if not self.api_key:
            logger.warning("Lunos API key not found. Using template responses.")
            self.use_ai = False
        else:
            self.use_ai = True
            logger.info("AI Conversation initialized with Lunos.tech")
    
    def _get_available_models(self):
        """Get list of available models from Lunos"""
        try:
            response = requests.get('https://api.lunos.tech/public/models', timeout=10)
            response.raise_for_status()
            models = response.json()
            
            # Filter models by capabilities
            text_models = []
            vision_models = []
            
            for model in models:
                if 'chat' in model.get('capabilities', []):
                    text_models.append(model['id'])
                if 'vision' in model.get('capabilities', []):
                    vision_models.append(model['id'])
            
            logger.info(f"Available text models: {len(text_models)}")
            logger.info(f"Available vision models: {len(vision_models)}")
            
            return text_models, vision_models
        except Exception as e:
            logger.error(f"Error fetching models: {str(e)}")
            return [], []
    
    def _load_bot_context(self):
        """Load bot personality and context"""
        return {
            "name": "EcoBot",
            "role": "Asisten virtual pengelolaan sampah untuk Desa Cukangkawung",
            "personality": "Ramah, informatif, dan peduli lingkungan",
            "capabilities": [
                "Identifikasi jenis sampah dari foto",
                "Memberikan tips pengelolaan sampah",
                "Menunjukkan lokasi titik pengumpulan sampah",
                "Edukasi tentang daur ulang",
                "Informasi jadwal pengumpulan"
            ],
            "knowledge_base": {
                "village": "Desa Cukangkawung",
                "waste_types": ["organik", "anorganik", "B3"],
                "services": ["klasifikasi gambar", "peta lokasi", "edukasi", "tips"]
            }
        }
    
    def generate_response(self, user_message, context_data=None):
        """Generate natural AI response using Lunos"""
        if not self.use_ai:
            return self._fallback_response(user_message)
        
        try:
            system_prompt = self._build_system_prompt(context_data)
            response = self._call_lunos_chat(system_prompt, user_message)
            return response
        except Exception as e:
            logger.error(f"Lunos API error: {str(e)}")
            return self._fallback_response(user_message)
    
    def analyze_image(self, image_data, user_question=None):
        """Analyze image using Lunos vision models"""
        if not self.use_ai:
            return self._fallback_image_response()
        
        try:
            # Convert image to base64 if needed
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_base64 = image_data
            
            # Prepare vision prompt
            system_prompt = """Kamu adalah EcoBot, asisten identifikasi sampah untuk Desa Cukangkawung. 
Analisis gambar yang dikirim user dan identifikasi jenis sampah dengan detail:

1. JENIS SAMPAH: (Organik/Anorganik/B3/Campuran)
2. DESKRIPSI: Jelaskan apa yang terlihat di gambar
3. CARA PENGELOLAAN: Tips khusus untuk mengelola sampah ini
4. LOKASI BUANG: Tempat yang tepat untuk membuang
5. TIPS TAMBAHAN: Saran daur ulang atau pengurangan

Format jawaban dengan ramah dan informatif. Jika tidak yakin, berikan beberapa kemungkinan."""

            user_prompt = user_question or "Tolong identifikasi jenis sampah dalam gambar ini dan berikan tips pengelolaannya."
            
            response = self._call_lunos_vision(system_prompt, user_prompt, image_base64)
            return response
            
        except Exception as e:
            logger.error(f"Lunos Vision API error: {str(e)}")
            return self._fallback_image_response()
    
    def _call_lunos_chat(self, system_prompt, user_message):
        """Call Lunos chat completion API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-App-ID': self.app_id
        }
        
        data = {
            'model': self.text_model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 400,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _call_lunos_vision(self, system_prompt, user_prompt, image_base64):
        """Call Lunos vision API for image analysis"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-App-ID': self.app_id
        }
        
        # Format for vision models (OpenAI-style)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user', 
                'content': [
                    {'type': 'text', 'text': user_prompt},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{image_base64}'
                        }
                    }
                ]
            }
        ]
        
        data = {
            'model': self.vision_model,
            'messages': messages,
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=45
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _build_system_prompt(self, context_data=None):
        """Build system prompt with bot context"""
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

FORMAT GAMBAR YANG DIDUKUNG WhatsApp:
- JPEG, PNG, WebP
- Maksimal 16MB per file
- Resolusi optimal: 640x480 hingga 1600x1200

INSTRUKSI PERILAKU:
1. Selalu ramah, informatif, dan tidak kaku seperti customer service profesional
2. Gunakan bahasa Indonesia yang natural dan mudah dipahami warga desa
3. Jika ditanya tentang layanan di luar kemampuan, arahkan ke layanan yang tersedia
4. Berikan respon yang personal dan praktis
5. Jika user mengirim foto, berikan analisis detail dan tips actionable
6. Selalu akhiri dengan ajakan menggunakan layanan lain atau bertanya lebih lanjut
7. Jika gambar tidak jelas, minta user kirim foto yang lebih terang/jelas

CATATAN: Respon maksimal 4-5 kalimat. Fokus pada advice yang helpful dan bisa langsung diterapkan.
"""
        
        if context_data:
            prompt += f"\nKONTEKS TAMBAHAN: {json.dumps(context_data, ensure_ascii=False)}"
        
        return prompt
    
    def _call_ai_api(self, system_prompt, user_message):
        """Legacy method - now redirects to Lunos"""
        return self._call_lunos_chat(system_prompt, user_message)
    
    def _fallback_image_response(self):
        """Fallback response for image analysis when AI is not available"""
        return """Maaf, layanan analisis gambar sedang tidak tersedia. 
        
Silakan coba lagi nanti atau hubungi petugas desa untuk bantuan identifikasi sampah manual. 

Sementara itu, Anda bisa:
- Ketik 'edukasi' untuk tips umum pengelolaan sampah
- Ketik 'lokasi' untuk info tempat pengumpulan sampah"""
    
    def _fallback_response(self, user_message):
        """Fallback to template responses when AI is not available"""
        message_lower = user_message.lower()
        
        # Simple keyword matching for fallback
        if any(keyword in message_lower for keyword in ['halo', 'hai', 'hello', 'selamat']):
            return "Halo! Saya EcoBot, asisten pengelolaan sampah Desa Cukangkawung. Ada yang bisa saya bantu? Kirim foto sampah untuk identifikasi atau ketik 'help' untuk bantuan."
        
        elif any(keyword in message_lower for keyword in ['lokasi', 'tempat', 'dimana']):
            return "Untuk melihat lokasi titik pengumpulan sampah terdekat, ketik 'lokasi' ya! Saya akan tunjukkan peta dan jadwal pengumpulannya."
        
        elif any(keyword in message_lower for keyword in ['cara', 'tips', 'bagaimana']):
            return "Mau belajar pengelolaan sampah? Ketik 'edukasi' untuk tips lengkap tentang pemilahan dan daur ulang sampah!"
        
        elif any(keyword in message_lower for keyword in ['terima kasih', 'thanks', 'makasih']):
            return "Sama-sama! Senang bisa membantu. Jangan lupa untuk selalu pilah sampah ya. Ada lagi yang ingin ditanyakan?"
        
        else:
            return "Maaf, saya tidak sepenuhnya memahami pertanyaan Anda. Saya bisa membantu identifikasi sampah dari foto, memberikan info lokasi pengumpulan, atau tips pengelolaan sampah. Coba kirim foto sampah atau ketik 'help' untuk bantuan!"
    
    def enhance_service_response(self, service_type, base_response, user_context=None):
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
            
            enhanced = self._call_lunos_chat(enhancement_prompt, "Tolong buat lebih natural")
            return enhanced if enhanced else base_response
        except:
            return base_response
    
    def get_supported_image_formats(self):
        """Get list of image formats supported by WhatsApp and our system"""
        return {
            'supported_formats': ['JPEG', 'PNG', 'WebP'],
            'max_size_mb': 16,
            'recommended_resolution': '640x480 to 1600x1200',
            'note': 'Pastikan foto terang dan jelas untuk hasil analisis terbaik'
        }
