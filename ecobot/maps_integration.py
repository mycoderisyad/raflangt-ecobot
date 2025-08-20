"""
Maps Integration Module
Integrasi dengan Google Maps untuk menampilkan titik pengumpulan sampah
"""

import os
import logging
import googlemaps
from datetime import datetime, timedelta
from utils.message_loader import message_loader

logger = logging.getLogger(__name__)

class MapsIntegration:
    """Google Maps integration for waste collection points"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.village_name = os.getenv('VILLAGE_NAME', 'Desa Cukangkawung')
        self.village_coords = self._parse_coordinates(
            os.getenv('VILLAGE_COORDINATES', '-6.2088,106.8456')
        )
        self.maps_data = message_loader.get_maps_data()
        
        # Load URLs from environment variables
        self.static_map_url = os.getenv('GOOGLE_MAPS_STATIC_URL')
        self.directions_url = os.getenv('GOOGLE_MAPS_DIRECTIONS_URL')
        self.view_url = os.getenv('GOOGLE_MAPS_VIEW_URL')

        if self.api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.api_key)
                self.use_mock = False
            except Exception as e:
                logger.warning(f"Google Maps API error: {str(e)}. Using mock data.")
                self.use_mock = True
        else:
            logger.warning("Google Maps API key not found. Using mock data.")
            self.use_mock = True
        
        # Load collection points from JSON data
        self.collection_points = self._load_collection_points()
        
        logger.info("Maps Integration initialized")
    
    def _load_collection_points(self):
        """Load collection points from JSON data with proper structure"""
        locations = self.maps_data.get('collection_points', {}).get('locations', [])
        collection_points = []
        
        for location in locations:
            # Convert JSON structure to expected format
            point = {
                'id': location.get('id', ''),
                'name': location.get('name', ''),
                'type': location.get('type', ''),
                'lat': location.get('coordinates', [0, 0])[0],
                'lng': location.get('coordinates', [0, 0])[1],
                'accepted_waste': location.get('accepted_waste', []),
                'schedule': location.get('schedule', ''),
                'contact': location.get('contact', ''),
                'description': location.get('description', ''),
                'address': location.get('address', '')
            }
            collection_points.append(point)
        
        return collection_points
    
    def get_collection_points_map(self):
        """Generate Google Maps URL with collection points"""
        try:
            if self.use_mock:
                return self._generate_mock_map_url()
            
            collection_points = self.maps_data.get('collection_points', {}).get('locations', [])
            markers = []
            
            for point in collection_points:
                color = self._get_marker_color(point.get('types', []))
                coords = point.get('coordinates', [0, 0])
                marker = f"{coords[0]},{coords[1]}"
                markers.append(f"color:{color}|label:P|{marker}")
            
            params = {
                'size': '800x600',
                'zoom': '15',
                'center': f"{self.village_coords['lat']},{self.village_coords['lng']}",
                'markers': '|'.join(markers),
                'key': self.api_key
            }
            
            # Build URL
            url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
            static_map_url = f"{self.static_map_url}?{url_params}"
            
            # Also create interactive map URL
            interactive_url = self._generate_interactive_map_url()
            
            return interactive_url
            
        except Exception as e:
            logger.error(f"Error generating map URL: {str(e)}")
            return self._generate_mock_map_url()
    
    def _generate_interactive_map_url(self):
        """Generate interactive Google Maps URL"""
        # Center coordinates
        center_lat, center_lng = self.village_coords['lat'], self.village_coords['lng']
        
        # Create waypoints for all collection points
        waypoints = []
        for point in self.collection_points:
            waypoints.append(f"{point['lat']},{point['lng']}")
        
        # Generate URL
        waypoints_str = '/'.join(waypoints)
        
        # Alternative: Use My Maps or custom map
        # For now, use simple maps with center location
        simple_url = f"{self.view_url}{center_lat},{center_lng},15z"
        
        return simple_url
    
    def _generate_mock_map_url(self):
        """Generate mock map URL when API is not available"""
        mock_data = self.maps_data.get('mock_response', {})
        center_lat, center_lng = self.village_coords['lat'], self.village_coords['lng']
        default_template = os.getenv('GOOGLE_MAPS_MOCK_TEMPLATE')
        url_template = mock_data.get('url_template', default_template)
        return url_template.format(lat=center_lat, lng=center_lng)
    
    def get_collection_points_list(self):
        """Get detailed list of collection points"""
        return self.collection_points
    
    def get_nearest_collection_point(self, user_lat, user_lng, waste_type=None):
        """Find nearest collection point that accepts specific waste type"""
        try:
            valid_points = []
            
            for point in self.collection_points:
                # Filter by waste type if specified
                if waste_type and waste_type not in point['accepted_waste']:
                    continue
                
                # Calculate distance
                distance = self._calculate_distance(
                    user_lat, user_lng, point['lat'], point['lng']
                )
                point_with_distance = point.copy()
                point_with_distance['distance'] = distance
                valid_points.append(point_with_distance)
            
            # Sort by distance
            valid_points.sort(key=lambda x: x['distance'])
            
            return valid_points[0] if valid_points else None
            
        except Exception as e:
            logger.error(f"Error finding nearest point: {str(e)}")
            return None
    
    def get_collection_schedule(self, point_id=None):
        """Get collection schedule for specific point or all points"""
        if point_id:
            point = next((p for p in self.collection_points if p['id'] == point_id), None)
            if point:
                return {
                    'point': point['name'],
                    'schedule': point['schedule'],
                    'waste_types': point['accepted_waste']
                }
            return None
        else:
            # Return all schedules
            schedules = []
            for point in self.collection_points:
                schedules.append({
                    'id': point['id'],
                    'name': point['name'],
                    'schedule': point['schedule'],
                    'waste_types': point['accepted_waste']
                })
            return schedules
    
    def get_waste_type_locations(self, waste_type):
        """Get all collection points that accept specific waste type"""
        matching_points = [
            point for point in self.collection_points 
            if waste_type in point['accepted_waste']
        ]
        return matching_points
    
    def format_collection_points_message(self, waste_type=None):
        """Format collection points info for WhatsApp message"""
        messages = message_loader.get_whatsapp_messages()
        format_config = messages.get('collection_points_format', {})
        
        if waste_type:
            points = self.get_waste_type_locations(waste_type)
            title_template = format_config.get('title_specific', '**Titik Pengumpulan Sampah {waste_type}**')
            title = title_template.format(waste_type=waste_type.upper()) + "\n\n"
        else:
            points = self.collection_points
            title = format_config.get('title_all', '**Semua Titik Pengumpulan Sampah**') + "\n\n"
        
        if not points:
            return messages.get('error_messages', {}).get('no_collection_points', f'Maaf, tidak ada titik pengumpulan untuk sampah {waste_type}.')
        
        labels = format_config.get('labels', {})
        icons = format_config.get('icons', {})
        message = title
        
        for i, point in enumerate(points, 1):
            # Waste type icons
            waste_icons = []
            for waste in point['accepted_waste']:
                if waste in icons:
                    waste_icons.append(icons[waste])
            
            message += f"**{i}. {point['name']}**\n"
            message += f"   {labels.get('type', 'Tipe:')} {point['type']}\n"
            message += f"   {labels.get('waste_types', 'Jenis:')} {' '.join(waste_icons)} {', '.join(point['accepted_waste'])}\n"
            message += f"   {labels.get('schedule', 'Jadwal:')} {point['schedule']}\n"
            message += f"   {labels.get('contact', 'Kontak:')} {point['contact']}\n"
            message += f"   {labels.get('description', 'Info:')} {point['description']}\n\n"
        
        # Add map link
        map_url = self.get_collection_points_map()
        map_label = format_config.get('map_link', '**Lihat di Peta:**')
        message += f"{map_label} {map_url}\n\n"
        
        # Add legend
        legend = format_config.get('legend', {})
        message += f"{legend.get('title', '**Keterangan:**')}\n"
        message += f"{legend.get('items', 'Organik | Anorganik | B3 (Berbahaya)')}\n\n"
        message += format_config.get('footer', 'Pastikan sampah bersih dan terpilah sebelum dibuang!')
        
        return message
    
    def _parse_coordinates(self, coord_string):
        """Parse coordinate string to lat/lng dict"""
        try:
            lat, lng = coord_string.split(',')
            return {'lat': float(lat), 'lng': float(lng)}
        except:
            # Default to Jakarta coordinates
            return {'lat': -6.2088, 'lng': 106.8456}
    
    def _get_marker_color(self, accepted_waste):
        """Get marker color based on accepted waste types"""
        if 'b3' in accepted_waste:
            return 'red'
        elif 'organik' in accepted_waste and 'anorganik' in accepted_waste:
            return 'green'
        elif 'organik' in accepted_waste:
            return 'yellow'
        elif 'anorganik' in accepted_waste:
            return 'blue'
        else:
            return 'gray'
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates (Haversine formula)"""
        import math
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        
        return c * r
    
    def get_directions_url(self, user_lat, user_lng, point_id):
        """Get Google Maps directions URL to specific collection point"""
        point = next((p for p in self.collection_points if p['id'] == point_id), None)
        if not point:
            return None
        
        directions_url = (
            f"{self.directions_url}{user_lat},{user_lng}/"
            f"{point['lat']},{point['lng']}"
        )
        
        return directions_url
    
    def is_collection_point_open(self, point_id):
        """Check if collection point is currently open"""
        point = next((p for p in self.collection_points if p['id'] == point_id), None)
        if not point:
            return False
        
        # Simple implementation - could be enhanced with proper schedule parsing
        now = datetime.now()
        current_day = now.strftime('%A').lower()
        current_hour = now.hour
        
        schedule = point['schedule'].lower()
        
        # Basic day checking
        day_mapping = {
            'monday': 'senin', 'tuesday': 'selasa', 'wednesday': 'rabu',
            'thursday': 'kamis', 'friday': 'jumat', 'saturday': 'sabtu',
            'sunday': 'minggu'
        }
        
        english_day = {v: k for k, v in day_mapping.items()}.get(current_day, current_day)
        
        # Check if current day is in schedule
        if any(day in schedule for day in [current_day, english_day]):
            if 8 <= current_hour <= 16:
                return True
        
        return False
