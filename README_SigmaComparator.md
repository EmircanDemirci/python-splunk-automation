# Sigma Rule Comparator - Düzeltilmiş Versiyon

## 🚀 Özellikler

Bu script, bir YAML Sigma kuralını MongoDB'deki mevcut kurallarla karşılaştırır ve en benzer kuralları bulur.

### ✅ Yapılan Düzeltmeler

1. **MongoDB Bağlantı Modülü**: Eksik `mongodb_connection.py` dosyası oluşturuldu
2. **Fuzzy Similarity Hatası**: String vs liste karşılaştırma hatası düzeltildi
3. **Dosya Uzantısı Temizleme**: Value'lardan dosya uzantıları otomatik olarak kaldırılıyor
4. **Gelişmiş Hata Yönetimi**: Daha iyi exception handling ve logging
5. **Dependency Yönetimi**: PyMongo ve PyYAML bağımlılıkları eklendi

### 🧹 Dosya Uzantısı Temizleme

Script aşağıdaki dosya uzantılarını otomatik olarak value'lardan kaldırır:

- **Executable**: `.exe`, `.dll`, `.sys`, `.drv`, `.ocx`, `.cpl`, `.scr`, `.com`, `.pif`
- **Script**: `.bat`, `.cmd`, `.ps1`, `.psm1`, `.vbs`, `.js`, `.py`, `.sh`
- **Archive**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.msi`, `.cab`
- **Document**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.rtf`
- **Config/Log**: `.txt`, `.log`, `.cfg`, `.conf`, `.ini`, `.xml`, `.json`, `.yaml`
- **Image**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.ico`, `.svg`
- **Diğer**: `.tmp`, `.temp`, `.bak`, `.old`, `.orig`

### 📁 Dosya Yapısı

```
workspace/
├── sigma_rule_comparator.py   # Ana script
├── mongodb_connection.py      # MongoDB bağlantı modülü
├── deneme_kural.yml          # Test için örnek Sigma kuralı
├── requirements.txt          # Python bağımlılıkları
└── venv/                     # Virtual environment
```

## 🔧 Kurulum

1. **Virtual Environment oluştur:**
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Bağımlılıkları yükle:**
```bash
pip install pymongo pyyaml
```

## 🚀 Kullanım

```python
from sigma_rule_comparator import SigmaRuleComparator
from mongodb_connection import MongoConnector

# MongoDB bağlantısı
mongo_connection = "mongodb+srv://user:pass@cluster.mongodb.net/"
connect_mongo = MongoConnector(mongo_connection, "sigmaDB", "rules")
collection = connect_mongo.connect()

# Comparator'ı başlat
comparator = SigmaRuleComparator(collection)

# YAML dosyasını karşılaştır
results = comparator.compare_with_mongodb("deneme_kural.yml", top_n=10)
```

## 📊 Çıktı Örneği

```
📄 YAML dosyası okunuyor...
🔍 YAML'dan çıkarılan:
   Fields: ['Image|endswith', 'CommandLine|contains']
   Values: ['powershell', 'cmd', 'downloadstring', 'malware', 'evil']
------------------------------------------------------------
🔍 MongoDB'den kurallar getiriliyor...
📊 Toplam 1250 kural bulundu

🏆 EN BENZERLİK GÖSTEREN 10 KURAL:
================================================================================

1. 📋 Suspicious PowerShell Activity
   🆔 Rule ID: 507f1f77bcf86cd799439011
   📊 TOPLAM BENZERLİK: 89.5%
   🔤 Value Benzerliği:  92.1%
   🏷️  Field Benzerliği:  78.3%
```

## 🔍 Benzerlik Algoritması

- **Field Benzerliği**: Jaccard benzerliği (%20 ağırlık)
- **Value Benzerliği**: Fuzzy string matching + bonus/ceza sistemi (%80 ağırlık)
  - Substring bonus: +0.2
  - Ortak kelime cezası: -0.3 (substring değilse)

## ⚙️ Konfigürasyon

MongoDB bağlantı bilgilerini `main()` fonksiyonunda güncelleyin:

```python
mongo_connection = "your_mongodb_connection_string"
database_name = "your_database_name" 
collection_name = "your_collection_name"
```

## 🐛 Hata Giderme

- **ImportError**: Virtual environment aktif olduğundan emin olun
- **MongoDB Connection**: Bağlantı string'ini ve network erişimini kontrol edin
- **File Not Found**: YAML dosyasının doğru konumda olduğundan emin olun

## 📝 Notlar

- Script, dosya uzantılarını otomatik olarak temizler
- Path separator'ları (`\`, `/`) ve quote karakterleri kaldırılır
- MongoDB'deki tüm kurallar bellekte yüklenir (büyük koleksiyonlar için optimizasyon gerekebilir)