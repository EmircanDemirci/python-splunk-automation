# 🔍 YAML Karşılaştırma Uygulaması

MongoDB ve Ollama AI kullanarak YAML dosyalarını akıllı bir şekilde karşılaştıran Python uygulaması.

## 🎯 Özellikler

- ✅ **YAML Dosya Analizi**: YAML yapılarını derinlemesine analiz eder
- 🤖 **AI Destekli Karşılaştırma**: Ollama LLM ile benzerlik analizi yapar
- 📊 **Benzerlik Skoru**: Matematiksel benzerlik hesaplaması
- 📋 **Detaylı Rapor**: Farklar ve benzerlikler detayında listelenir  
- 🌐 **Web Arayüzü**: Modern ve kullanıcı dostu web interface
- 💻 **Konsol Desteği**: Terminal üzerinden de kullanılabilir
- 🗄️ **MongoDB Entegrasyonu**: 5 adet örnek YAML kuralı ile karşılaştırma

## 🚀 Hızlı Başlangıç

### Otomatik Kurulum
```bash
python3 setup_and_run.py
```

Kurulum scriptini çalıştırın ve menüden "1" seçeneğini seçin.

### Manuel Kurulum

#### 1. Sistem Gereksinimleri
```bash
# MongoDB kurulumu
sudo apt update
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Ollama kurulumu  
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
```

#### 2. Python Bağımlılıkları
```bash
pip install -r requirements.txt
```

#### 3. Uygulamayı Çalıştırma

**Web Arayüzü:**
```bash
python web_interface.py
```
Tarayıcınızda `http://localhost:8000` adresini ziyaret edin.

**Konsol Uygulaması:**
```bash
python yaml_comparator.py
```

## 📋 Örnek Kullanım

### Web Arayüzü ile
1. `http://localhost:8000` adresini açın
2. YAML içeriğinizi text area'ya yapıştırın veya dosya yükleyin
3. "Karşılaştır" butonuna tıklayın
4. AI analizi sonuçlarını görün

### Konsol ile
```bash
python yaml_comparator.py
```
YAML içeriğinizi girin ve "END" yazarak bitirin.

### Test YAML Örneği
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

## 🗄️ Veritabanı Kuralları

Uygulama 5 adet önceden tanımlanmış YAML kuralı ile karşılaştırma yapar:

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

### Örnek API Kullanımı
```bash
curl -X POST "http://localhost:8000/compare" \
     -H "Content-Type: application/json" \
     -d '{"yaml_content": "server:\n  host: localhost\n  port: 8080"}'
```

## 🏗️ Proje Yapısı

```
📁 yaml-comparator/
├── 📄 yaml_comparator.py      # Ana karşılaştırma motoru
├── 📄 web_interface.py        # FastAPI web uygulaması  
├── 📄 setup_and_run.py        # Kurulum ve çalıştırma scripti
├── 📄 requirements.txt        # Python bağımlılıkları
└── 📄 README.md              # Bu dosya
```

## 🔍 Algoritma Detayları

### Benzerlik Hesaplama
1. **YAML Parsing**: Her iki YAML dosyası parse edilir
2. **Düzleştirme**: Nested yapılar düz key-value formatına çevrilir
3. **Set Karşılaştırması**: Jaccard similarity kullanılır
4. **Skor Hesaplama**: `benzerlik = kesişim / birleşim`

### AI Analizi
1. **Prompt Hazırlama**: YAML içerikleri ve farklılıklar AI'ya gönderilir
2. **Ollama LLM**: Llama2 modeli ile analiz yapılır
3. **Türkçe Rapor**: Benzerlik nedenleri Türkçe açıklanır

## 🛠️ Konfigürasyon

### MongoDB Ayarları
```python
# yaml_comparator.py içinde
comparator = YamlComparator(
    mongo_uri="mongodb://localhost:27017/",
    db_name="yaml_rules", 
    collection_name="rules"
)
```

### Ollama Model Değiştirme
```python
# Farklı model kullanmak için
comparator = YamlComparator(ollama_model="codellama")
```

## 🔧 Troubleshooting

### MongoDB Bağlantı Sorunu
```bash
sudo systemctl status mongodb
sudo systemctl start mongodb
```

### Ollama Model İndirme
```bash
ollama pull llama2
ollama list  # Modelleri kontrol et
```

### Port Çakışması
Web arayüzü için farklı port:
```bash
uvicorn web_interface:app --host 0.0.0.0 --port 8080
```

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
  Bu iki YAML dosyası web sunucu konfigürasyonu açısından oldukça benzerdir.
  Her ikisi de server ve database bölümlerine sahiptir ve temel yapısal
  özellikler ortaktır. Ana benzerlik nedenleri...
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında dağıtılmaktadır.

## 🎯 Gelecek Özellikler

- [ ] Daha fazla AI modeli desteği (GPT, Claude)
- [ ] YAML şema validasyonu
- [ ] Batch dosya işleme
- [ ] Export/Import kuralları
- [ ] REST API documentation (OpenAPI)
- [ ] Docker containerization
- [ ] Performance optimizasyonları

## 📞 Destek

Sorularınız için issue açabilir veya yeni özellik önerebilirsiniz.
