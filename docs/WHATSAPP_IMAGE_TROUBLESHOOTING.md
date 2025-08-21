# WhatsApp Image Analysis Troubleshooting

## Issue Identified
✅ **Image analysis bekerja** dengan CLI testing  
❌ **Image analysis tidak bekerja** saat kirim gambar langsung via WhatsApp  
✅ **Link gambar bisa dianalisis** dengan baik

## Root Cause Analysis

### 1. **API Format Fixed** ✅
Updated unli.dev request format sesuai dokumentasi:
```json
{
  "model": "auto",                    // Fixed: use "auto" not env variable
  "messages": [
    {
      "role": "user",                 // Fixed: no system message
      "content": [
        {
          "type": "image_url",        // Fixed: image_url first
          "image_url": {
            "url": "data:image/jpeg;base64,..."
          }
        },
        {
          "type": "text",             // Fixed: text after image
          "text": "prompt here"
        }
      ]
    }
  ]
}
```

### 2. **WhatsApp Image Download Issue** ❌
**Problem**: Media download dari WAHA API gagal dengan 404 error
**Symptoms**: 
- Webhook received ✅
- Message type detected as 'image' ✅  
- Media URL provided ✅
- Download failed dengan 404 ❌

## Debugging Steps

### 1. Check Webhook Data
```bash
# Monitor webhook untuk image messages
tail -f logs/app.log | grep -i "image\|media\|download"
```

### 2. Test Media Download Manually
```bash
# Check WAHA media endpoint
curl -H "X-API-Key: YOUR_API_KEY" \
     "https://waha.rafgt.my.id/api/files/SESSION/FILENAME"
```

### 3. Verify WAHA Configuration
```env
WAHA_BASE_URL=https://waha.rafgt.my.id/api
WAHA_API_KEY=your_api_key_here
WAHA_SESSION_NAME=default
```

## Potential Solutions

### Option 1: Fix WAHA Media Download
**Check if WAHA endpoint for media is correct:**
```
Expected: https://waha.rafgt.my.id/api/files/{session}/{filename}
Actual URL from webhook: {check logs}
```

### Option 2: Alternative Download Method
WAHA might use different endpoint format:
```
/api/{session}/files/{messageId}
/api/files/{session}/{messageId}  
/api/media/{session}/{messageId}
```

### Option 3: Direct File Processing
If WAHA provides file content in webhook:
```json
{
  "payload": {
    "type": "image",
    "media": {
      "data": "base64_content_here",
      "url": "http://...",
      "mimetype": "image/jpeg"
    }
  }
}
```

## Current Status

### ✅ **Working Components**
- Unli.dev API integration with correct format
- OpenAI client setup and fallback
- Image bytes processing (temp file handling)
- Webhook message type detection  
- CLI testing dengan sample images

### ❌ **Issue Remaining**
- **WAHA media download 404 error**
- Need to fix media URL format or authentication

## Testing Commands

### Test Image Analysis (works)
```bash
cd /home/azureuser/ecobot
python3 -c "
from services.ai_service import AIService
import requests
from dotenv import load_dotenv

load_dotenv()
ai = AIService()

# Test with URL
url = 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400'
response = requests.get(url)
result = ai.analyze_image(response.content, '628123456789')
print(result)
"
```

### Monitor WhatsApp Webhooks
```bash
# Watch for incoming image messages
tail -f logs/app.log | grep -E "(image|media|download|404)"
```

### Test Webhook Format
```bash
python3 webhook_debug.py
```

## Next Steps

1. **Identify correct WAHA media URL format**
2. **Check WAHA authentication for media download**  
3. **Test alternative WAHA endpoints**
4. **Consider webhook base64 content if available**

## Workaround
**Currently working**: Kirim link gambar instead of file upload
**Target**: Fix direct image upload processing via WAHA media API
