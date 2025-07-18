# 🎯 Detection Odaklı Sigma Benzerlik Analizi

**Sigma kurallarının detection mantığına odaklanarak hızlı benzerlik analizi**

## 🚀 Ana Özellikler

- 🎯 **Detection Odaklı:** MITRE tag'lere değil, detection içeriğine odaklanır
- ⚡ **Süper Hızlı:** İlk benzer kuralı bulunca durur
- 🔍 **Akıllı Parse:** Field'ları ve value'ları ayrı ayrı analiz eder
- 📊 **Detaylı Analiz:** Ortak field'lar ve değerleri gösterir
- 🚀 **MongoDB Ready:** SigmaHQ kuralları ile gerçek zamanlı karşılaştırma

## 🎯 Algoritma

### 1. **Detection Parse**
```python
detection = {
    "selection": {
        "Image|endswith": "\\powershell.exe",
        "CommandLine|contains": ["DownloadString", "iex"]
    }
}

# Parse sonucu:
fields = {"image", "commandline"}
values = {"\\powershell.exe", "downloadstring"}
```

### 2. **Benzerlik Hesaplama**
- **%70 Detection Content:** String benzerlik
- **%20 Field Similarity:** Ortak field'lar (Image, CommandLine, vb.)
- **%10 Value Similarity:** Ortak değerler (powershell.exe, vb.)

### 3. **MongoDB Filtreleme**
```python
# Önce aynı field'ları kullanan kuralları bul
query = {"$or": [
    {"detection.selection.image": {"$exists": True}},
    {"detection.selection.commandline": {"$exists": True}}
]}
```

## 💻 Kullanım

### Komut Satırı
```bash
python3 simple_sigma_comparator.py
```

### API (Port 8001)
```bash
python3 simple_sigma_api.py
```

### Test
```bash
python3 quick_test.py  # Algorithm test
python3 api_test.py    # API test
```

## 📊 Örnek Sonuçlar

```bash
🎯 Detection Odaklı Sigma Benzerlik Testi

🔧 DETECTION PARSE:
📝 Parse: image \powershell.exe commandline downloadstring iex selection
🏷️ Fields: {'image', 'commandline'}
💎 Values: {'\\powershell.exe', 'downloadstring'}

🔄 BENZERLIK TESTİ:
🎯 Detection Benzerliği: 75.2%
🏷️ Ortak Field'lar: {'image', 'commandline'}
💎 Ortak Value'lar: {'\\powershell.exe'}

📊 SONUÇ:
   ✅ Benzer kural: 75.2% (PowerShell)
   ❌ Farklı kural: 23.2% (Registry)
   🎯 Sistem detection odaklı çalışıyor!
```

## 🔧 API Endpoints

### POST /find-similar
```bash
curl -X POST http://localhost:8001/find-similar \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_rule": {
      "detection": {
        "selection": {
          "Image|endswith": "\\powershell.exe",
          "CommandLine|contains": ["DownloadString"]
        },
        "condition": "selection"
      }
    },
    "threshold": 0.4
  }'
```

### Response
```json
{
  "success": true,
  "similar_rule": {
    "title": "PowerShell Download Cradle",
    "similarity_percentage": 75,
    "explanation": "Yüksek detection benzerliği - Ortak field: image, commandline"
  },
  "processing_time_seconds": 0.15
}
```

## 🎯 Ne Fark Etti?

### Eski Sistem (MITRE Tag Odaklı)
```python
# MITRE tag'lere bakıyordu
similarity = tag_overlap * 0.3 + text_similarity * 0.7
```

### Yeni Sistem (Detection Odaklı)
```python
# Detection içeriğine odaklanıyor
similarity = (detection_similarity * 0.7) + 
              (field_bonus * 0.2) + 
              (value_bonus * 0.1)
```

## 📈 Performans

| Test Kuralı | Detection Benzerliği | Açıklama |
|-------------|---------------------|----------|
| PowerShell Download | 75.2% | Yüksek - Aynı field'lar |
| CMD Execution | 45.1% | Orta - Benzer field'lar |
| Registry Modification | 23.2% | Düşük - Farklı field'lar |

## ⚙️ Konfigürasyon

### Threshold Ayarları
```python
threshold = 0.4  # Dengeli (önerilen)
threshold = 0.6  # Sıkı (sadece çok benzer)
threshold = 0.2  # Gevşek (daha fazla sonuç)
```

### MongoDB Optimizasyonu
```javascript
// Önerilen index'ler
db.rules.createIndex({"detection.selection.Image": 1})
db.rules.createIndex({"detection.selection.CommandLine": 1})
db.rules.createIndex({"detection.selection.EventID": 1})
```

## 📁 Dosyalar

```
📦 detection-focused/
├── 📄 simple_sigma_comparator.py   # Ana sınıf
├── 📄 simple_sigma_api.py          # FastAPI
├── 📄 quick_test.py                # Algorithm test
├── 📄 api_test.py                  # API test
├── 📄 requirements_simple.txt      # Dependencies
└── 📄 README_DETECTION_FOCUSED.md  # Bu dosya
```

## 🔍 Detection Parsing Detayları

### Field Çıkarma
```python
# Input: "Image|endswith": "\\powershell.exe"
# Output: field = "image", value = "\\powershell.exe"

fields = {"image", "commandline", "eventid"}
```

### Value Çıkarma
```python
# Önemli değerleri filtreler:
# - Dosya uzantıları: .exe, .dll, .ps1
# - 3+ karakter string'ler
# - Path'ler ve komutlar

values = {"\\powershell.exe", "downloadstring", "invoke-expression"}
```

### Bonus Sistem
```python
# Field bonus: Ortak field sayısı / toplam field sayısı
field_bonus = len(common_fields) / len(all_fields)

# Value bonus: Ortak value sayısı / toplam value sayısı  
value_bonus = len(common_values) / len(all_values)
```

## 🎯 Kullanım Senaryoları

### ✅ İdeal
- **SOC Rule Development:** Yeni kuralda benzer detection var mı?
- **Rule Optimization:** Hangi field'lar daha etkili?
- **Duplicate Detection:** Aynı detection mantığı tekrar mı yazılmış?

### 🔍 Analiz Örnekleri
```python
# PowerShell kuralları
fields: {"image", "commandline"} 
values: {"powershell.exe", "downloadstring"}
→ 75%+ benzerlik

# Registry kuralları  
fields: {"eventid", "targetobject"}
values: {"currentversion\\run"}
→ 20%- benzerlik (farklı kategori)
```

---

🎯 **Detection mantığına odaklanarak daha akıllı Sigma benzerlik analizi!**