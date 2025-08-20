"""
Education Module
Menyediakan konten edukatif tentang pengelolaan sampah
"""

import logging
import random
from utils.message_loader import message_loader

logger = logging.getLogger(__name__)

class EducationModule:
    """Provide educational content about waste management"""
    
    def __init__(self):
        self.messages = message_loader.get_education_messages()
        logger.info("Education Module initialized")
    
    def get_waste_education(self, waste_type):
        """Get educational content for specific waste type"""
        waste_types = self.messages.get('waste_types', {})
        
        if waste_type in waste_types:
            return waste_types[waste_type]
        else:
            return self._get_default_education()
    
    def get_general_education(self):
        """Get general waste management education"""
        general_tips = self.messages.get('general_tips', [])
        general_edu = self.messages.get('general_education', {})
        
        tips = random.sample(general_tips, min(4, len(general_tips)))
        
        content = f"{general_edu.get('title', 'Tips Pengelolaan Sampah')}\n\n"
        
        principles = general_edu.get('principles', {})
        content += f"{principles.get('title', 'Prinsip 4R:')}\n"
        for item in principles.get('items', []):
            content += f"• {item}\n"
        content += "\n"
        
        practical_tips = general_edu.get('practical_tips', {})
        content += f"{practical_tips.get('title', '**Tips Praktis:**')}\n"
        for tip in tips:
            content += f"• {tip}\n"
        
        benefits = general_edu.get('benefits', {})
        content += f"\n{benefits.get('title', 'Manfaat:')}\n"
        for benefit in benefits.get('items', []):
            content += f"• {benefit}\n"
        
        return content
    
    def _get_default_education(self):
        """Get default education content for unknown waste types"""
        default_msg = self.messages.get('default_messages', {})
        return {
            'name': 'Jenis Sampah Tidak Dikenali',
            'description': default_msg.get('unknown_type', 'Jenis sampah tidak dikenali'),
            'sorting_guide': 'Silakan kirim foto yang lebih jelas atau hubungi petugas.',
            'recycling_tips': 'Pastikan sampah sudah dipilah dengan benar.',
            'detailed_info': default_msg.get('error_message', 'Terjadi kesalahan dalam identifikasi')
        }
