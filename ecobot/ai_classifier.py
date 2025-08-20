"""
AI Classifier Module
Menggunakan Lumos AI API untuk klasifikasi sampah berdasarkan gambar
"""

import os
import logging
import requests
import base64
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class AIClassifier:
    """AI-powered waste classification using Lumos API"""
    
    def __init__(self):
        self.api_key = os.getenv('LUNOS_API_KEY')
        self.base_url = os.getenv('LUNOS_BASE_URL', 'https://api.lunos.tech/v1')
        
        if not self.api_key:
            logger.warning("Lunos API key not found. Using mock classification.")
            self.use_mock = True
        else:
            self.use_mock = False
            
        # Waste categories
        self.waste_categories = {
            'organik': {
                'keywords': ['food', 'fruit', 'vegetable', 'organic', 'leaf', 'banana'],
                'confidence_threshold': 0.7
            },
            'anorganik': {
                'keywords': ['plastic', 'bottle', 'can', 'metal', 'glass', 'paper'],
                'confidence_threshold': 0.7
            },
            'b3': {
                'keywords': ['battery', 'electronic', 'chemical', 'medicine', 'toxic'],
                'confidence_threshold': 0.8
            }
        }
        
        logger.info("AI Classifier initialized")
    
    def classify_waste_image(self, image_data):
        """
        Classify waste type from image data
        
        Args:
            image_data (bytes): Image data in bytes format
            
        Returns:
            dict: Classification result with waste_type and confidence
        """
        try:
            if self.use_mock:
                return self._mock_classification(image_data)
            
            # Prepare image for API
            image_b64 = self._prepare_image_for_api(image_data)
            if not image_b64:
                return None
            
            # Call Lumos API
            result = self._call_lumos_api(image_b64)
            
            if result:
                # Process API response
                return self._process_classification_result(result)
            else:
                # Fallback to mock if API fails
                logger.warning("API failed, using mock classification")
                return self._mock_classification(image_data)
                
        except Exception as e:
            logger.error(f"Error in waste classification: {str(e)}")
            return self._mock_classification(image_data)
    
    def _prepare_image_for_api(self, image_data):
        """Prepare image for API submission"""
        try:
            # Open and resize image if needed
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1024x1024)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_b64
            
        except Exception as e:
            logger.error(f"Error preparing image: {str(e)}")
            return None
    
    def _call_lumos_api(self, image_b64):
        """Call Lumos AI API for image classification"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare payload for waste classification
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analisis gambar sampah ini dan klasifikasikan ke dalam salah satu kategori:
                                1. ORGANIK - sisa makanan, daun, sampah yang dapat terurai
                                2. ANORGANIK - plastik, kaleng, kertas, kaca
                                3. B3 - baterai, elektronik, bahan kimia berbahaya
                                
                                Berikan jawaban dalam format JSON: {"category": "organik/anorganik/b3", "confidence": 0.95, "description": "deskripsi singkat"}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API call: {str(e)}")
            return None
    
    def _process_classification_result(self, api_result):
        """Process API response and extract classification"""
        try:
            # Extract content from API response
            content = api_result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Try to parse JSON response
            import json
            try:
                parsed_result = json.loads(content)
                waste_type = parsed_result.get('category', '').lower()
                confidence = float(parsed_result.get('confidence', 0.0))
                description = parsed_result.get('description', '')
            except (json.JSONDecodeError, ValueError):
                # Fallback: parse text response
                waste_type, confidence = self._parse_text_response(content)
                description = content[:100] + "..." if len(content) > 100 else content
            
            # Validate waste type
            if waste_type not in self.waste_categories:
                waste_type = self._determine_fallback_category(content)
                confidence = max(0.5, confidence)
            
            return {
                'waste_type': waste_type,
                'confidence': confidence,
                'description': description,
                'method': 'lumos_api'
            }
            
        except Exception as e:
            logger.error(f"Error processing classification result: {str(e)}")
            return None
    
    def _parse_text_response(self, text):
        """Parse text response for waste classification"""
        text_lower = text.lower()
        
        # Check for each category
        for category, info in self.waste_categories.items():
            for keyword in info['keywords']:
                if keyword in text_lower:
                    return category, 0.8
        
        # Default to anorganik if uncertain
        return 'anorganik', 0.6
    
    def _determine_fallback_category(self, text):
        """Determine fallback category based on text content"""
        text_lower = text.lower()
        
        # Priority-based matching
        if any(word in text_lower for word in ['organik', 'organic', 'food', 'makanan', 'daun']):
            return 'organik'
        elif any(word in text_lower for word in ['b3', 'battery', 'electronic', 'berbahaya', 'beracun']):
            return 'b3'
        else:
            return 'anorganik'
    
    def _mock_classification(self, image_data):
        """Mock classification for development/testing"""
        try:
            # Simple mock based on image size or random
            import random
            
            # Simulate different waste types
            waste_types = ['organik', 'anorganik', 'b3']
            probabilities = [0.4, 0.5, 0.1]  # More common types have higher probability
            
            waste_type = random.choices(waste_types, weights=probabilities)[0]
            confidence = random.uniform(0.7, 0.95)
            
            descriptions = {
                'organik': 'Sampah organik seperti sisa makanan atau daun',
                'anorganik': 'Sampah anorganik seperti plastik atau kaleng',
                'b3': 'Sampah B3 yang berpotensi berbahaya'
            }
            
            logger.info(f"Mock classification: {waste_type} ({confidence:.2f})")
            
            return {
                'waste_type': waste_type,
                'confidence': confidence,
                'description': descriptions[waste_type],
                'method': 'mock'
            }
            
        except Exception as e:
            logger.error(f"Error in mock classification: {str(e)}")
            return {
                'waste_type': 'anorganik',
                'confidence': 0.5,
                'description': 'Klasifikasi default',
                'method': 'fallback'
            }
    
    def validate_classification(self, result):
        """Validate classification result"""
        if not result:
            return False
        
        required_fields = ['waste_type', 'confidence']
        return all(field in result for field in required_fields)
    
    def get_supported_categories(self):
        """Get list of supported waste categories"""
        return list(self.waste_categories.keys())
