# 🎯 Tek Sigma Kuralı - SigmaHQ Benzerlik Analizi

**Tek bir Sigma kuralı ile MongoDB'deki SigmaHQ kuralları arasında AI destekli benzerlik analizi yapan sistem**

## 📋 Özellikler

- ✅ **Tek Kural Analizi:** Bir Sigma kuralı verin, en benzer SigmaHQ kurallarını bulun
- 🤖 **AI Destekli:** Ollama ile LLaMA 3.1/Mistral modelleri kullanarak semantik analiz
- 📊 **MongoDB Entegrasyonu:** SigmaHQ kuralları MongoDB'de saklanır
- 🚀 **FastAPI REST API:** N8N ve diğer sistemlerle entegrasyon için
- 🎯 **Akıllı Scoring:** Detection mantığı, MITRE tags, log source benzerliği
- 📝 **AI Özetleri:** Her benzer kural için detaylı açıklama

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler

```bash
# Python 3.8+
python --version

# Ollama kurulumu
curl -fsSL https://ollama.ai/install.sh | sh

# AI model indirin
ollama pull llama3.1
```

### 2. Kurulum

```bash
# Repository'yi klonlayın
git clone <repo-url>
cd sigma-comparison

# Virtual environment oluşturun
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Başlatma

```bash
# Terminal 1: Ollama servisini başlatın
ollama serve

# Terminal 2: API sunucusunu başlatın
python single_sigma_api.py

# Terminal 3: Test edin
python test_single_sigma.py
```

## 💻 Kullanım

### 🖥️ Komut Satırı

```bash
# İnteraktif mod
python single_sigma_comparator.py

# Test scripti
python test_single_sigma.py
```

### 🌐 API Kullanımı

**Sistem Durumu:**
```bash
curl http://localhost:8000/health
```

**Sigma Analizi (JSON):**
```bash
curl -X POST http://localhost:8000/analyze-sigma \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_rule": {
      "title": "PowerShell Download",
      "detection": {
        "selection": {
          "Image|endswith": "\\powershell.exe",
          "CommandLine|contains": ["DownloadString"]
        },
        "condition": "selection"
      }
    },
    "threshold": 0.3,
    "max_results": 5
  }'
```

**Sigma Analizi (YAML):**
```bash
curl -X POST http://localhost:8000/analyze-sigma-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_yaml": "title: Test Rule\ndetection:\n  selection:\n    Image: powershell.exe\n  condition: selection",
    "threshold": 0.4
  }'
```

## 📊 Örnek Yanıt

```json
{
  "success": true,
  "input_rule_title": "PowerShell Download",
  "similar_rules": [
    {
      "rule_id": "64a1b2c3d4e5f6789abcdef1",
      "title": "PowerShell Download Cradle",
      "similarity_score": 0.87,
      "similarity_percentage": 87,
      "tags": ["attack.execution", "attack.t1059.001"],
      "level": "high",
      "author": "Florian Roth",
      "ai_summary": "Bu kural da PowerShell ile download aktivitelerini tespit eder. Detection mantığı ve MITRE teknikleri çok benzer."
    }
  ],
  "total_analyzed": 2847,
  "processing_time_seconds": 24.5
}
```

## 🎯 AI Benzerlik Skorları

- **0.9-1.0:** Neredeyse identik kurallar
- **0.8-0.9:** Aynı tekniği farklı şekilde tespit ediyor
- **0.6-0.7:** Benzer saldırı kategorisi, farklı implementation
- **0.4-0.5:** Aynı MITRE technique, farklı yaklaşım
- **0.2-0.3:** Aynı log source, farklı amaç
- **0.0-0.1:** Tamamen farklı

## 🔄 N8N Entegrasyonu

Detaylı N8N entegrasyon kılavuzu için: [N8N_Single_Sigma_Guide.md](N8N_Single_Sigma_Guide.md)

**Temel N8N Workflow:**
1. HTTP Request → `/analyze-sigma`
2. Function Node → Sonuçları formatla
3. IF Node → Yüksek benzerlik kontrolü
4. Email/Slack → Alert gönder

## 📁 Dosya Yapısı

```
📦 sigma-comparison/
├── 📄 single_sigma_comparator.py    # Ana karşılaştırma sınıfı
├── 📄 single_sigma_api.py          # FastAPI sunucusu
├── 📄 test_single_sigma.py         # Test scripti
├── 📄 requirements.txt             # Python bağımlılıkları
├── 📄 N8N_Single_Sigma_Guide.md    # N8N entegrasyon kılavuzu
└── 📄 README_TR.md                 # Bu dosya
```

## ⚙️ Konfigürasyon

### MongoDB Ayarları
```python
MONGO_CONNECTION = "mongodb+srv://user:pass@cluster.mongodb.net/"
DATABASE_NAME = "sigmaDB"
COLLECTION_NAME = "rules"
```

### Ollama Ayarları
```python
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1"  # veya "mistral"
```

### API Ayarları
```python
# API sunucu portu
PORT = 8000

# Benzerlik eşikleri
DEFAULT_THRESHOLD = 0.3
MAX_RESULTS = 10
```

## 🛠️ Özelleştirme

### Yeni AI Model Ekleme
```python
# single_sigma_comparator.py içinde
class SigmaHQComparator:
    def __init__(self, ..., model_name="yeni-model"):
        self.model_name = model_name
```

### Benzerlik Kriterlerini Değiştirme
```python
def calculate_content_similarity(self, ...):
    prompt = f"""
    Özel değerlendirme kriterleri:
    - Detection mantığı (%60)
    - Log source (%25)
    - MITRE tags (%15)
    """
```

### Yeni Endpoint Ekleme
```python
# single_sigma_api.py içinde
@app.post("/custom-endpoint")
async def custom_analysis(request: CustomRequest):
    # Özel analiz mantığı
    pass
```

## 🔍 Troubleshooting

### ❌ Yaygın Hatalar

**1. "Ollama bağlantısı kurulamadı"**
```bash
# Çözüm
ollama serve
curl http://localhost:11434/api/tags
```

**2. "MongoDB bağlantı hatası"**
```bash
# MongoDB connection string'i kontrol edin
# Ağ bağlantısını test edin
```

**3. "detection bölümü gerekli"**
```yaml
# Sigma rule'da mutlaka detection bölümü olmalı
detection:
  selection:
    field: value
  condition: selection
```

**4. "AI model bulunamadı"**
```bash
# Model'i indirin
ollama pull llama3.1
ollama list
```

## 📈 Performans İpuçları

### ⚡ Hızlandırma
- **Threshold artırın:** 0.5+ daha az kural analiz eder
- **Max results sınırlayın:** Sadece gerekli kadar sonuç
- **Hafif model kullanın:** `llama3.1` `mistral`'den hızlı
- **Rate limiting:** Büyük batch'lerde bekleme süresi ekleyin

### 🔧 Optimizasyon
```python
# Paralel işleme için
import asyncio
import aiohttp

# Caching için  
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_similarity(rule_hash):
    # Hesaplanan benzerlik skorlarını önbelleğe al
    pass
```

## 🎯 Kullanım Senaryoları

### 1. **SOC Rule Development**
- Yeni kural yazarken benzer olanları bulma
- Duplicate rule kontrolü
- Best practice referansları

### 2. **Threat Intelligence**
- Yeni IOC'lar için detection pattern'i bulma
- Coverage gap analizi
- Rule effectiveness ölçümü

### 3. **Security Training**
- Sigma rule yazma eğitiminde örnek bulma
- Community standartlarını öğrenme
- MITRE mapping referansları

### 4. **Compliance & Audit**
- Detection coverage assessment
- Rule quality kontrolü
- Redundancy analizi

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b yeni-ozellik`
3. Commit yapın: `git commit -am 'Yeni özellik ekle'`
4. Push yapın: `git push origin yeni-ozellik`
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 Destek

- 🐛 **Bug Report:** GitHub Issues
- 💡 **Feature Request:** GitHub Discussions  
- 📧 **Email:** your-email@domain.com
- 📖 **Dokümantasyon:** [Wiki](link-to-wiki)

## 🏆 Teşekkürler

- **SigmaHQ Community:** Açık kaynak Sigma kuralları için
- **Ollama Team:** Local AI model desteği için
- **MongoDB:** Veritabanı altyapısı için
- **FastAPI:** Modern API framework için

---

🎯 **Tek bir Sigma kuralınız mı var? En benzer SigmaHQ kurallarını AI ile bulun!**