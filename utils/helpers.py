"""
Utility functions and helpers for EcoBot
"""

import os
import logging
import requests
import re
from io import BytesIO
from PIL import Image
import mimetypes

logger = logging.getLogger(__name__)

def is_image_message(content_type):
    """Check if the message contains an image"""
    if not content_type:
        return False
    return content_type.startswith('image/')

def download_image(media_url):
    """Download image from URL and return image data"""
    try:
        response = requests.get(media_url, timeout=30)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if not is_image_message(content_type):
            logger.warning(f"Invalid content type: {content_type}")
            return None
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        content_length = len(response.content)
        if content_length > max_size:
            logger.warning(f"Image too large: {content_length} bytes")
            return None
        
        # Validate image can be opened
        try:
            image = Image.open(BytesIO(response.content))
            image.verify()  # Verify it's a valid image
            return response.content
        except Exception as e:
            logger.error(f"Invalid image file: {str(e)}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {str(e)}")
        return None

def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove whitespace and special characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it's a valid WhatsApp number format
    # Should start with + and have 10-15 digits
    pattern = r'^\+\d{10,15}$'
    return bool(re.match(pattern, cleaned))

def format_phone_number(phone):
    """Format phone number to international format"""
    if not phone:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If starts with 0, replace with +62 (Indonesia)
    if cleaned.startswith('0'):
        cleaned = '+62' + cleaned[1:]
    elif not cleaned.startswith('+'):
        # Assume it's Indonesian number without country code
        cleaned = '+62' + cleaned
    
    return cleaned if validate_phone_number(cleaned) else None

def safe_get_env(key, default=None, required=False):
    """Safely get environment variable with validation"""
    value = os.getenv(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    
    return value

def log_user_interaction(user_phone, message_type, content=None):
    """Log user interaction for analytics"""
    try:
        log_data = {
            'timestamp': str(datetime.now()),
            'user_phone': user_phone,
            'message_type': message_type,
            'content_preview': content[:50] + '...' if content and len(content) > 50 else content
        }
        logger.info(f"User interaction: {log_data}")
        
        # Could save to database or analytics service
        return True
        
    except Exception as e:
        logger.error(f"Error logging user interaction: {str(e)}")
        return False

def sanitize_text(text):
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized.strip()

def compress_image(image_data, max_size=(800, 600), quality=85):
    """Compress image to reduce size"""
    try:
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Resize if too large
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save with compression
        output = BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        return image_data  # Return original if compression fails

def get_file_extension(filename):
    """Get file extension from filename"""
    if not filename:
        return None
    
    _, ext = os.path.splitext(filename.lower())
    return ext

def is_supported_image_format(filename_or_content_type):
    """Check if image format is supported"""
    supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    supported_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    if filename_or_content_type.startswith('image/'):
        return filename_or_content_type in supported_mimes
    else:
        ext = get_file_extension(filename_or_content_type)
        return ext in supported_formats

def create_error_response(error_message, error_code=None):
    """Create standardized error response"""
    return {
        'success': False,
        'error': error_message,
        'error_code': error_code,
        'timestamp': datetime.now().isoformat()
    }

def create_success_response(data=None, message=None):
    """Create standardized success response"""
    response = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    
    if data:
        response['data'] = data
    if message:
        response['message'] = message
    
    return response

def retry_operation(func, max_retries=3, delay=1):
    """Retry operation with exponential backoff"""
    import time
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_system_info():
    """Get basic system information for health checks"""
    import platform
    import psutil
    
    try:
        return {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    except ImportError:
        return {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'status': 'basic_info_only'
        }

def validate_api_key(api_key, service_name):
    """Validate API key format"""
    if not api_key:
        logger.warning(f"No API key provided for {service_name}")
        return False
    
    # Basic validation - should be at least 20 characters
    if len(api_key) < 20:
        logger.warning(f"API key for {service_name} seems too short")
        return False
    
    return True

def mask_sensitive_data(data, fields_to_mask=None):
    """Mask sensitive data in logs"""
    if fields_to_mask is None:
        fields_to_mask = ['api_key', 'token', 'password', 'secret']
    
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in fields_to_mask):
                masked[key] = '*' * 8 if value else None
            else:
                masked[key] = mask_sensitive_data(value, fields_to_mask)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item, fields_to_mask) for item in data]
    else:
        return data

# Import datetime for timestamp functions
from datetime import datetime
