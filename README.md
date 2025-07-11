# Sigma to Splunk Automation Tool

Bu otomasyon sistemi, YAML formatındaki Sigma kurallarını Splunk sorgularına dönüştüren bir REST API sağlar. POST istekleri ile Sigma kuralları gönderebilir ve karşılığında Splunk sorguları alabilirsiniz. Ayrıca GitHub'dan otomatik olarak Sigma kurallarını çekip ID'ye göre arama yapabilirsiniz.

## 🚀 Özellikler

- **REST API**: FastAPI tabanlı modern REST API
- **Tekil Dönüştürme**: Bir Sigma kuralını POST ile gönderip Splunk sorgusuna dönüştürün
- **Toplu Dönüştürme**: Birden fazla Sigma kuralını tek istekte dönüştürün
- **GitHub Entegrasyonu**: GitHub'dan otomatik Sigma kural arama
- **ID Bazlı Arama**: Sigma kurallarını ID'ye göre bulma
- **Kombine İşlem**: Kural bulma ve dönüştürmeyi tek istekte yapma
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
| `/search-sigma` | POST | ID'ye göre Sigma kural arama |
| `/search-and-convert` | POST | Kural arama + dönüştürme |
| `/list-sigma-files` | GET | GitHub'daki Sigma dosyalarını listele |
| `/example` | GET | Örnek Sigma kuralı al |
| `/backends` | GET | Desteklenen backend'leri listele |
| `/docs` | GET | API dokümantasyonu (Swagger UI) |

### 1. GitHub'dan ID ile Sigma Kural Arama

```bash
curl -X POST "http://localhost:8000/search-sigma" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
    "metadata": {
      "request_id": "search-001",
      "user": "analyst"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Kural bulundu: proc_creation_win_agentexecutor_potential_abuse.yml",
  "found_rule": {
    "filename": "proc_creation_win_agentexecutor_potential_abuse.yml",
    "download_url": "https://raw.githubusercontent.com/...",
    "content": "title: AgentExecutor PowerShell Execution\nid: 7efd2c8d-8b18-45b7-947d-adfe9ed04f61\n...",
    "id": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
    "file_size": 2178
  },
  "search_stats": {
    "total_files": 1000,
    "searched_files": 9,
    "skipped_files": 0,
    "target_id": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61"
  }
}
```

### 2. Kural Arama ve Dönüştürme (Tek İstek)

```bash
curl -X POST "http://localhost:8000/search-and-convert" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
    "metadata": {
      "request_id": "search-convert-001",
      "user": "analyst"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Kural bulundu ve başarıyla dönüştürüldü",
  "search_result": {
    "success": true,
    "found_rule": { "filename": "...", "content": "..." }
  },
  "conversion_result": {
    "success": true,
    "queries": ["Image=\"\\\\AgentExecutor.exe\" OR OriginalFileName=\"AgentExecutor.exe\" CommandLine IN (\"* -powershell*\", \"* -remediationScript*\") NOT ParentImage=\"*\\\\Microsoft.Management.Services.IntuneWindowsAgent.exe\""]
  }
}
```

### 3. GitHub Dosya Listesi

```bash
curl -X GET "http://localhost:8000/list-sigma-files"
```

**Response:**
```json
{
  "success": true,
  "message": "1000 dosya bulundu",
  "files": [
    {
      "name": "proc_creation_win_7zip_exfil_dmp_files.yml",
      "download_url": "https://raw.githubusercontent.com/...",
      "size": 1215
    }
  ],
  "total_count": 1000
}
```

### 4. Tekil Dönüştürme (Geleneksel)

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

### 5. Python ile Kullanım

```python
import requests

# API base URL
api_url = "http://localhost:8000"

# 1. ID ile Sigma kural arama
def search_sigma_rule(rule_id):
    response = requests.post(f"{api_url}/search-sigma", json={
        "target_id": rule_id,
        "metadata": {"user": "analyst", "operation": "search"}
    })
    return response.json()

# 2. Arama ve dönüştürme kombine
def search_and_convert(rule_id):
    response = requests.post(f"{api_url}/search-and-convert", json={
        "target_id": rule_id,
        "metadata": {"user": "analyst", "operation": "search_convert"}
    })
    return response.json()

# 3. GitHub'dan dosya listesi
def list_sigma_files():
    response = requests.get(f"{api_url}/list-sigma-files")
    return response.json()

# Örnek kullanım
rule_id = "7efd2c8d-8b18-45b7-947d-adfe9ed04f61"

# Sadece kural arama
search_result = search_sigma_rule(rule_id)
if search_result['success']:
    print(f"Bulunan dosya: {search_result['found_rule']['filename']}")
    print(f"İçerik: {search_result['found_rule']['content'][:200]}...")

# Arama ve dönüştürme
combined_result = search_and_convert(rule_id)
if combined_result['success']:
    splunk_query = combined_result['conversion_result']['queries'][0]
    print(f"Splunk Query: {splunk_query}")
```

## 🧪 Test Etme

API'yi test etmek için test scriptini çalıştırın:

```bash
python test_api.py
```

Bu script tüm endpoint'leri test eder ve sonuçları gösterir.

## 📋 Request/Response Modelleri

### SigmaSearchRequest (Yeni)
```json
{
  "target_id": "string (Sigma kural ID'si)",
  "metadata": {
    "request_id": "string",
    "user": "string",
    "custom_field": "any"
  }
}
```

### SigmaSearchResponse (Yeni)
```json
{
  "success": "boolean",
  "message": "string",
  "found_rule": {
    "filename": "string",
    "download_url": "string", 
    "content": "string",
    "id": "string",
    "file_size": "number"
  },
  "search_stats": {
    "total_files": "number",
    "searched_files": "number", 
    "skipped_files": "number",
    "target_id": "string"
  },
  "metadata": "object"
}
```

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

## 🔍 Örnek Kullanım Senaryoları

### Senaryo 1: n8n İş Akışı Entegrasyonu
```bash
# n8n'den gelen Sigma ID'si ile kural arama ve dönüştürme
POST /search-and-convert
{
  "target_id": "{{$node['Webhook'].json['sigma_id']}}",
  "metadata": {
    "workflow_id": "{{$execution.id}}",
    "user": "{{$node['Webhook'].json['user']}}"
  }
}
```

### Senaryo 2: Toplu Analiz
```python
# Birden fazla ID'yi sıralı şekilde işleme
sigma_ids = [
    "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
    "c0b40568-b1e9-4b03-8d6c-b096da6da9ab"
]

results = []
for sigma_id in sigma_ids:
    result = search_and_convert(sigma_id)
    results.append(result)
```

### Senaryo 3: Kural Keşfetme
```python
# GitHub'daki tüm dosyaları listeleme ve filtreleme
files = list_sigma_files()
process_creation_files = [
    f for f in files['files'] 
    if 'process_creation' in f['name']
]
```

## 🛠️ Hata Ayıklama

### Yaygın Hatalar

1. **GitHub API Hatası**: GitHub API limitine takılma
2. **ID Bulunamadı**: Yanlış veya mevcut olmayan Sigma ID'si
3. **YAML Parse Hatası**: Geçersiz Sigma kural formatı
4. **Network Hatası**: GitHub'a erişim problemi

### Log Takibi

API logları konsola yazdırılır:
```bash
INFO:__main__:Sigma kural arama isteği: 7efd2c8d-8b18-45b7-947d-adfe9ed04f61
INFO:__main__:Kural bulundu: proc_creation_win_agentexecutor_potential_abuse.yml
INFO:__main__:Başarıyla 1 Splunk sorgusu oluşturuldu
```

### Performans İpuçları

- API ID'yi bulduktan sonra aramayı durdurur (optimize edilmiş)
- 1000 dosya arasından sadece gerekli olanları indirir
- Hata durumunda dosyalar atlanır, işlem devam eder

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

## 🔧 GitHub Entegrasyonu Detayları

### Desteklenen Repository Yolu
- Varsayılan: `rules/windows/process_creation`
- GitHub: `SigmaHQ/sigma` repository
- Dosya formatı: `.yml` uzantılı dosyalar
- Ortalama dosya sayısı: ~1000 dosya

### Arama Algoritması
1. GitHub API ile dosya listesi alınır
2. Her dosya sıralı olarak indirilir
3. İçerikten ID çıkarılır (`id:` satırı aranır)
4. Target ID ile eşleşme kontrol edilir
5. İlk eşleşmede arama durur (performans)

## 📝 Lisans

Bu proje educational amaçlı geliştirilmiştir.
