# ⚡ Basit ve Hızlı Sigma Benzerlik Analizi

**AI olmadan sadece algoritma ile çok hızlı Sigma kural benzerlik analizi**

## 🎯 Özellikler

- ⚡ **Süper Hızlı:** AI yok, sadece string algoritması
- 🎯 **İlk Eşleşmede Dur:** Benzer kural bulunca analizi durdurur
- 🏷️ **Akıllı Filtreleme:** MITRE tag'e göre önce filtreler
- 📊 **Minimum Kaynak:** Az RAM, az CPU kullanımı
- 🚀 **Anında Sonuç:** Saniyeler içinde cevap
- ❌ **AI Gerektirmez:** Ollama/LLM kurulumu gereksiz

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Repository'yi klonlayın
git clone <repo-url>
cd sigma-comparison

# Virtual environment
python -m venv venv
source venv/bin/activate

# Minimal bağımlılıklar
pip install -r requirements_simple.txt
```

### 2. Kullanım

```bash
# Komut satırı
python simple_sigma_comparator.py

# API sunucusu (port 8001)
python simple_sigma_api.py

# Test
python test_simple_sigma.py
```

## 💻 API Kullanımı

### Endpoints

- **GET /health** - Sistem durumu
- **POST /find-similar** - Benzer kural bul (JSON)
- **POST /find-similar-yaml** - Benzer kural bul (YAML)
- **GET /stats** - Hızlı istatistikler

### Örnek İstek

```bash
curl -X POST http://localhost:8001/find-similar \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_rule": {
      "title": "PowerShell Activity",
      "detection": {
        "selection": {
          "Image|endswith": "\\powershell.exe"
        },
        "condition": "selection"
      },
      "tags": ["attack.execution"]
    },
    "threshold": 0.4
  }'
```

### Örnek Yanıt

```json
{
  "success": true,
  "input_rule_title": "PowerShell Activity",
  "similar_rule": {
    "title": "PowerShell Download Cradle",
    "similarity_score": 0.67,
    "similarity_percentage": 67,
    "explanation": "Yüksek benzerlik - Benzer detection mantığı"
  },
  "processing_time_seconds": 0.15,
  "message": "Benzer kural bulundu"
}
```

## ⚡ Performans Karşılaştırması

| Özellik | AI Versiyonu | Basit Versiyon |
|---------|-------------|----------------|
| **Hız** | 20-30 saniye | 0.1-2 saniye |
| **RAM** | 2-4 GB | 50-100 MB |
| **Kurulum** | Ollama + Model | Sadece Python |
| **Doğruluk** | Çok yüksek | Yüksek |
| **Kaynak** | Yoğun | Minimal |

## 🔍 Algoritma

### 1. **MITRE Tag Filtresi**
```python
# Önce aynı MITRE tag'i olan kuralları ara
if input_tags:
    query = {"tags": {"$in": input_tags}}
```

### 2. **String Benzerlik**
```python
# SequenceMatcher ile hızlı karşılaştırma
similarity = SequenceMatcher(None, input_text, sigmahq_text).ratio()
```

### 3. **Tag Bonus**
```python
# Ortak tag'ler için bonus puan
tag_overlap = len(input_tags ∩ sigmahq_tags) / len(input_tags ∪ sigmahq_tags)
final_score = (similarity * 0.7) + (tag_overlap * 0.3)
```

### 4. **İlk Eşleşmede Dur**
```python
if similarity_score >= threshold:
    return first_match  # Burada dur!
```

## 🎯 Kullanım Senaryoları

### ✅ İdeal Durumlar
- **Hızlı SOC Operasyonları**
- **Real-time Rule Checking**
- **Batch Processing**
- **Resource-Limited Environments**
- **CI/CD Pipeline Integration**

### ❌ Uygun Olmayan Durumlar
- Semantik analiz gerekiyor
- Çok detaylı açıklama gerekiyor
- Complex rule logic comparison
- Research-grade analysis

## 📊 N8N Entegrasyonu

```json
{
  "name": "Fast Sigma Check",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8001/find-similar",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"sigma_rule\": {{ $json.rule }},\n  \"threshold\": 0.4\n}"
      },
      "name": "Fast Similar Check",
      "type": "n8n-nodes-base.httpRequest"
    }
  ]
}
```

## 🔧 Konfigürasyon

### Threshold Ayarları
- **0.2-0.3:** Çok hassas (daha fazla sonuç)
- **0.4-0.5:** Dengeli (önerilen)
- **0.6-0.8:** Sıkı (sadece çok benzer kurallar)

### Performance Tuning
```python
# MongoDB connection pool
client = MongoClient(connection_string, maxPoolSize=50)

# Index optimization (MongoDB'de)
db.rules.createIndex({"tags": 1})
db.rules.createIndex({"title": "text", "description": "text"})
```

## 📁 Dosya Yapısı

```
📦 basit-sigma/
├── 📄 simple_sigma_comparator.py  # Ana sınıf
├── 📄 simple_sigma_api.py         # FastAPI
├── 📄 test_simple_sigma.py        # Test
├── 📄 requirements_simple.txt     # Minimal deps
└── 📄 README_SIMPLE.md            # Bu dosya
```

## 🆚 AI vs Basit Versiyon

### AI Versiyonu (Eski)
```python
# Yavaş ama çok akıllı
for rule in all_rules:
    ai_score = call_ollama_api(input_rule, rule)  # 1-2 saniye
    if ai_score > threshold:
        results.append(rule)
```

### Basit Versiyon (Yeni)
```python
# Hızlı ve yeterince akıllı
for rule in filtered_rules:
    string_score = calculate_similarity(input_rule, rule)  # 0.001 saniye
    if string_score > threshold:
        return rule  # İlk eşleşmede dur!
```

## 💡 İpuçları

### Hızlandırma
1. **MITRE tag'leri kullanın** - %90 hızlanma
2. **Threshold'u 0.4+ tutun** - Gereksiz kontrolleri azaltır
3. **MongoDB indexing** - Sorgu performansı
4. **Connection pooling** - Bağlantı yeniden kullanımı

### Doğruluk Artırma
1. **Title benzerliği önemli** - Başlık aynıysa büyük bonus
2. **Detection logic'e odaklanın** - Ana karşılaştırma noktası
3. **Tag kombinasyonları** - Birden fazla ortak tag varsa yüksek skor

## ✅ Test Sonuçları

```bash
# Örnek test çıktısı
⚡ Basit ve Hızlı SigmaHQ Benzerlik Testi
🏆 BENZER KURAL BULUNDU! (⏱️ 0.23 saniye)
📈 PERFORMANS:
   ⚡ İşlem süresi: 0.23 saniye
   🔍 Analiz türü: String benzerlik (AI yok)  
   🎯 İlk eşleşmede durdu: Evet
```

## 🔄 Migration

### AI'dan Basit'e Geçiş
```python
# Eski (AI)
similar_rules = ai_comparator.find_most_similar_rules(rule, threshold=0.3, max_results=10)

# Yeni (Basit)
similar_rule = simple_comparator.find_first_similar_rule(rule, threshold=0.4)
```

## 🤝 Katkı

Bu basit versiyon minimal tutulmuştur. Katkılar:
- Performance optimizations
- Algorithm improvements
- Bug fixes
- Documentation

---

⚡ **Hızlı, basit, etkili - AI olmadan Sigma benzerlik analizi!**