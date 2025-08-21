"""
Feature Service
Handles all EcoBot features like education, schedule, location, etc.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from core.config import get_config
from core.utils import LoggerUtils
from core.constants import WASTE_TYPES


class FeatureService:
    """Service for handling EcoBot features"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = LoggerUtils.get_logger(__name__)
        self.village_name = os.getenv('VILLAGE_NAME', 'Desa Cukangkawung')
    
    def get_education_content(self, query: str = None) -> str:
        """Get education content about waste management"""
        if not query:
            return self._get_general_education()
        
        query_lower = query.lower()
        
        if 'kompos' in query_lower:
            return self._get_compost_education()
        elif any(word in query_lower for word in ['milah', 'pilah', 'pisah']):
            return self._get_sorting_education()
        elif 'daur' in query_lower or 'recycle' in query_lower:
            return self._get_recycling_education()
        elif 'organik' in query_lower:
            return self._get_organic_education()
        elif 'anorganik' in query_lower or 'plastik' in query_lower:
            return self._get_inorganic_education()
        elif 'b3' in query_lower or 'berbahaya' in query_lower:
            return self._get_hazardous_education()
        else:
            return self._get_general_education()
    
    def get_schedule_info(self) -> str:
        """Get waste collection schedule"""
        schedule_data = {
            "title": "Jadwal Pengumpulan Sampah",
            "subtitle": f"Jadwal rutin pengumpulan sampah di {self.village_name}",
            "schedule": [
                "🗓️ Senin, Rabu, Jumat",
                "⏰ Pukul: 07.00 - 16.00 WIB",
                "Titik: Balai Desa & Pos Ronda",
                "",
                "Jadwal Khusus B3:",
                "🗓️ Sabtu terakhir setiap bulan",
                "⏰ Pukul: 09.00 - 12.00 WIB",
                "Titik: Kantor Desa"
            ],
            "notes": [
                "Pastikan sampah sudah dipilah sebelum disetor",
                "💡 Bawa sampah 30 menit sebelum waktu tutup",
                "Hubungi koordinator jika ada kendala"
            ]
        }
        
        response = f"{schedule_data['title']}\n"
        response += f"{schedule_data['subtitle']}\n\n"
        response += "\n".join(schedule_data['schedule'])
        response += "\n\nCatatan Penting:\n"
        response += "\n".join(schedule_data['notes'])
        
        return response
    
    def get_location_info(self) -> str:
        """Get waste collection locations with Google Maps"""
        try:
            # Load maps data
            maps_file = os.path.join('messages', 'maps_data.json')
            with open(maps_file, 'r', encoding='utf-8') as f:
                maps_data = json.load(f)
            
            response = "Lokasi Pengumpulan Sampah\n"
            response += f"Titik pengumpulan sampah di {self.village_name}:\n\n"
            
            for i, location in enumerate(maps_data.get('collection_points', []), 1):
                response += f"{i}. {location['name']}\n"
                response += f"{location['address']}\n"
                response += f"{location['contact']}\n"
                response += f"🗺️ {location['maps_url']}\n"
                
                if location.get('accepted_waste'):
                    response += f"Menerima: {', '.join(location['accepted_waste'])}\n"
                
                if location.get('schedule'):
                    response += f"⏰ {location['schedule']}\n"
                
                response += "\n"
            
            response += "💡 Tips: Klik link maps untuk navigasi ke lokasi"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error loading maps data: {e}")
            return self._get_default_location()
    
    def get_points_info(self, phone_number: str) -> str:
        """Get user points information"""
        # Points system to be implemented in future version
        return """🏆 Sistem Poin EcoBot
        
🚧 Fitur Coming Soon!
        
Sistem poin akan memungkinkan Anda:
• Mengumpulkan poin dari setiap kontribusi
• Menukar poin dengan hadiah menarik
• Kompetisi bulanan antar warga
• Melacak kontribusi lingkungan Anda

Pantau terus untuk update fitur ini! 🌱"""
    
    def register_user_points(self, phone_number: str, name: str = None) -> str:
        """Register user to points system"""
        # Registration system to be implemented in future version
        return """Pendaftaran Sistem Poin
        
🚧 Fitur Coming Soon!
        
Saat ini sistem poin masih dalam pengembangan. 
Anda akan otomatis terdaftar ketika fitur ini sudah siap.

Terima kasih atas antusiasme Anda! 🙏"""
    
    def redeem_points(self, phone_number: str, item: str = None) -> str:
        """Redeem points for rewards"""
        # Redemption system to be implemented in future version
        return """Redeem Poin
        
🚧 Fitur Coming Soon!
        
Catalog hadiah yang bisa ditukar:
• Bibit tanaman (50 poin)
• 🧴 Botol minum ramah lingkungan (100 poin)
• 📚 Buku panduan berkebun (150 poin)
• 🏆 Sertifikat apresiasi (200 poin)

Tunggu peluncuran resmi fitur ini! 🚀"""
    
    def get_statistics(self, user_role: str) -> str:
        """Get system statistics (for coordinators)"""
        if user_role not in ['koordinator', 'admin']:
            return "Akses ditolak. Fitur ini hanya untuk koordinator dan admin."
        
        # Sample data - replace with actual database queries in production
        stats = {
            'total_users': 45,
            'active_users': 32,
            'images_classified': 127,
            'organic_waste': 78,
            'inorganic_waste': 43,
            'hazardous_waste': 6,
            'this_month': 89
        }
        
        response = f"""Statistik Sistem EcoBot
        
👥 Pengguna:
• Total terdaftar: {stats['total_users']} orang
• Aktif bulan ini: {stats['active_users']} orang

📸 Klasifikasi Sampah:
• Total gambar: {stats['images_classified']} foto
• Sampah organik: {stats['organic_waste']} foto
• Sampah anorganik: {stats['inorganic_waste']} foto
• Sampah B3: {stats['hazardous_waste']} foto

Bulan Ini:
• Interaksi: {stats['this_month']} kali
• Tingkat partisipasi: {round((stats['active_users']/stats['total_users'])*100)}%

Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        return response
    
    def generate_report(self, user_role: str) -> str:
        """Generate and send monthly report"""
        if user_role not in ['koordinator', 'admin']:
            return "Akses ditolak. Fitur ini hanya untuk koordinator dan admin."
        
        # Report generation to be implemented with email service integration
        return """📧 Laporan Bulanan
        
Laporan berhasil dipersiapkan!

Isi Laporan:
• Statistik penggunaan sistem
• Data klasifikasi sampah
• Tingkat partisipasi warga
• Rekomendasi perbaikan

📤 Status Pengiriman:
Laporan akan dikirim otomatis ke email koordinator dalam 5 menit.

📁 Format: PDF + Excel
📧 Tujuan: supportecobot@mailry.web.id"""
    
    def _get_general_education(self) -> str:
        """General education about waste management"""
        return """Edukasi Pengelolaan Sampah

📚 Topik yang tersedia:
• Ketik "apa itu kompos" - Belajar membuat kompos
• Ketik "bagaimana cara memilah" - Panduan pemilahan
• Ketik "manfaat daur ulang" - Info daur ulang
• Ketik "sampah organik" - Tips sampah organik
• Ketik "sampah anorganik" - Tips sampah anorganik

💡 Tips Harian:
Pemilahan sampah dimulai dari rumah! Sediakan 3 tempat sampah dengan warna berbeda untuk organik, anorganik, dan B3.

Tahukah Anda?
1 kg sampah organik bisa menghasilkan 0.3 kg kompos berkualitas dalam 2-3 minggu!"""
    
    def _get_compost_education(self) -> str:
        """Education about composting"""
        return """Cara Membuat Kompos

🥬 Bahan Yang Bisa Dikompos:
• Sisa sayuran dan buah-buahan
• Daun kering dan ranting kecil
• Cangkang telur (hancurkan dulu)
• Ampas kopi dan teh

Hindari:
• Daging dan tulang
• Minyak dan lemak
• Kotoran hewan peliharaan
• Sampah yang sudah basi

Langkah Mudah:
1. Campurkan bahan hijau (sisa makanan) dan coklat (daun kering) dengan rasio 1:3
2. Tambahkan sedikit tanah sebagai starter
3. Aduk setiap 3-4 hari
4. Siram jika terlalu kering
5. Kompos siap dalam 6-8 minggu

💡 Tips: Potong kecil-kecil bahan kompos agar lebih cepat terurai!"""
    
    def _get_sorting_education(self) -> str:
        """Education about waste sorting"""
        return """Panduan Pemilahan Sampah

🟢 ORGANIK (Tempat Hijau):
• Sisa makanan & minuman
• Kulit buah & sayuran
• Daun & ranting
• Kertas bekas makanan

🔵 ANORGANIK (Tempat Biru):
• Plastik (botol, kemasan)
• Kaleng & logam
• Kertas & karton bersih
• Kaca & botol

🔴 B3 (Tempat Merah):
• Baterai bekas
• Lampu neon
• Obat kadaluarsa
• Cat & thinner

Tips Pemilahan:
• Cuci bersih kemasan sebelum dibuang
• Pisahkan tutup dan badan botol
• Lipat karton agar menghemat ruang
• Kumpulkan B3 untuk disetor khusus"""
    
    def _get_recycling_education(self) -> str:
        """Education about recycling"""
        return """Manfaat Daur Ulang

Dampak Lingkungan:
• Mengurangi pencemaran tanah & air
• Menghemat energi hingga 70%
• Mengurangi emisi gas rumah kaca
• Melestarikan sumber daya alam

💰 Manfaat Ekonomi:
• Botol plastik: Rp 2.000/kg
• Kardus: Rp 1.500/kg
• Kaleng aluminium: Rp 15.000/kg
• Kertas putih: Rp 2.500/kg

🎨 Ide Kreatif:
• Botol plastik → Pot tanaman
• Kardus → Organizer
• Kaleng → Tempat pensil
• Koran → Tas belanja

💡 Tahukah Anda?
1 ton kertas daur ulang = menyelamatkan 17 pohon!"""
    
    def _get_organic_education(self) -> str:
        """Education about organic waste"""
        return """🥬 Sampah Organik

Yang Termasuk:
• Sisa makanan (nasi, sayur, buah)
• Kulit buah & sayuran
• Daun & rumput
• Kotoran hewan herbivora

🏠 Pengolahan di Rumah:
• Kompos takakura (dalam ember)
• Kompos cair (MOL)
• Biogas sederhana
• Pakan ternak (ayam/kambing)

⚡ Manfaat:
• Pupuk alami untuk tanaman
• Mengurangi volume sampah 60%
• Menghemat biaya pupuk
• Tanah lebih subur

⏱️ Waktu Penguraian:
• Sisa makanan: 2-4 minggu
• Daun: 6-12 bulan  
• Kulit buah: 1-2 bulan

💡 Tips: Potong kecil untuk mempercepat penguraian!"""
    
    def _get_inorganic_education(self) -> str:
        """Education about inorganic waste"""
        return """🔵 Sampah Anorganik

Jenis Utama:
• Plastik (PET, HDPE, PP, dll)
• Kertas & karton
• Logam (besi, aluminium)
• Kaca

Cara Pengolahan:
• Cuci bersih sebelum dipilah
• Lepas label & tutup
• Pisahkan berdasarkan jenis
• Kumpulkan hingga jumlah banyak

💰 Nilai Ekonomi:
• Botol plastik bening: Rp 3.000/kg
• Gelas plastik: Rp 2.500/kg
• Kertas koran: Rp 2.000/kg
• Botol kaca: Rp 500/kg

🏭 Industri Daur Ulang:
• 1 botol plastik → 7 botol baru
• 1 kaleng aluminium → 20 kaleng baru
• 1 ton kertas → 850 kg kertas baru

Hindari: Plastik kotor, kertas berminyak, kaca pecah"""
    
    def _get_hazardous_education(self) -> str:
        """Education about hazardous waste"""
        return """🔴 Sampah B3 (Berbahaya & Beracun)

Yang Termasuk:
• Baterai & aki bekas
• Lampu neon & LED
• Obat kadaluarsa
• Cat, thinner, pestisida
• Electronic waste (HP, laptop)

🏥 Bahaya Jika Salah Kelola:
• Meracuni tanah & air tanah
• Mencemari udara
• Membahayakan kesehatan
• Merusak ekosistem

Tempat Penyerahan:
• Kantor desa (Sabtu terakhir)
• Puskesmas (untuk obat)
• Toko elektronik (untuk baterai)
• Bank sampah khusus B3

Cara Aman:
• Kemas dalam wadah terpisah
• Jangan campurkan dengan sampah lain
• Beri label "B3" pada wadah
• Serahkan ke petugas terlatih

💡 Alternatif: Gunakan produk ramah lingkungan untuk mengurangi limbah B3"""
    
    def _get_default_location(self) -> str:
        """Default location info if maps data unavailable"""
        return f"""Lokasi Pengumpulan Sampah

🏛️ 1. Balai {self.village_name}
Jl. Raya Desa, RT 01/RW 01
0812-3456-7891
⏰ Senin, Rabu, Jumat (07.00-16.00)
Menerima: Organik, Anorganik

🏠 2. Pos Ronda RT 02
Jl. Masjid, RT 02/RW 01  
0812-3456-7892
⏰ Senin, Rabu, Jumat (08.00-15.00)
Menerima: Organik, Anorganik

🏥 3. Kantor Desa (Khusus B3)
Komplek Pemdes
0812-3456-7890
⏰ Sabtu terakhir (09.00-12.00)
Menerima: B3, E-waste

🗺️ Peta Lengkap:
https://maps.google.com/maps?q=-6.2088,106.8456&z=15

💡 Tips: Hubungi dulu sebelum datang untuk memastikan petugas ada"""
