# Sigma to Splunk Automation Tool

Bu otomasyon sistemi, YAML formatındaki Sigma kurallarını Splunk sorgularına dönüştüren bir REST API sağlar. POST istekleri ile Sigma kuralları gönderebilir ve karşılığında Splunk sorguları alabilirsiniz.

## 🚀 Özellikler

- **REST API**: FastAPI tabanlı modern REST API
- **Tekil Dönüştürme**: Bir Sigma kuralını POST ile gönderip Splunk sorgusuna dönüştürün
- **Toplu Dönüştürme**: Birden fazla Sigma kuralını tek istekte dönüştürün
- **Web Arayüzü**: Streamlit tabanlı kullanıcı dostu arayüz (mevcut)
- **Otomatik Dokümantasyon**: OpenAPI/Swagger UI desteği
- **Hata Yönetimi**: Detaylı hata mesajları ve loglama
- **CORS Desteği**: Cross-origin istekleri için CORS desteği

## 📋 Gereksinimler

```bash
pip install -r requirements.txt
```

## 🔧 Kurulum ve Çalıştırma

### 1. REST API Sunucusu

```bash
# API sunucusunu başlat
python api_server.py

# Veya uvicorn ile
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

API şu adreste çalışacak: `http://localhost:8000`

### 2. Streamlit Web Arayüzü (Opsiyonel)

```bash
streamlit run streamlit_app.py
```

## 📖 API Kullanımı

### Endpoint'ler

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/health` | GET | API sağlık durumu |
| `/convert` | POST | Tekil Sigma kuralı dönüştürme |
| `/convert-batch` | POST | Toplu Sigma kuralı dönüştürme |
| `/example` | GET | Örnek Sigma kuralı al |
| `/backends` | GET | Desteklenen backend'leri listele |
| `/docs` | GET | API dokümantasyonu (Swagger UI) |

### 1. Tekil Dönüştürme

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_rule": "title: Test Rule\ndescription: Test detection rule\nlogsource:\n  category: process_creation\n  product: windows\ndetection:\n  selection:\n    Image|endswith: \"\\\\cmd.exe\"\n  condition: selection\nlevel: medium",
    "metadata": {
      "request_id": "12345",
      "user": "test_user"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Sigma kuralı başarıyla 1 Splunk sorgusuna dönüştürüldü",
  "queries": [
    "source=\"WinEventLog:Microsoft-Windows-Sysmon/Operational\" EventCode=1 Image=\"*\\\\cmd.exe\""
  ],
  "rule_info": {
    "title": "Test Rule",
    "description": "Test detection rule",
    "level": "medium",
    "author": "N/A"
  },
  "metadata": {
    "request_id": "12345",
    "user": "test_user"
  }
}
```

### 2. Toplu Dönüştürme

```bash
curl -X POST "http://localhost:8000/convert-batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "sigma_rule": "title: CMD Detection\nlogsource:\n  category: process_creation\n  product: windows\ndetection:\n  selection:\n    Image|endswith: \"\\\\cmd.exe\"\n  condition: selection\nlevel: low",
      "metadata": {"rule_id": "rule1"}
    },
    {
      "sigma_rule": "title: PowerShell Detection\nlogsource:\n  category: process_creation\n  product: windows\ndetection:\n  selection:\n    Image|endswith: \"\\\\powershell.exe\"\n  condition: selection\nlevel: medium",
      "metadata": {"rule_id": "rule2"}
    }
  ]'
```

### 3. Python ile Kullanım

```python
import requests

# API base URL
api_url = "http://localhost:8000"

# Sigma kuralı
sigma_rule = """
title: Suspicious Process Creation
description: Detects suspicious process creation
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\cmd.exe'
        CommandLine|contains: 'whoami'
    condition: selection
level: medium
"""

# POST isteği gönder
response = requests.post(
    f"{api_url}/convert",
    json={
        "sigma_rule": sigma_rule,
        "metadata": {"user": "analyst", "case_id": "case-123"}
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Başarılı: {result['message']}")
    for i, query in enumerate(result['queries'], 1):
        print(f"Splunk Query {i}: {query}")
else:
    print(f"❌ Hata: {response.status_code} - {response.text}")
```

## 🧪 Test Etme

API'yi test etmek için test scriptini çalıştırın:

```bash
python test_api.py
```

## 📋 Request/Response Modelleri

### SigmaConvertRequest
```json
{
  "sigma_rule": "string (YAML formatında Sigma kuralı)",
  "metadata": {
    "request_id": "string",
    "user": "string",
    "custom_field": "any"
  }
}
```

### SigmaConvertResponse
```json
{
  "success": "boolean",
  "message": "string",
  "queries": ["string array"],
  "rule_info": {
    "title": "string",
    "description": "string",
    "author": "string",
    "level": "string",
    "tags": ["string array"]
  },
  "metadata": "object"
}
```

## 🔍 Örnek Sigma Kuralları

### Basit Process Detection
```yaml
title: CMD Execution Detection
description: Detects cmd.exe execution
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\cmd.exe'
  condition: selection
level: low
```

### Gelişmiş Detection
```yaml
title: Suspicious PowerShell Commands
description: Detects suspicious PowerShell command usage
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - 'Invoke-Expression'
      - 'DownloadString'
      - 'EncodedCommand'
  condition: selection
falsepositives:
  - Legitimate administrative scripts
level: high
tags:
  - attack.execution
  - attack.t1059.001
```

## 🛠️ Hata Ayıklama

### Yaygın Hatalar

1. **YAML Parse Hatası**: Sigma kuralı geçerli YAML formatında değil
2. **Geçersiz Sigma Formatı**: Sigma kuralı standartlara uygun değil
3. **Backend Hatası**: Splunk dönüştürme sırasında hata

### Log Takibi

API logları konsola yazdırılır:
```bash
INFO:__main__:Sigma dönüştürme isteği alındı. Metadata: {'user': 'test'}
INFO:__main__:Başarıyla 1 Splunk sorgusu oluşturuldu
```

## 🌐 API Dokümantasyonu

API çalıştığında şu adreslerde dokümantasyon mevcuttur:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🚀 Production Deployment

Production ortamında çalıştırmak için:

```bash
# Güvenlik için host ve port ayarları
uvicorn api_server:app --host 127.0.0.1 --port 8000 --workers 4

# HTTPS ile
uvicorn api_server:app --host 0.0.0.0 --port 443 --ssl-keyfile=/path/to/key.pem --ssl-certfile=/path/to/cert.pem
```

## 📝 Lisans

Bu proje educational amaçlı geliştirilmiştir.
