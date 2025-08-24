"""AI Service - Image Analysis Integration"""
import logging
import tempfile
import os
from typing import Optional, Dict, Any
from services.image_analysis_service import ImageAnalysisService


class AIService:
    """AI Service for image analysis and waste classification"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.image_analyzer = ImageAnalysisService()
        self.logger.info("AI Service initialized with Image Analysis Service")

    def generate_conversation_response(
        self, user_message: str, user_phone: str = None
    ) -> Optional[str]:
        """Legacy method - now redirects to AI agent warning"""
        self.logger.warning(
            "generate_conversation_response called - should use ai_agent instead"
        )
        return "Text conversations are now handled by AI Agent. Please use ai_agent.process_message() instead."

    def analyze_image(
        self, image_data, user_phone: str = None, user_question: str = None
    ) -> Optional[str]:
        """Analyze image using image analysis service - supports both file path and bytes"""
        try:
            # Handle different input types
            if isinstance(image_data, bytes):
                # Save bytes to temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as tmp_file:
                    tmp_file.write(image_data)
                    image_path = tmp_file.name

                # Analyze the temporary file
                result = self._analyze_image_file(image_path, user_phone)

                # Clean up temporary file
                try:
                    os.unlink(image_path)
                except:
                    pass

                return result
            else:
                # Assume it's a file path
                return self._analyze_image_file(image_data, user_phone)

        except Exception as e:
            self.logger.error(f"Image analysis error: {str(e)}")
            return self._fallback_image_response()

    def _analyze_image_file(
        self, image_path: str, user_phone: str = None
    ) -> Optional[str]:
        """Internal method to analyze image file"""
        try:
            # Use image analysis service for waste classification
            analysis_result = self.image_analyzer.analyze_waste_image(
                image_path, user_phone
            )

            if analysis_result.get("success"):
                waste_type = analysis_result.get("waste_type", "TIDAK_TERIDENTIFIKASI")
                confidence = analysis_result.get("confidence", 0.0)
                description = analysis_result.get("description", "Sampah terdeteksi")
                tips = analysis_result.get("tips", "Silakan buang sesuai jenisnya")

                # Format response message
                confidence_percent = int(confidence * 100)

                if waste_type == "TIDAK_TERIDENTIFIKASI":
                    response = "Maaf, saya tidak dapat mengidentifikasi jenis sampah dari gambar ini dengan akurat. "
                    response += (
                        "Gambar mungkin kurang jelas atau tidak menunjukkan sampah. "
                    )
                    response += "Coba ambil foto yang lebih jelas atau hubungi petugas setempat untuk bantuan."
                else:
                    response = "Hasil Analisis Sampah:\n\n"
                    response += f"Jenis: {waste_type}\n"
                    response += f"Confidence: {confidence_percent}%\n"
                    response += f"Deskripsi: {description}\n\n"
                    response += f"Tips Pengelolaan:\n{tips}\n\n"

                    # Add specific advice based on waste type
                    if waste_type == "ORGANIK":
                        response += "Sampah organik bisa dijadikan kompos atau diberikan ke petugas pengomposan desa."
                    elif waste_type == "ANORGANIK":
                        response += "Pastikan bersih sebelum dibuang. Sebagian bisa didaur ulang."
                    elif waste_type == "B3":
                        response += "PENTING: Sampah B3 harus ditangani khusus. Jangan buang sembarangan!"

                return response

            else:
                error_msg = analysis_result.get("error", "Unknown error")
                self.logger.error(f"Image analysis failed: {error_msg}")
                return self._fallback_image_response()

        except Exception as e:
            self.logger.error(f"Image analysis error: {str(e)}")
            return self._fallback_image_response()

    def classify_waste_image(self, image_data) -> Optional[Dict[str, Any]]:
        """Classify waste from image using image analysis service - supports both file path and bytes"""
        try:
            # Handle different input types
            if isinstance(image_data, bytes):
                # Save bytes to temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as tmp_file:
                    tmp_file.write(image_data)
                    image_path = tmp_file.name

                # Analyze the temporary file
                result = self.image_analyzer.analyze_waste_image(image_path)

                # Clean up temporary file
                try:
                    os.unlink(image_path)
                except:
                    pass

                return result
            else:
                # Assume it's a file path
                return self.image_analyzer.analyze_waste_image(image_data)
        except Exception as e:
            self.logger.error(f"Waste classification error: {str(e)}")
            return self._classify_with_simulation()

    def enhance_service_response(
        self, service_type: str, base_response: str, user_context: Dict = None
    ) -> str:
        """Legacy method - text enhancement now handled by AI agent"""
        self.logger.warning(
            "enhance_service_response called - should use ai_agent instead"
        )
        return base_response

    def _fallback_image_response(self) -> str:
        """Fallback response for image analysis when service is not available"""
        return """Maaf, layanan analisis gambar sedang tidak tersedia. 

Silakan coba lagi nanti atau hubungi petugas desa untuk bantuan identifikasi sampah manual. 

Sementara itu, Anda bisa:
- Ketik 'edukasi' untuk tips umum pengelolaan sampah
- Ketik 'lokasi' untuk info tempat pengumpulan sampah"""

    def _classify_with_simulation(self) -> Dict[str, Any]:
        """Simulate waste classification for development"""
        import random

        waste_types = ["ORGANIK", "ANORGANIK", "B3"]
        selected_type = random.choice(waste_types)
        confidence = round(random.uniform(0.7, 0.95), 2)

        self.logger.info(f"Simulated classification: {selected_type} ({confidence})")

        return {
            "success": True,
            "waste_type": selected_type,
            "confidence": confidence,
            "description": f"Simulasi {selected_type}",
            "tips": "Buang sampah sesuai jenisnya",
            "method": "simulation",
        }

    def get_supported_image_formats(self) -> Dict[str, Any]:
        """Get list of image formats supported by the image analysis service"""
        try:
            return self.image_analyzer.get_supported_formats()
        except Exception as e:
            self.logger.error(f"Error getting supported formats: {str(e)}")
            return {
                "supported_formats": ["JPEG", "PNG"],
                "max_size_mb": 16,
                "recommended_resolution": "640x480 to 1600x1200",
                "note": "Pastikan foto terang dan jelas untuk hasil analisis terbaik",
            }

    def get_ai_capabilities(self) -> Dict[str, Any]:
        """Get information about AI capabilities"""
        try:
            image_caps = (
                self.image_analyzer.get_supported_formats()
                if hasattr(self.image_analyzer, "get_supported_formats")
                else {}
            )

            return {
                "text_ai": {
                    "available": False,
                    "note": "Text conversations now handled by AI agent",
                },
                "image_analysis": image_caps,
                "services": {
                    "conversation": "ai_agent (Lunos.tech)",
                    "image_analysis": "image_analysis_service (unli.dev)",
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting AI capabilities: {str(e)}")
            return {
                "text_ai": {"available": False},
                "image_analysis": {"available": False},
                "error": str(e),
            }
