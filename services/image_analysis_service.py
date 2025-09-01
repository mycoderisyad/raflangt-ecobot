"""
Image Analysis Service
Service untuk analisis gambar menggunakan API unli.dev
Specialized untuk klasifikasi jenis sampah dan waste management
"""

import os
import base64
import json
import logging
import requests
from typing import Dict, Any, Optional
from core.config import get_config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ImageAnalysisService:
    """Service untuk analisis gambar menggunakan unli.dev API"""

    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv("UNLI_API_KEY")
        self.base_url = os.getenv("UNLI_BASE_URL", "https://api.unli.dev/v1")
        self.model = os.getenv("UNLI_MODEL", "auto")

        # Setup headers for requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.api_key:
            logger.info(f"Image Analysis service initialized with model: {self.model}")
        else:
            logger.warning(
                "UNLI_API_KEY not configured. Image analysis will be limited."
            )

    def encode_image_to_base64(self, image_data: bytes) -> Optional[str]:
        """Convert image bytes to base64 string with proper MIME type"""
        try:
            base64_string = base64.b64encode(image_data).decode("utf-8")

            # Detect image format from image data
            if image_data.startswith(b"\x89PNG"):
                mime_type = "image/png"
            elif image_data.startswith(b"\xff\xd8\xff"):
                mime_type = "image/jpeg"
            elif image_data.startswith(b"GIF"):
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"  # default

            return f"data:{mime_type};base64,{base64_string}"

        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            return None

    def is_sticker(self, image_data: bytes) -> bool:
        """Detect if image is likely a sticker (animated GIF, small size, etc.)"""
        try:
            # Check if it's a GIF (common sticker format)
            if image_data.startswith(b'GIF'):
                return True
            
            # Check file size - stickers are usually small
            if len(image_data) < 100 * 1024:  # Less than 100KB
                return True
                
            # Additional checks could be added here for other sticker formats
            return False
        except Exception:
            return False

    def analyze_waste_image(
        self, image_data: bytes, user_phone: str = None
    ) -> Dict[str, Any]:
        """
        Analyze waste image using unli.dev API
        Returns waste classification with confidence score
        """
        try:
            # Check if this is a sticker first
            if self.is_sticker(image_data):
                return {
                    "success": True,
                    "is_sticker": True,
                    "waste_type": "STICKER",
                    "confidence": 1.0,
                    "description": "Sticker detected",
                    "tips": "This is a sticker, not waste for analysis",
                }

            if not self.api_key:
                logger.warning("Unli.dev API key not configured")
                return {
                    "success": False,
                    "error": "API key not configured",
                    "waste_type": "TIDAK_TERIDENTIFIKASI",
                    "confidence": 0.0,
                    "description": "API key tidak dikonfigurasi",
                    "tips": "Silakan hubungi administrator untuk konfigurasi API",
                }

            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_data)
            if not base64_image:
                return {
                    "success": False,
                    "error": "Failed to encode image",
                    "waste_type": "TIDAK_TERIDENTIFIKASI",
                    "confidence": 0.0,
                    "description": "Gagal memproses gambar",
                    "tips": "Pastikan gambar dalam format yang didukung (JPG, PNG, GIF)",
                }

            # Prepare the prompt for waste classification
            waste_prompt = """Anda adalah sistem AI untuk klasifikasi sampah di Indonesia. 
Analisis gambar yang diberikan dan klasifikasikan jenis sampah dengan akurat.

JENIS SAMPAH:
1. ORGANIK - sisa makanan, daun, ranting, kulit buah/sayur, sampah kebun
2. ANORGANIK - plastik, kaleng, botol, kertas, kaca, logam, kardus
3. B3 - baterai, lampu, obat kadaluarsa, cat, zat kimia berbahaya
4. TIDAK_TERIDENTIFIKASI - jika tidak jelas atau bukan sampah

INSTRUKSI:
- Berikan klasifikasi yang akurat berdasarkan objek dalam gambar
- Confidence score 0.0-1.0 (1.0 = sangat yakin)
- Deskripsi singkat objek yang terlihat
- Tips pengelolaan yang sesuai

Response format JSON:
{
  "waste_type": "ORGANIK/ANORGANIK/B3/TIDAK_TERIDENTIFIKASI",
  "confidence": 0.95,
  "description": "Deskripsi singkat objek yang terlihat",
  "tips": "Tips pengelolaan untuk jenis sampah ini"
}

Klasifikasikan jenis sampah dalam gambar ini dengan akurat. Berikan response dalam format JSON yang diminta."""

            # Make API request
            try:
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": base64_image},
                                },
                                {"type": "text", "text": waste_prompt},
                            ],
                        }
                    ],
                    "max_tokens": 700,
                    "temperature": 0.1,
                }

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=30,
                )

                if response.status_code != 200:
                    error_msg = f"{response.status_code} - {response.text}"
                    logger.error(f"Unli.dev API error: {error_msg}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "waste_type": "TIDAK_TERIDENTIFIKASI",
                        "confidence": 0.0,
                        "description": "Gagal menganalisis gambar",
                        "tips": "Coba lagi dalam beberapa saat",
                    }

                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

            except requests.RequestException as e:
                logger.error(f"API request failed: {str(e)}")
                return {
                    "success": False,
                    "error": f"API request failed: {str(e)}",
                    "waste_type": "TIDAK_TERIDENTIFIKASI",
                    "confidence": 0.0,
                    "description": "Koneksi ke API gagal",
                    "tips": "Periksa koneksi internet dan coba lagi",
                }

            # Parse JSON response
            try:
                # Clean up the response - remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = (
                        content.split("\n", 1)[1].rsplit("\n", 1)[0]
                        if "\n" in content
                        else content.replace("```", "")
                    )

                classification_result = json.loads(content)

                # Validate required fields
                required_fields = ["waste_type", "confidence", "description", "tips"]
                for field in required_fields:
                    if field not in classification_result:
                        classification_result[field] = "Not provided"

                # Validate waste_type
                valid_types = ["ORGANIK", "ANORGANIK", "B3", "TIDAK_TERIDENTIFIKASI"]
                if classification_result["waste_type"] not in valid_types:
                    classification_result["waste_type"] = "TIDAK_TERIDENTIFIKASI"

                # Ensure confidence is a float between 0 and 1
                try:
                    confidence = float(classification_result["confidence"])
                    classification_result["confidence"] = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    classification_result["confidence"] = 0.5

                classification_result["success"] = True
                classification_result["method"] = "unli_api"

                logger.info(
                    f"Image classification successful: {classification_result['waste_type']} (confidence: {classification_result['confidence']})"
                )
                return classification_result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Raw response: {content}")

                # Fallback classification based on keywords in response
                return self._fallback_classification(content)

        except Exception as e:
            logger.error(f"Unexpected error in image analysis: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "waste_type": "TIDAK_TERIDENTIFIKASI",
                "confidence": 0.0,
                "description": "Terjadi kesalahan sistem",
                "tips": "Silakan coba lagi atau hubungi administrator",
            }

    def _fallback_classification(self, response_text: str) -> Dict[str, Any]:
        """Fallback classification when JSON parsing fails"""
        logger.info("Using fallback classification method")

        # Simple keyword-based classification
        text_lower = response_text.lower()

        if any(
            keyword in text_lower
            for keyword in ["organik", "sisa makanan", "daun", "buah", "sayur"]
        ):
            waste_type = "ORGANIK"
            confidence = 0.7
        elif any(
            keyword in text_lower
            for keyword in ["plastik", "botol", "kaleng", "kertas", "anorganik"]
        ):
            waste_type = "ANORGANIK"
            confidence = 0.7
        elif any(
            keyword in text_lower for keyword in ["baterai", "b3", "berbahaya", "kimia"]
        ):
            waste_type = "B3"
            confidence = 0.7
        else:
            waste_type = "TIDAK_TERIDENTIFIKASI"
            confidence = 0.3

        return {
            "success": True,
            "waste_type": waste_type,
            "confidence": confidence,
            "description": "Klasifikasi berdasarkan analisis teks",
            "tips": f"Sampah {waste_type.lower()} - silakan pisahkan sesuai jenisnya",
            "method": "fallback_text",
        }

    def get_waste_education(self, waste_type: str) -> Dict[str, Any]:
        """Get educational content for specific waste type"""
        education_content = {
            "ORGANIK": {
                "title": "Sampah Organik",
                "description": "Sampah yang berasal dari makhluk hidup dan dapat terurai secara alami",
                "examples": ["Sisa makanan", "Daun kering", "Kulit buah", "Ranting"],
                "handling": [
                    "Pisahkan dari sampah lain",
                    "Buat kompos di rumah",
                    "Berikan pada ternak (jika sesuai)",
                    "Buang ke tempat sampah organik",
                ],
                "benefits": "Dapat dijadikan kompos untuk menyuburkan tanaman",
            },
            "ANORGANIK": {
                "title": "Sampah Anorganik",
                "description": "Sampah yang tidak dapat terurai secara alami",
                "examples": ["Plastik", "Kaleng", "Botol kaca", "Kertas"],
                "handling": [
                    "Bersihkan sebelum dibuang",
                    "Pisahkan berdasarkan jenis",
                    "Kumpulkan untuk didaur ulang",
                    "Jual ke pengepul sampah",
                ],
                "benefits": "Dapat didaur ulang menjadi produk baru",
            },
            "B3": {
                "title": "Sampah B3 (Bahan Berbahaya dan Beracun)",
                "description": "Sampah yang mengandung bahan berbahaya bagi kesehatan dan lingkungan",
                "examples": ["Baterai", "Lampu bekas", "Obat kadaluarsa", "Cat"],
                "handling": [
                    "JANGAN buang sembarangan",
                    "Kumpulkan di tempat khusus",
                    "Serahkan ke fasilitas pengelolaan B3",
                    "Hindari kontak langsung",
                ],
                "benefits": "Mencegah pencemaran lingkungan dan bahaya kesehatan",
            },
        }

        return education_content.get(
            waste_type,
            {
                "title": "Sampah Tidak Teridentifikasi",
                "description": "Jenis sampah tidak dapat diidentifikasi dengan jelas",
                "examples": [],
                "handling": [
                    "Periksa kembali jenis sampah",
                    "Konsultasi dengan petugas kebersihan",
                    "Buang di tempat sampah umum",
                ],
                "benefits": "Pengelolaan yang tepat membantu menjaga kebersihan lingkungan",
            },
        )
