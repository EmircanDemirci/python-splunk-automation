# 🔍 Basit YAML Karşılaştırma Uygulaması

Python ile yazılmış, JSON dosya depolama ve mock AI kullanarak YAML dosyalarını akıllı bir şekilde karşılaştıran uygulama.

## ✨ Özellikler

- ✅ **Kolay Kurulum**: MongoDB veya Ollama AI gerektirmez
- 🗂️ **JSON Depolama**: Kurallar basit JSON dosyasında saklanır  
- 🤖 **Mock AI Analizi**: Gerçekçi AI analizleri mock olarak üretilir
- 📊 **Benzerlik Skoru**: Matematiksel benzerlik hesaplaması
- 📋 **Detaylı Rapor**: Farklar ve benzerlikler detayında listelenir  
- 🌐 **Web Arayüzü**: Modern ve kullanıcı dostu web interface
- 💻 **Konsol Desteği**: Terminal üzerinden de kullanılabilir
- 🚀 **Hızlı Test**: Hiçbir dış bağımlılık gerektirmez

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.8+
- Virtual environment (önerilen)

### Kurulum

1. **Repository'yi klonlayın**
```bash
git clone <your-repo>
cd yaml-comparator
```

2. **Virtual environment oluşturun**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install fastapi uvicorn pydantic pyyaml
```

### Kullanım

#### 🌐 Web Arayüzü
```bash
source venv/bin/activate
python simple_web_interface.py
```
Tarayıcınızda `http://localhost:8000` adresini açın.

#### 💻 Konsol Uygulaması
```bash
source venv/bin/activate
python simple_yaml_comparator.py
```

## 📋 Test Örneği

Aşağıdaki YAML içeriğini test edebilirsiniz:

```yaml
server:
  host: localhost
  port: 9000
  ssl: false
database:
  type: postgresql
  host: db.example.com
  port: 5432
```

## 🗄️ Önceden Tanımlanmış Kurallar

Uygulama 5 adet örnek YAML kuralı ile gelir:

1. **Web Server Konfigürasyonu** - HTTP sunucu ayarları
2. **Docker Compose Yapılandırması** - Container tanımları  
3. **Kubernetes Deployment** - K8s dağıtım kuralları
4. **CI/CD Pipeline** - GitHub Actions workflow
5. **Monitoring Konfigürasyonu** - Prometheus ayarları

## 🔧 API Endpoints

### Web Arayüzü
- `GET /` - Ana sayfa
- `POST /compare` - YAML karşılaştırma
- `POST /upload` - Dosya yükleme
- `GET /rules` - Mevcut kuralları listele
- `GET /health` - Sağlık kontrolü

### Örnek API Kullanımı
```bash
curl -X POST "http://localhost:8000/compare" \
     -H "Content-Type: application/json" \
     -d '{"yaml_content": "server:\n  host: localhost\n  port: 8080"}'
```

## 🏗️ Proje Yapısı

```
📁 yaml-comparator/
├── 📄 simple_yaml_comparator.py    # Ana karşılaştırma motoru
├── 📄 simple_web_interface.py      # FastAPI web uygulaması  
├── 📄 yaml_rules.json             # YAML kuralları (otomatik oluşur)
├── 📄 BASIT_README.md             # Bu dosya
└── 📁 venv/                       # Virtual environment
```

## 🔍 Algoritma Detayları

### Benzerlik Hesaplama
1. **YAML Parsing**: Her iki YAML dosyası parse edilir
2. **Düzleştirme**: Nested yapılar düz key-value formatına çevrilir
3. **Set Karşılaştırması**: Jaccard similarity kullanılır
4. **Skor Hesaplama**: `benzerlik = kesişim / birleşim`

### Mock AI Analizi
1. **Akıllı Değerlendirme**: Benzerlik skoruna göre seviye belirlenir
2. **Kontekst Analizi**: Kural türüne göre özel açıklamalar üretilir
3. **Öneriler**: Kullanıcıya faydalı öneriler sunulur

## 📊 Örnek Çıktı

```
================================================================================
YAML KARŞILAŞTIRMA SONUÇLARI
================================================================================

1. KURAL: Web Server Konfigürasyonu
Kural ID: rule_1
Benzerlik Skoru: 0.750 (75.0%)
------------------------------------------------------------

📋 BENZERLİKLER (3 adet):
  ✓ Ortak: server.host = localhost
  ✓ Ortak: server.port = 8080
  ✓ Ortak: database.type = mysql

📋 FARKLAR (2 adet):
  ✗ Farklı: server.ssl -> Girdi: false, Kural: true
  ✗ Sadece kuralda: logging.level = info

🤖 AI ANALİZİ:
  Bu dosyalar web sunucu konfigürasyonu açısından benzerlik gösteriyor.
  Benzerlik seviyesi yüksek (%75.0).
  
  Ana Değerlendirme: 
  Ana yapısal özellikler büyük ölçüde uyumlu...
```

## 🛠️ Konfigürasyon

### Kural Dosyası Konumu
Varsayılan olarak kurallar `yaml_rules.json` dosyasında saklanır. Farklı konum kullanmak için:

```python
comparator = SimpleYamlComparator(rules_file="my_custom_rules.json")
```

### Port Değiştirme
Web arayüzü için farklı port:
```bash
uvicorn simple_web_interface:app --host 0.0.0.0 --port 8080
```

## 🎯 Avantajlar

- **✅ Basit Kurulum**: Karmaşık sistem bağımlılıkları yok
- **⚡ Hızlı**: Anında çalışmaya başlar
- **🔧 Esnek**: Kolayca özelleştirilebilir
- **📚 Öğretici**: Kod açık ve anlaşılır
- **🧪 Test Dostu**: Hızlı prototipleme için ideal

## 🚀 Geliştirilmiş Versiyon

Eğer gerçek MongoDB ve Ollama AI ile çalışmak istiyorsanız:

1. `yaml_comparator.py` - Tam özellikli MongoDB + Ollama versiyonu
2. `web_interface.py` - Gelişmiş web arayüzü
3. `setup_and_run.py` - Otomatik kurulum scripti

## 📝 Notlar

- Bu basit versiyon eğitim ve test amaçlıdır
- Gerçek production kullanımı için MongoDB + Ollama versiyonunu tercih edin
- Mock AI analizleri gerçekçi ama statiktir
- JSON dosyası otomatik olarak oluşturulur ve güncellenir

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📞 Destek

Sorularınız veya önerileriniz için issue açabilirsiniz.