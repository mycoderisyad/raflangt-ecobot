# EcoBot Testing Guide

## Quick Test Commands

### 1. Test AI Image Analysis (Direct)
```bash
cd /home/azureuser/ecobot
python3 -c "
from services.ai_service import AIService
import requests
from dotenv import load_dotenv

load_dotenv()
ai = AIService()

# Test with sample waste image
url = 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400'  # plastic bottle
response = requests.get(url)
result = ai.analyze_image(response.content, '628123456789')
print('Result:', result)
"
```

### 2. Test WhatsApp Integration
1. **Send text message** ke bot: "Halo bot"
2. **Send image URL**: Kirim link gambar (https://...)  
3. **Send direct image**: Upload gambar langsung ⚠️ (currently broken)

### 3. Test Admin Commands  
```bash
# Via WhatsApp, send:
/stats           # System statistics
/users           # User list  
/help            # Admin help
```

### 4. Monitor Logs Real-time
```bash
tail -f logs/app.log
```

### 5. Check Webhook Debug
```bash
python3 webhook_debug.py
```

## Status Check Commands

### System Health
```bash
ps aux | grep python3         # Check if bot running
ls -la logs/                  # Check log files
tail -20 logs/app.log         # Recent logs
```

### Database Check
```bash
python3 -c "
from database.models.user import User
from database.models.collection import Collection
from sqlalchemy.orm import sessionmaker
from database.models.base import engine

Session = sessionmaker(bind=engine)
session = Session()

print('Users:', session.query(User).count())
print('Collections:', session.query(Collection).count())
session.close()
"
```

### Environment Variables Check
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

keys = ['LUNOS_API_KEY', 'UNLI_API_KEY', 'WAHA_API_KEY', 'WAHA_BASE_URL']
for key in keys:
    value = os.getenv(key)
    if value:
        print(f'{key}: {value[:10]}...')
    else:
        print(f'{key}: NOT SET')
"
```

## Restart Bot
```bash
pkill -f "python3.*start.py"
nohup python3 start.py > logs/app.log 2>&1 &
```

## Development Mode (with logs)
```bash
python3 start.py
```
