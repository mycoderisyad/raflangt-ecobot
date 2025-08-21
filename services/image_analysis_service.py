"""
Image Analysis Service
Service untuk analisis gambar menggunakan API unli.dev
Specialized untuk klasifikasi jenis sampah dan waste management
"""

import os
import base64
import logging
from typing import Dict, Any, Optional
from core.config import get_config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    import requests
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available, falling back to requests")

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    """Service untuk analisis gambar menggunakan unli.dev API"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = os.getenv('UNLI_API_KEY')
        self.base_url = os.getenv('UNLI_BASE_URL', 'https://api.unli.dev/v1')
        self.model = os.getenv('UNLI_IMAGE_MODEL')
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"Image Analysis service initialized with OpenAI client, model: {self.model}")
        else:
            self.client = None
            # Fallback headers for requests
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            logger.info(f"Image Analysis service initialized with requests fallback, model: {self.model}")
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image file to base64 string"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
                
                # Detect image format
                if image_path.lower().endswith(('.png')):
                    mime_type = 'image/png'
                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif image_path.lower().endswith(('.gif')):
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'  # default
                
                return f"data:{mime_type};base64,{base64_string}"
                
        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            return None
    
    def analyze_waste_image(self, image_path: str, user_phone: str = None) -> Dict[str, Any]:
        """
        Analyze waste image using unli.dev API
        Returns waste classification with confidence score
        """
        try:
            if not self.api_key:
                logger.warning("Unli.dev API key not configured")
                return {
                    'success': False,
                    'error': 'API key not configured',
                    'waste_type': 'TIDAK_TERIDENTIFIKASI',
                    'confidence': 0.0
                }
            
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return {
                    'success': False,
                    'error': 'Failed to encode image',
                    'waste_type': 'TIDAK_TERIDENTIFIKASI',
                    'confidence': 0.0
                }
            
            # Prepare the prompt for waste classification (combined with text)
            combined_prompt = """Anda adalah sistem AI untuk klasifikasi sampah di Indonesia. 
Analisis gambar yang diberikan dan klasifikasikan jenis sampah dengan akurat.

JENIS SAMPAH:
1. ORGANIK - sisa makanan, daun, ranting, kulit buah/sayur
2. ANORGANIK - plastik, kaleng, botol, kertas, kaca, logam
3. B3 - baterai, lampu, obat kadaluarsa, cat, zat kimia berbahaya
4. TIDAK_TERIDENTIFIKASI - jika tidak jelas atau bukan sampah

Response format JSON:
{
  "waste_type": "ORGANIK/ANORGANIK/B3/TIDAK_TERIDENTIFIKASI",
  "confidence": 0.95,
  "description": "Deskripsi singkat objek yang terlihat",
  "tips": "Tips pengelolaan untuk jenis sampah ini"
}

Klasifikasikan jenis sampah dalam gambar ini dengan akurat. Berikan response dalam format JSON yang diminta."""
            
            # Make API request using OpenAI client or requests fallback
            try:
                if self.client:
                    # Use OpenAI client with unli.dev format (as per documentation)
                    response = self.client.chat.completions.create(
                        model="auto",  # Fixed: use "auto" as per unli.dev docs
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": base64_image
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": combined_prompt
                                    }
                                ]
                            }
                        ],
                        max_tokens=300,
                        temperature=0.1
                    )
                    content = response.choices[0].message.content.strip()
                else:
                    # Fallback to requests with corrected format
                    data = {
                        "model": "auto",  # Fixed: use "auto" as per unli.dev docs
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": base64_image
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": combined_prompt
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0.1
                    }
                    
                    import requests
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"{response.status_code} - {response.text}"
                        logger.error(f"Unli.dev API error: {error_msg}")
                        return {
                            'success': False,
                            'error': f'API error: {response.status_code}',
                            'waste_type': 'TIDAK_TERIDENTIFIKASI',
                            'confidence': 0.0
                        }
                    
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
            
            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                return {
                    'success': False,
                    'error': f'API request failed: {str(e)}',
                    'waste_type': 'TIDAK_TERIDENTIFIKASI',
                    'confidence': 0.0
                }
            
            # Parse JSON response
            try:
                import json
                analysis_result = json.loads(content)
                
                # Validate required fields
                waste_type = analysis_result.get('waste_type', 'TIDAK_TERIDENTIFIKASI')
                confidence = float(analysis_result.get('confidence', 0.0))
                description = analysis_result.get('description', 'Sampah terdeteksi')
                tips = analysis_result.get('tips', 'Silakan buang sesuai jenisnya')
                
                logger.info(f"Image analysis successful: {waste_type} ({confidence:.2f})")
                
                return {
                    'success': True,
                    'waste_type': waste_type,
                    'confidence': confidence,
                    'description': description,
                    'tips': tips,
                    'raw_response': content
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw content: {content}")
                
                # Fallback: extract waste type from text response
                content_upper = content.upper()
                if 'ORGANIK' in content_upper:
                    waste_type = 'ORGANIK'
                    confidence = 0.8
                elif 'ANORGANIK' in content_upper:
                    waste_type = 'ANORGANIK'
                    confidence = 0.8
                elif 'B3' in content_upper:
                    waste_type = 'B3'
                    confidence = 0.8
                else:
                    waste_type = 'TIDAK_TERIDENTIFIKASI'
                    confidence = 0.3
                
                return {
                    'success': True,
                    'waste_type': waste_type,
                    'confidence': confidence,
                    'description': content[:100],
                    'tips': 'Buang sampah sesuai jenisnya',
                    'raw_response': content
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during image analysis: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'waste_type': 'TIDAK_TERIDENTIFIKASI',
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"Unexpected error during image analysis: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'waste_type': 'TIDAK_TERIDENTIFIKASI',
                'confidence': 0.0
            }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get information about supported image formats"""
        return {
            'supported_formats': ['JPEG', 'PNG', 'GIF'],
            'max_size_mb': 16,
            'recommended_resolution': '640x480 to 1600x1200',
            'optimal_conditions': [
                'Pencahayaan yang cukup',
                'Objek terlihat jelas',
                'Fokus pada sampah utama',
                'Hindari background yang ramai'
            ]
        }
    
    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """Validate image before processing"""
        try:
            import os
            from PIL import Image
            
            if not os.path.exists(image_path):
                return {'valid': False, 'error': 'File tidak ditemukan'}
            
            # Check file size (max 16MB)
            file_size = os.path.getsize(image_path)
            if file_size > 16 * 1024 * 1024:
                return {'valid': False, 'error': 'File terlalu besar (max 16MB)'}
            
            # Check if it's a valid image
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_name = img.format
                    
                    if format_name not in ['JPEG', 'PNG', 'GIF']:
                        return {'valid': False, 'error': f'Format {format_name} tidak didukung'}
                    
                    return {
                        'valid': True,
                        'width': width,
                        'height': height,
                        'format': format_name,
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    }
            except Exception as e:
                return {'valid': False, 'error': f'File bukan gambar valid: {str(e)}'}
                
        except ImportError:
            # PIL not available, basic validation only
            return {'valid': True, 'note': 'Basic validation only'}
        except Exception as e:
            return {'valid': False, 'error': f'Error validating image: {str(e)}'}
