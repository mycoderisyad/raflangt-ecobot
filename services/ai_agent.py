import os
import json
import logging
import requests
import random
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
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv("LUNOS_API_KEY")
        self.base_url = os.getenv("LUNOS_BASE_URL")
        self.model = os.getenv("LUNOS_AGENT_MODE")
        
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

    # ----------------------
    # Friendly identity helpers
    # ----------------------
    def _generate_alias(self, user_phone: str) -> str:
        """Create a stable friendly alias based on phone digits.

        Example: '62XXXXXXXXXX@c.us' -> 'soeco1234' (last 4 digits).
        """
        digits = "".join(c for c in (user_phone or "") if c.isdigit())
        tail = digits[-4:] or "0000"
        return f"soeco{tail}"

    def _get_display_name(self, user_phone: str, user_context: Dict[str, Any], user_facts: Dict[str, Any]) -> str:
        """Resolve a friendly display name with fallbacks and memory.

        Preference order:
        1) Explicit user name in DB (non-empty and not placeholder)
        2) Remembered fact 'user_name'
        3) Remembered alias 'user_alias'
        4) Generate alias 'soecoXXXX' (saved to memory)
        """
        # 1) DB/user context name
        ctx_name = (user_context or {}).get("name")
        if ctx_name and str(ctx_name).strip().lower() not in ("teman", "belum dikenali", "none", "null"):
            return str(ctx_name).strip()

        # 2) Memory user_name
        fact_name = (user_facts or {}).get("user_name", {}).get("value") if user_facts else None
        if fact_name and str(fact_name).strip().lower() not in ("none", "null"):
            return str(fact_name).strip()

        # 3) Existing alias
        fact_alias = (user_facts or {}).get("user_alias", {}).get("value") if user_facts else None
        if fact_alias:
            return str(fact_alias).strip()

        # 4) Generate + persist alias
        alias = self._generate_alias(user_phone)
        try:
            self.memory_model.save_user_fact(user_phone, "user_alias", alias)
        except Exception:
            pass
        return alias
    
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
                user_phone, 50  # Increased to 50 conversations for better memory
            )

            # Respect previously saved AI mode preference
            try:
                saved_mode = user_facts.get("ai_mode", {}).get("value") if user_facts else None
                if saved_mode in self.modes:
                    mode = saved_mode
            except Exception:
                pass

            # Prefer saved user_name/alias if profile name is unknown or None
            try:
                raw_name = user_context.get("name")
                if (
                    not raw_name
                    or str(raw_name).strip().lower() in ("teman", "belum dikenali", "none", "null")
                ):
                    display_name = self._get_display_name(user_phone, user_context, user_facts)
                    user_context["name"] = display_name
            except Exception:
                pass

            # Build comprehensive context based on mode
            context = self._build_context(
                user_phone, user_context, user_facts, conversation_history, mode
            )

            # Database-first short-circuit for layanan-ecobot
            lowered = user_message.lower()
            db_data_prefetch: Dict[str, Any] = self._get_database_data(user_message)
            if mode == "ecobot" and (
                (db_data_prefetch.get("collection_points") or db_data_prefetch.get("schedules"))
            ):
                direct_response = self._format_db_response(db_data_prefetch, lowered)
                # Append required tail via post-process
                direct_response = self._apply_mode_rules_postprocess(
                    mode=mode,
                    response=direct_response,
                    user_message=user_message,
                    db_data=db_data_prefetch,
                )
                # Save conversation and return early
                try:
                    self.conversation_model.add_message(user_phone, "user", user_message)
                    self.conversation_model.add_message(user_phone, "assistant", direct_response)
                except Exception:
                    pass
                return {"status": "success", "reply_sent": direct_response}

            # Generate response based on mode
            if mode == "ecobot":
                response = self._generate_ecobot_response(user_message, context)
            elif mode == "general":
                response = self._generate_general_response(user_message, context)
            else:  # hybrid mode
                response = self._generate_hybrid_response(user_message, context)

            # Enforce EcoBotModesPrompt business rules post-processing
            try:
                response = self._apply_mode_rules_postprocess(
                    mode=mode,
                    response=response,
                    user_message=user_message,
                    db_data=self._get_database_data(user_message),
                )
            except Exception as _:
                # If post-processing fails, use the raw response
                pass
            
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
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            user_name = self._get_display_name(user_phone, user_context, user_facts)

            # Analyze the image using image analysis service
            analysis_result = self.image_analyzer.analyze_waste_image(
                image_data, user_phone
            )

            if analysis_result.get("success"):
                waste_type = analysis_result.get("waste_type", "TIDAK_TERIDENTIFIKASI")
                confidence = analysis_result.get("confidence", 0.0)
                description = analysis_result.get("description", "")
                tips = analysis_result.get("tips", "")

                # Build a more human greeting and tone
                greeting = f"Halo {user_name}! "

                # Slightly varied encouragement to feel less robotic
                random.seed(f"{user_name}-{waste_type}")  # stable per user/type
                if waste_type == "ORGANIK":
                    encouragement = random.choice([
                        "Mantap! Sampah organik bisa jadi kompos lho.",
                        "Keren—ini cocok buat kompos di rumah!",
                        "Nice! Bahan organik, gampang diolah jadi kompos.",
                    ]) + " "
                elif waste_type == "ANORGANIK":
                    encouragement = random.choice([
                        "Sip! Jangan lupa pisahkan untuk didaur ulang, ya.",
                        "Oke! Ini bisa dikumpulkan untuk recycling.",
                        "Baik! Pisahkan bersih-bersih dulu sebelum didaur ulang.",
                    ]) + " "
                elif waste_type == "B3":
                    encouragement = random.choice([
                        "Perhatian ya—ini termasuk B3, perlu penanganan khusus.",
                        "Hati-hati, ini B3. Simpan terpisah dan serahkan ke fasilitas khusus.",
                        "Ini kategori B3. Jangan dibuang sembarangan, ya.",
                    ]) + " "
                else:
                    encouragement = random.choice([
                        "Kita cek bareng, ya. Jenisnya belum jelas.",
                        "Hmm… belum 100% jelas. Yuk kita pelajari bareng.",
                        "Menarik—belum teridentifikasi. Coba kirim angle lain kalau bisa.",
                    ]) + " "

                # Format confidence as percentage
                confidence_percent = int(confidence * 100)

                response = f"""{greeting}{encouragement}

*HASIL IDENTIFIKASI:*
• *Jenis Sampah:* {waste_type}
• *Tingkat Keyakinan:* {confidence_percent}%
• *Yang Terdeteksi:* {description}

*Tips Pengelolaan:*
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
        """Get comprehensive user context including memory and conversation history"""
        try:
            user = self.user_model.get_user(user_phone)
            
            # Get conversation summary and topics
            conversation_summary = self.conversation_model.get_conversation_summary(user_phone, 7)
            conversation_topics = self.conversation_model.get_conversation_topics(user_phone, 10)
            conversation_count = self.conversation_model.get_conversation_count(user_phone)
            
            if user:
                return {
                    "phone": user_phone,
                    "name": user.get("name", "Teman"),
                    "role": user.get("role", "warga"),
                    "registration_status": user.get("registration_status", "registered"),
                    "points": user.get("points", 0),
                    "first_seen": user.get("first_seen"),
                    "last_active": user.get("last_active"),
                    "total_messages": user.get("total_messages", 0),
                    "total_images": user.get("total_images", 0),
                    "conversation_count": conversation_count,
                    "recent_activity": conversation_summary,
                    "common_topics": conversation_topics
                }
            else:
                return {
                    "phone": user_phone,
                    "role": "warga",
                    "name": "Belum dikenali",
                    "registration_status": "unknown",
                    "points": 0,
                    "first_seen": None,
                    "last_active": None,
                    "total_messages": 0,
                    "total_images": 0,
                    "conversation_count": conversation_count,
                    "recent_activity": conversation_summary,
                    "common_topics": conversation_topics
                }
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {"phone": user_phone, "role": "warga", "name": "Teman"}
    
    def _build_context(self, user_phone: str, user_context: Dict, user_facts: Dict, 
                      conversation_history: List[Dict], mode: str) -> Dict[str, Any]:
        """Build comprehensive context for the AI agent with enhanced memory"""
        
        # Get conversation summary/topics once (reuse if already present in user_context)
        conversation_summary = (
            user_context.get("recent_activity")
            if isinstance(user_context, dict) and user_context.get("recent_activity")
            else self.conversation_model.get_conversation_summary(user_phone, 7)
        )
        conversation_topics = (
            user_context.get("common_topics")
            if isinstance(user_context, dict) and user_context.get("common_topics")
            else self.conversation_model.get_conversation_topics(user_phone, 10)
        )
        
        # Build enhanced context
        context = {
            "user_context": user_context,
            "user_facts": user_facts,
            "conversation_history": conversation_history,
            "conversation_summary": conversation_summary,
            "conversation_topics": conversation_topics,
            "personality": self.personality,
            "mode": self.modes.get(mode, self.modes["hybrid"]),
            "timestamp": datetime.now().isoformat(),
            "memory_enhancement": {
                "total_conversations": len(conversation_history),
                "recent_activity": conversation_summary,
                "common_topics": conversation_topics,
                "user_preferences": self._extract_user_preferences(user_facts),
                "conversation_patterns": self._analyze_conversation_patterns(conversation_history)
            }
        }
        
        return context

    def _generate_ecobot_response(self, user_message: str, context: Dict) -> str:
        """Generate response for EcoBot service mode (database-focused)"""
        # Get database data for specific queries
        db_data = self._get_database_data(user_message)
        system_prompt = self._build_ecobot_system_prompt(context, db_data)

        messages = self._build_messages_with_history(
            system_prompt, context.get("conversation_history", []), user_message
        )
        return self._call_lunos_api(messages)

    def _generate_general_response(self, user_message: str, context: Dict) -> str:
        """Generate response for general waste management mode"""
        system_prompt = self._build_general_system_prompt(context)
        messages = self._build_messages_with_history(
            system_prompt, context.get("conversation_history", []), user_message
        )
        return self._call_lunos_api(messages)

    def _generate_hybrid_response(self, user_message: str, context: Dict) -> str:
        """Generate response for hybrid mode (database + general knowledge)"""
        # Get database data for specific queries
        db_data = self._get_database_data(user_message)
        system_prompt = self._build_hybrid_system_prompt(context, db_data)

        messages = self._build_messages_with_history(
            system_prompt, context.get("conversation_history", []), user_message
        )
        return self._call_lunos_api(messages)

    def _build_messages_with_history(
        self, system_prompt: str, conversation_history: List[Dict], latest_user_message: str
    ) -> List[Dict[str, str]]:
        """Compose messages for the LLM including recent conversation history.

        We include the last few exchanges to provide continuity and personalization
        while keeping token usage under control.
        """
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Adaptive character budget for history (rough token proxy)
        max_chars = 4000  # adjustable
        used_chars = 0

        # iterate newest-first and cap by char budget
        safe_history = conversation_history[::-1] if conversation_history else []
        limited_history: List[Dict[str, str]] = []
        for msg in safe_history:
            role = msg.get("role")
            content = msg.get("content")
            if role in ("user", "assistant") and content:
                inc = len(content)
                if used_chars + inc > max_chars:
                    break
                used_chars += inc
                limited_history.append({"role": role, "content": content})

        # add back in chronological order
        for msg in reversed(limited_history):
            messages.append(msg)

        messages.append({"role": "user", "content": latest_user_message})
        return messages

    def _get_database_data(self, user_message: str) -> Dict[str, Any]:
        """Extract relevant data from database based on user message"""
        data: Dict[str, Any] = {"collection_points": [], "schedules": []}

        try:
            lowered = user_message.lower()

            # Location: collection_points
            if any(word in lowered for word in ["lokasi", "bank sampah", "tempat sampah", "dimana", "mana", "location", "maps", "peta"]):
                cp_query_fields = (
                    "id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description"
                )
                cp_query_active = (
                    f"SELECT {cp_query_fields} FROM collection_points WHERE is_active = 1"
                )
                cp_rows = self.db_manager.execute_query(cp_query_active)
                if not cp_rows:
                    cp_query_all = f"SELECT {cp_query_fields} FROM collection_points"
                    cp_rows = self.db_manager.execute_query(cp_query_all)
                # Normalize to list[dict]
                cp_list = [dict(r) for r in (cp_rows or [])]
                data["collection_points"] = cp_list
                try:
                    logger.info(f"Found {len(cp_list)} collection_points")
                except Exception:
                    pass

            # Schedule: collection_schedules
            if any(word in lowered for word in ["jadwal", "kapan", "waktu", "pengumpulan", "schedule"]):
                sch_fields = (
                    "id, location_name, address, schedule_day, schedule_time, waste_types, contact"
                )
                sch_query_active = (
                    f"SELECT {sch_fields} FROM collection_schedules WHERE is_active = 1"
                )
                sch_rows = self.db_manager.execute_query(sch_query_active)
                if not sch_rows:
                    sch_query_all = f"SELECT {sch_fields} FROM collection_schedules"
                    sch_rows = self.db_manager.execute_query(sch_query_all)
                sch_list = [dict(r) for r in (sch_rows or [])]
                data["schedules"] = sch_list
                try:
                    logger.info(f"Found {len(sch_list)} schedules")
                except Exception:
                    pass

            # Optional: lightweight stats to enrich hybrid/ecobot answers
            if any(word in lowered for word in ["statistik", "data", "aktivitas", "report"]):
                result = self.db_manager.execute_query(
                    "SELECT COUNT(*) as total_users, SUM(points) as total_points FROM users WHERE is_active = 1"
                )
                data["statistics"] = result[0] if result else None

            if any(word in lowered for word in ["klasifikasi", "jenis sampah", "analisis"]):
                result = self.db_manager.execute_query(
                    "SELECT waste_type, COUNT(*) as count FROM waste_classifications GROUP BY waste_type"
                )
                data["waste_analysis"] = result

        except Exception as e:
            logger.error(f"Error getting database data: {str(e)}")

        return data

    def _format_db_response(self, db_data: Dict[str, Any], lowered_message: str) -> str:
        """Compose a deterministic reply from database rows for layanan-ecobot."""
        parts: List[str] = []

        cps = db_data.get("collection_points") or []
        sch = db_data.get("schedules") or []

        if cps:
            parts.append("Bank Sampah / Titik Pengumpulan:")
            for idx, row in enumerate(cps[:5], start=1):
                try:
                    name = row.get('name')
                    ctype = row.get('type')
                    lat = row.get('latitude')
                    lng = row.get('longitude')
                    accepted = row.get('accepted_waste_types')
                    schedule = row.get('schedule')
                    contact = row.get('contact') or '-'
                    desc = row.get('description') or ''

                    item_lines = [
                        f"{idx}. {name} ({ctype})",
                        f"   - Lokasi: {lat}, {lng}",
                        f"   - Diterima: {accepted}",
                        f"   - Jadwal: {schedule}",
                        f"   - Kontak: {contact}",
                    ]
                    if desc:
                        item_lines.append(f"   - Catatan: {desc}")
                    parts.append("\n".join(item_lines))
                except Exception:
                    continue

        if sch:
            parts.append("")
            parts.append("Jadwal Pengumpulan:")
            for idx, row in enumerate(sch[:5], start=1):
                try:
                    loc = row.get('location_name')
                    addr = row.get('address')
                    day = row.get('schedule_day')
                    time = row.get('schedule_time')
                    types = row.get('waste_types')
                    contact = row.get('contact') or '-'
                    parts.append(
                        "\n".join(
                            [
                                f"{idx}. {loc}",
                                f"   - Alamat: {addr}",
                                f"   - Waktu: {day} {time}",
                                f"   - Jenis: {types}",
                                f"   - Kontak: {contact}",
                            ]
                        )
                    )
                except Exception:
                    continue

        if not parts:
            return "Maaf, data belum tersedia di database EcoBot."

        return "\n".join(parts).strip()

    def _call_lunos_api(self, messages: List[Dict]) -> str:
        """Call Lunos API for response generation"""
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.7,
        }

        # Robust retry with exponential backoff to handle transient network errors (e.g., ECONNRESET)
        max_retries = 3
        backoff_seconds = 1.5

        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=30,
                )
                response.raise_for_status()

                # Be defensive when parsing provider response
                result = response.json()
                try:
                    content = (
                        result
                        .get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    if not content:
                        raise KeyError("content")
                    return str(content).strip()
                except Exception as parse_error:
                    logger.error(f"Lunos response parse error: {parse_error}; raw={result}")
                    return "Maaf, sistem AI sedang tidak bisa memproses jawaban. Coba lagi sebentar ya."

            except requests.exceptions.RequestException as req_error:
                # Save and retry on transient errors
                last_error = req_error
                logger.error(
                    f"Lunos API request failed (attempt {attempt}/{max_retries}): {req_error}"
                )
                if attempt < max_retries:
                    import time
                    time.sleep(backoff_seconds * attempt)
                    continue
            except Exception as unexpected_error:
                last_error = unexpected_error
                logger.error(f"Unexpected error calling Lunos API: {unexpected_error}")
                break

        # If we reach here, all retries failed
        raise RuntimeError(
            f"Failed to call Lunos API after {max_retries} attempts: {last_error}"
        )

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
                try:
                    prompt += (
                        f"\n- {point.get('name')} tipe {point.get('type')} "
                        f"(Koordinat: {point.get('latitude')}, {point.get('longitude')})"
                    )
                except Exception:
                    continue

        if db_data.get("schedules"):
            prompt += "\n\nJADWAL PENGUMPULAN:"
            for schedule in db_data["schedules"]:
                try:
                    prompt += (
                        f"\n- {schedule.get('location_name')} ("
                        f"{schedule.get('schedule_day')} {schedule.get('schedule_time')}) "
                        f"untuk {schedule.get('waste_types')}"
                    )
                except Exception:
                    continue

        if db_data.get("statistics"):
            try:
                stats = db_data["statistics"]
                prompt += (
                    f"\n\nSTATISTIK: Total {stats.get('total_users', 0)} user aktif "
                    f"dengan {stats.get('total_points', 0)} total poin"
                )
            except Exception:
                pass
        
        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}

INSTRUKSI KHUSUS:
1. PRIORITY: Database terlebih dahulu (Database first).
2. Jika database ada datanya, tampilkan langsung (jangan minta user ulangi lokasi).
3. Jika data tersedia di database, jawab sesuai data tersebut.
4. Jika database kosong, jawab singkat dan ramah lalu arahkan ke /general-ecobot atau /hybrid-ecobot.
5. Fokus pada fitur EcoBot: lokasi, jadwal, poin, statistik.
6. Jangan memberikan informasi umum panjang bila data tidak ada; cukup ringkas + arahkan.
7. Gunakan nama user jika tersedia dan batasi 3-4 kalimat.

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

PENTING: Kamu adalah asisten EcoBot yang memberikan informasi spesifik dari database dengan personalisasi tinggi.

Tambahkan kalimat penutup: yang natural, sopan dan ramah serta singkat.
"""

        return prompt

    def _build_general_system_prompt(self, context: Dict) -> str:
        """Build system prompt for general waste management mode"""
        user_context = context["user_context"]
        user_facts = context["user_facts"]
        conversation_history = context["conversation_history"]
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
1. PRIORITY: AI domain knowledge terlebih dahulu (AI first).
2. Berikan edukasi umum tentang pengelolaan sampah.
3. Jika pertanyaan berkaitan dengan database EcoBot (lokasi, jadwal, collection point), jawab singkat secara umum lalu arahkan user untuk beralih ke mode /layanan-ecobot agar mendapat jawaban detail.
4. Jika pertanyaan tidak berkaitan dengan database, jawab normal tanpa mengarahkan user ke mode lain.
5. Gunakan nama user jika tersedia. Respons natural dan edukatif.

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
                try:
                    prompt += (
                        f"\n- {point.get('name')} tipe {point.get('type')} "
                        f"(Koordinat: {point.get('latitude')}, {point.get('longitude')})"
                    )
                except Exception:
                    continue

        if db_data.get("schedules"):
            prompt += "\n\nJADWAL PENGUMPULAN:"
            for schedule in db_data["schedules"]:
                try:
                    prompt += (
                        f"\n- {schedule.get('location_name')} ("
                        f"{schedule.get('schedule_day')} {schedule.get('schedule_time')}) "
                        f"untuk {schedule.get('waste_types')}"
                    )
                except Exception:
                    continue

        prompt += f"""

ANALISIS GAYA KOMUNIKASI USER:
- Formalitas: {communication_style.get('formality', 'Netral')}
- Penggunaan emoji: {communication_style.get('emoji_usage', 'Jarang')}
- Panjang pesan: {communication_style.get('message_length', 'Sedang')}
- Topik favorit: {communication_style.get('preferred_topics', 'Belum teridentifikasi')}

INSTRUKSI KHUSUS:
1. PRIORITY: Database terlebih dahulu, lalu AI sebagai fallback.
2. Jika pertanyaan user sesuai data di database, jawab berdasarkan database sesuai role akses.
3. Jika data tidak tersedia di database, gunakan pengetahuan AI untuk menjawab.
4. Kombinasikan informasi database + pengetahuan umum sesuai kebutuhan.
5. Tambahkan konfirmasi di akhir jawaban: "Apakah informasi ini membantu? Jika ingin lokasi lain, silakan sebutkan tempat tinggal Anda".
6. Respons natural dan informatif.

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

    def _is_db_related(self, user_message: str) -> bool:
        """Detect if a message is about EcoBot database topics."""
        lowered = user_message.lower()
        keywords = [
            "lokasi",
            "bank sampah",
            "collection point",
            "titik",
            "peta",
            "maps",
            "jadwal",
            "waktu",
            "pengumpulan",
        ]
        return any(word in lowered for word in keywords)

    def _apply_mode_rules_postprocess(
        self,
        mode: str,
        response: str,
        user_message: str,
        db_data: Dict[str, Any],
    ) -> str:
        """Apply deterministic business rules to the LLM response per mode.

        This ensures required endings and guidance regardless of model behavior.
        """
        safe_response = (response or "").strip()

        if mode == "ecobot":
            # No tail in layanan-ecobot as requested; only guidance when data missing
            if self._is_db_related(user_message) and not any(
                key in db_data for key in ("collection_points", "schedules", "statistics")
            ):
                guidance = (
                    "Data yang kamu minta belum tersedia di database EcoBot. "
                    "Kamu bisa tetap bertanya dengan mode /hybrid-ecobot atau /general-ecobot untuk jawaban umum."
                )
                safe_response = f"{guidance}\n\n{safe_response}" if safe_response else guidance
            return safe_response

        if mode == "general":
            if self._is_db_related(user_message):
                notice = (
                    "Untuk detail lokasi/jadwal dari database EcoBot, silakan gunakan mode /layanan-ecobot."
                )
                if notice not in safe_response:
                    safe_response = f"{safe_response}\n\n{notice}".strip()
            return safe_response

        # hybrid
        confirm = (
            "Apakah informasi ini membantu? Jika ingin lokasi lain, silakan sebutkan tempat tinggal Anda"
        )
        if confirm not in safe_response:
            safe_response = f"{safe_response}\n\n{confirm}".strip()
        return safe_response
    
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
            
            # Extract conversation patterns
            if len(user_message) > 10:
                # Save conversation style preference
                if "?" in user_message:
                    self.memory_model.save_user_fact(user_phone, "conversation_style", "questioner")
                elif len(user_message) > 50:
                    self.memory_model.save_user_fact(user_phone, "conversation_style", "detailed")
                else:
                    self.memory_model.save_user_fact(user_phone, "conversation_style", "brief")
            
            # Extract waste management interests
            waste_keywords = {
                "organik": "organic_waste_interest",
                "daur ulang": "recycling_interest", 
                "kompos": "composting_interest",
                "b3": "hazardous_waste_interest",
                "jadwal": "schedule_interest",
                "lokasi": "location_interest"
            }
            
            for keyword, fact_key in waste_keywords.items():
                if keyword in user_message.lower():
                    self.memory_model.save_user_fact(user_phone, fact_key, "high")
                    break
                
        except Exception as e:
            logger.error(f"Error extracting facts: {str(e)}")
    
    def _fallback_response(self, user_message: str, user_phone: str, mode: str = "hybrid") -> str:
        """Fallback response when AI is not available"""
        try:
            user_context = self._get_user_context(user_phone)
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            user_name = self._get_display_name(user_phone, user_context, user_facts)
            
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

    def _extract_user_preferences(self, user_facts: Dict) -> Dict[str, Any]:
        """Extract user preferences from facts"""
        preferences = {}
        
        # Extract interests
        for key, fact_data in user_facts.items():
            if "interest" in key:
                preferences[key] = fact_data.get("value", "unknown")
        
        # Extract conversation style
        if "conversation_style" in user_facts:
            preferences["conversation_style"] = user_facts["conversation_style"].get("value", "general")
        
        return preferences

    def _analyze_conversation_patterns(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation patterns for better personalization"""
        if not conversation_history:
            return {}
        
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
        
        if not user_messages:
            return {}
        
        # Analyze message patterns
        patterns = {
            "total_messages": len(user_messages),
            "avg_message_length": sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages),
            "question_frequency": sum(1 for msg in user_messages if "?" in msg.get("content", "")),
            # Do not track emojis; keep numeric field for compatibility
            "emoji_usage": 0,
            "topic_diversity": len(set(msg.get("content", "")[:20] for msg in user_messages))
        }
        
        return patterns

    def get_memory_stats(self, user_phone: str) -> Dict[str, Any]:
        """Get comprehensive memory statistics for a user"""
        try:
            user_facts = self.memory_model.get_all_user_facts(user_phone)
            conversation_count = self.conversation_model.get_conversation_count(user_phone)
            conversation_summary = self.conversation_model.get_conversation_summary(user_phone, 30)
            conversation_topics = self.conversation_model.get_conversation_topics(user_phone, 20)
            
            return {
                "user_facts_count": len(user_facts),
                "conversation_count": conversation_count,
                "recent_activity": conversation_summary,
                "common_topics": conversation_topics,
                "memory_keys": list(user_facts.keys()),
                "last_conversation": conversation_summary.get("last_message") if conversation_summary else None
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {}
