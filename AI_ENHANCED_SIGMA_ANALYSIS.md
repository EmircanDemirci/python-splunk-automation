# AI-Enhanced Sigma Rule Analysis System

## 🎯 Proje Özeti

Bu proje, Sigma kurallarını MongoDB veritabanındaki mevcut kurallarla karşılaştırıp **en benzer kuralları bulan** ve **Ollama AI ile detaylı analiz yapan** gelişmiş bir sistemdir.

## 🚀 Temel Özellikler

### 1. **Akıllı Benzerlik Analizi**
- **Field Similarity**: Kural field'larının Jaccard benzerliği
- **Value Similarity**: Fuzzy string matching ile değer benzerliği
- **Weighted Scoring**: %80 value + %20 field ağırlıklı puanlama
- **Semantic Cleaning**: Dosya uzantıları ve Sigma yapılarının temizlenmesi

### 2. **Ollama AI Entegrasyonu**
- DeepSeek-R1 8B model ile profesyonel analiz
- Siber güvenlik perspektifinden kural değerlendirmesi
- IOC (Indicators of Compromise) analizi
- Kural birleştirme önerileri

### 3. **Kapsamlı Raporlama**
- Terminal çıktısı ile anlık sonuçlar
- JSON formatında detaylı veri
- Markdown formatında okunabilir raporlar
- Batch analiz desteği

## 📁 Dosya Yapısı

```
├── enhanced_sigma_comparator.py    # Ana analiz motoru (AI entegrasyonlu)
├── mongodb_connection.py           # MongoDB bağlantı yöneticisi
├── analysis_runner.py              # Analiz çalıştırıcı ve rapor oluşturucu
├── deneme_kural.yml                # Test için örnek Sigma kuralı
└── analysis_results/               # Analiz sonuçları (otomatik oluşur)
    ├── *_analysis_*.json          # JSON detayları
    └── *_report_*.md               # Markdown raporları
```

## 🔧 Kurulum ve Kullanım

### Gereksinimler
```bash
pip install pymongo pyyaml requests python-Levenshtein
```

### Ollama Kurulumu
```bash
# Ollama'yı kur
curl -fsSL https://ollama.ai/install.sh | sh

# DeepSeek R1 modelini indir
ollama pull deepseek-r1:8b
```

### Temel Kullanım

#### 1. Tek Dosya Analizi
```python
from analysis_runner import AnalysisRunner

# MongoDB bağlantısı
mongo_connection = "mongodb+srv://username:password@cluster.mongodb.net/"

# Runner'ı başlat
runner = AnalysisRunner(mongo_connection)

# Analizi çalıştır
results = runner.run_analysis(
    yaml_file_path="deneme_kural.yml",
    top_n=10,
    save_results=True
)
```

#### 2. Toplu Analiz
```python
# Bir dizindeki tüm YAML dosyalarını analiz et
runner.batch_analysis("yaml_rules_directory/", pattern="*.yml")
```

#### 3. Doğrudan Comparator Kullanımı
```python
from enhanced_sigma_comparator import EnhancedSigmaRuleComparator
from mongodb_connection import MongoConnector

# MongoDB bağlantısı
connect_mongo = MongoConnector(connection_string, "sigmaDB", "rules")
collection = connect_mongo.connect()

# Comparator'ı başlat
comparator = EnhancedSigmaRuleComparator(collection)

# Analizi çalıştır
results = comparator.compare_with_mongodb_and_analyze("deneme_kural.yml")
```

## 🧠 AI Analizi Özellikleri

### Analiz Kriterleri
1. **En Benzer Kural Tespiti**: Hangi kural gerçekten en benzer ve neden?
2. **Benzerlik Tipleri**: 
   - Aynı saldırı türü tespiti
   - Log kaynak benzerliği
   - IOC (Indicators of Compromise) analizi
3. **Farklılık Analizi**: Önemli farklılıklar ve tamamlayıcı özellikler
4. **Öneriler**: Kural birleştirme, iyileştirme önerileri
5. **Sonuç**: En benzer kuralın ID'si ve seçim gerekçesi

### AI Prompt Yapısı
```
## ANALİZ EDİLECEK KURAL:
**Başlık:** [YAML Title]
**Açıklama:** [YAML Description]
**Detection Bölümü:** [JSON Detection Rules]

## VERİTABANINDAKİ EN BENZER KURALLAR:
### 1. BENZER KURAL (Benzerlik: X%)
- Field/Value benzerlikleri
- MongoDB içeriği

[Detaylı analiz sorguları...]
```

## 📊 Çıktı Formatları

### 1. Terminal Çıktısı
```
🏆 EN BENZERLİK GÖSTEREN 10 KURAL:
================================================================================

1. 📋 Suspicious PowerShell Command Execution
   🆔 Rule ID: 60f5e8c7e12345678901234
   📊 TOPLAM BENZERLİK: 87.3%
   🔤 Value Benzerliği:  89.2%
   🏷️  Field Benzerliği:  78.1%

🤖 OLLAMA AI ANALİZ SONUÇLARI:
================================================================================
[AI'nin detaylı analizi...]
```

### 2. JSON Çıktısı
```json
{
  "analysis_timestamp": "20241215_143022",
  "yaml_rule": { /* YAML kuralının tamamı */ },
  "top_matches": [
    {
      "rule_id": "60f5e8c7e12345678901234",
      "title": "Suspicious PowerShell Command Execution",
      "weighted_similarity": 0.873,
      "field_similarity": 0.781,
      "value_similarity": 0.892
    }
  ],
  "ai_analysis": {
    "success": true,
    "analysis_text": "AI'nin detaylı analizi...",
    "analyzed_rules_count": 5
  }
}
```

### 3. Markdown Raporu
```markdown
# Sigma Rule Analysis Report

**Analysis Date:** 20241215_143022
**Source YAML:** `deneme_kural.yml`

## Analyzed Rule
**Title:** Suspicious PowerShell Command Execution
**Level:** high

## Top Similar Rules
### 1. Similar Rule Title
- **Rule ID:** `60f5e8c7e12345678901234`
- **Total Similarity:** 87.3%

## AI Analysis
**Status:** ✅ Successful
[AI analiz sonuçları...]
```

## 🔍 Akıllı Eşleştirme Algoritması

### Field Temizleme
- Sigma yapılarının çıkarılması (`selection_`, `filter_`, vb.)
- Pipe modifier'ların temizlenmesi (`Image|endswith` → `image`)
- Regex karakterlerinin normalize edilmesi

### Value Temizleme
- Dosya uzantılarının kaldırılması (`.exe`, `.dll`, vb.)
- Path separator'ların normalize edilmesi
- Gereksiz karakterlerin temizlenmesi

### Fuzzy Matching
- **SequenceMatcher** ile temel benzerlik
- **Substring bonus** (akıllı uzunluk kontrolü ile)
- **Anlamlı eşleşme filtreleme** (çok kısa/saçma eşleşmeleri engeller)
- **Token cezası** (kelime ortaklığı olan ama substring olmayan durumlar)

## ⚙️ Konfigürasyon Seçenekleri

### MongoDB Ayarları
```python
# Bağlantı string'i
MONGO_CONNECTION = "mongodb+srv://user:pass@cluster.mongodb.net/"
DATABASE_NAME = "sigmaDB"
COLLECTION_NAME = "rules"
```

### Ollama Ayarları
```python
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "deepseek-r1:8b"  # veya mevcut diğer modeller
```

### Analiz Parametreleri
```python
TOP_N = 10                    # En benzer kaç kural getirilecek
SIMILARITY_THRESHOLD = 0.5    # Minimum benzerlik eşiği (%50)
VALUE_WEIGHT = 0.8           # Value similarity ağırlığı
FIELD_WEIGHT = 0.2           # Field similarity ağırlığı
```

## 🚨 Hata Yönetimi

### MongoDB Bağlantı Hataları
- Otomatik bağlantı testi
- Connection timeout yönetimi
- Graceful error handling

### Ollama AI Hataları
- Model availability kontrolü
- Request timeout (60 saniye)
- Retry mechanism (3 deneme)
- Fallback to non-AI mode

### YAML Parse Hataları
- Encoding detection (UTF-8)
- YAML syntax validation
- Partial parsing recovery

## 📈 Performans Optimizasyonu

### Veritabanı Optimizasyonu
- Efficient MongoDB queries
- Index kullanımı önerileri
- Batch processing için pagination

### AI Optimizasyonu
- Model caching
- Prompt optimization
- Token limit management

### Memory Management
- Large dataset handling
- Incremental processing
- Result streaming

## 🔮 Gelecek Geliştirmeler

1. **Multi-Model AI Support**: Ollama dışında ChatGPT, Claude entegrasyonu
2. **Real-time Monitoring**: Sürekli yeni kural akışı izleme
3. **Advanced Visualization**: Web UI ile interaktif analiz
4. **Custom Similarity Metrics**: Domain-specific scoring algorithms
5. **Integration APIs**: SIEM ve SOC tool entegrasyonları

## 📞 Kullanım Örnekleri

### Senaryo 1: Yeni Kural Geliştirme
```python
# Yeni geliştirdiğiniz kuralın benzeri var mı?
results = runner.run_analysis("yeni_kural.yml")
if results["similar_rules_found"] > 0:
    print("⚠️ Benzer kurallar mevcut, birleştirme düşünün!")
```

### Senaryo 2: Kural Temizleme
```python
# Yedekli kuralları tespit etme
runner.batch_analysis("all_rules/", pattern="*.yml")
# Yüksek benzerlik gösteren kuralları manuel gözden geçirin
```

### Senaryo 3: Threat Hunting
```python
# Belirli bir saldırı türü için hangi kurallar var?
results = runner.run_analysis("powershell_attack.yml")
# AI analizi ile IOC'leri ve eksik noktaları görün
```

## 🎯 Sonuç

Bu sistem sayesinde:
- ✅ **Zamandan tasarruf**: Manuel kural karşılaştırması yerine otomatik analiz
- ✅ **Kalite artışı**: AI destekli profesyonel değerlendirme
- ✅ **Yedekliliği önleme**: Benzer kuralların tespiti
- ✅ **Kapsamlı raporlama**: JSON, Markdown, terminal çıktıları
- ✅ **Ölçeklenebilirlik**: Batch processing ve büyük veritabanı desteği

**VERİTABANINDAN EN BENZER KURALLARI GETİR, OLLAMA AI İLE ANALİZ ET!** 🚀