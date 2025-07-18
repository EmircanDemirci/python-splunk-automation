# 🚀 N8N Entegrasyonu - Ollama AI Sigma Benzerlik Analizi

## 📋 Genel Bakış

Bu kılavuz, Ollama AI kullanarak MongoDB'deki Sigma kurallarının benzerlik analizi yapan sistem ile N8N'in nasıl entegre edileceğini açıklar.

## 🔧 Kurulum

### 1. Ollama Kurulumu
```bash
# Ollama'yı kurun
curl -fsSL https://ollama.ai/install.sh | sh

# Model indirin (seçeneklerden biri)
ollama pull llama3.1        # Önerilen - hızlı ve akıllı
ollama pull mistral         # Alternatif
ollama pull codellama       # Kod analizi için
```

### 2. Python Bağımlılıkları
```bash
pip install fastapi uvicorn pymongo requests pyyaml
```

### 3. API Sunucusunu Başlatın
```bash
python n8n_ollama_api.py
```

API şu adreste çalışacak: `http://localhost:8000`

## 📡 API Endpoints

### 🏥 Health Check
```
GET /health
```
**Kullanım:** Sistem durumunu kontrol et

**Yanıt:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "mongodb_connected": true,
  "available_models": ["llama3.1", "mistral"]
}
```

### 🔍 Benzer Kuralları Bul
```
POST /find-similar
```

**Request Body:**
```json
{
  "rule_id": "64a1b2c3d4e5f6789abcdef0",  // MongoDB'den kural ID'si
  "threshold": 0.7,                        // Benzerlik eşiği (0-1)
  "max_results": 5,                        // Maksimum sonuç sayısı
  "model_name": "llama3.1"                 // AI model
}
```

**Veya doğrudan kural içeriği ile:**
```json
{
  "rule_content": {
    "title": "Suspicious PowerShell",
    "description": "Detects malicious PowerShell usage",
    "detection": {
      "selection": {
        "Image|endswith": "\\powershell.exe",
        "CommandLine|contains": ["DownloadString", "iex"]
      },
      "condition": "selection"
    }
  },
  "threshold": 0.7,
  "max_results": 5
}
```

**Yanıt:**
```json
{
  "success": true,
  "target_rule_title": "Suspicious PowerShell Command",
  "target_rule_id": "64a1b2c3d4e5f6789abcdef0",
  "similar_rules": [
    {
      "rule_id": "64a1b2c3d4e5f6789abcdef1",
      "title": "PowerShell Download Activity",
      "similarity_score": 0.85,
      "ai_summary": "Bu kural PowerShell ile dosya indirme aktivitelerini tespit eder...",
      "tags": ["attack.execution", "attack.t1059.001"],
      "level": "medium"
    }
  ],
  "total_rules_analyzed": 1250,
  "processing_time_seconds": 15.3,
  "ai_model_used": "llama3.1"
}
```

### 📋 Kural Listesi
```
GET /rules?limit=50&skip=0
```

### 📄 Tek Kural Getir
```
GET /rule/{rule_id}
```

## 🔄 N8N Workflow Örnekleri

### 📊 Workflow 1: Kural ID ile Benzerlik Analizi

```json
{
  "name": "Sigma Rule Similarity Analysis",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "GET",
        "url": "http://localhost:8000/health"
      },
      "name": "Health Check",
      "type": "n8n-nodes-base.httpRequest",
      "position": [250, 300]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/find-similar",
        "jsonParameters": true,
        "options": {
          "bodyContentType": "json"
        },
        "bodyParametersJson": "{\n  \"rule_id\": \"{{ $json.rule_id }}\",\n  \"threshold\": 0.7,\n  \"max_results\": 5,\n  \"model_name\": \"llama3.1\"\n}"
      },
      "name": "Find Similar Rules",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "functionCode": "// Sonuçları işle ve formatla\nconst response = items[0].json;\n\nif (!response.success) {\n  throw new Error('API çağrısı başarısız');\n}\n\n// Her benzer kural için ayrı item oluştur\nconst results = [];\n\nresponse.similar_rules.forEach((rule, index) => {\n  results.push({\n    json: {\n      rank: index + 1,\n      rule_id: rule.rule_id,\n      title: rule.title,\n      similarity_score: rule.similarity_score,\n      similarity_percentage: Math.round(rule.similarity_score * 100),\n      ai_summary: rule.ai_summary,\n      tags: rule.tags,\n      level: rule.level,\n      target_rule: response.target_rule_title,\n      processing_time: response.processing_time_seconds\n    }\n  });\n});\n\nreturn results;"
      },
      "name": "Process Results",
      "type": "n8n-nodes-base.function",
      "position": [650, 300]
    }
  ],
  "connections": {
    "Health Check": {
      "main": [[{"node": "Find Similar Rules", "type": "main", "index": 0}]]
    },
    "Find Similar Rules": {
      "main": [[{"node": "Process Results", "type": "main", "index": 0}]]
    }
  }
}
```

### 📈 Workflow 2: Otomatik Benzerlik Raporu

```json
{
  "name": "Daily Sigma Similarity Report",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "value": "0 9 * * 1-5"}]
        }
      },
      "name": "Daily Trigger",
      "type": "n8n-nodes-base.cron",
      "position": [250, 300]
    },
    {
      "parameters": {
        "httpMethod": "GET",
        "url": "http://localhost:8000/rules?limit=10"
      },
      "name": "Get Recent Rules",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "functionCode": "// Her kural için benzerlik analizi yap\nconst rules = items[0].json.rules;\nconst analysisPromises = [];\n\nrules.forEach(rule => {\n  analysisPromises.push({\n    json: {\n      rule_id: rule.rule_id,\n      title: rule.title,\n      author: rule.author\n    }\n  });\n});\n\nreturn analysisPromises;"
      },
      "name": "Prepare Analysis",
      "type": "n8n-nodes-base.function",
      "position": [650, 300]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/find-similar",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"rule_id\": \"{{ $json.rule_id }}\",\n  \"threshold\": 0.8,\n  \"max_results\": 3\n}"
      },
      "name": "Analyze Each Rule",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    }
  ]
}
```

### 🚨 Workflow 3: Yeni Kural Benzerlik Uyarısı

```json
{
  "name": "New Rule Similarity Alert",
  "nodes": [
    {
      "parameters": {
        "resource": "collection",
        "operation": "watchForChanges",
        "collection": "rules",
        "options": {
          "fullDocument": "updateLookup"
        }
      },
      "name": "MongoDB Trigger",
      "type": "n8n-nodes-base.mongoDb",
      "position": [250, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "{{ $json.operationType }}",
              "operation": "equal",
              "value2": "insert"
            }
          ]
        }
      },
      "name": "Only New Rules",
      "type": "n8n-nodes-base.if",
      "position": [450, 300]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/find-similar",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"rule_content\": {{ $json.fullDocument }},\n  \"threshold\": 0.9,\n  \"max_results\": 1\n}"
      },
      "name": "Check Similarity",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "{{ $json.similar_rules.length }}",
              "operation": "larger",
              "value2": 0
            }
          ]
        }
      },
      "name": "Has Similar Rules?",
      "type": "n8n-nodes-base.if",
      "position": [850, 300]
    },
    {
      "parameters": {
        "subject": "🚨 Benzer Sigma Kuralı Tespit Edildi",
        "message": "Yeni eklenen kural '{{ $json.target_rule_title }}' benzer kurallara sahip:\n\n{% for rule in $json.similar_rules %}\n- {{ rule.title }} ({{ (rule.similarity_score * 100) | round }}% benzer)\n  AI Özeti: {{ rule.ai_summary }}\n{% endfor %}",
        "options": {
          "allowUnauthorizedCerts": true
        }
      },
      "name": "Send Alert Email",
      "type": "n8n-nodes-base.emailSend",
      "position": [1050, 300]
    }
  ]
}
```

## ⚙️ N8N Node Ayarları

### 🌐 HTTP Request Node
- **Method:** POST/GET
- **URL:** `http://localhost:8000/find-similar`
- **Authentication:** None (yerel API)
- **Headers:** 
  ```
  Content-Type: application/json
  ```

### 📊 Function Node (Sonuç İşleme)
```javascript
// Benzerlik skorunu yüzdeye çevir
items.forEach(item => {
  if (item.json.similarity_score) {
    item.json.similarity_percentage = Math.round(item.json.similarity_score * 100);
    item.json.similarity_level = item.json.similarity_score > 0.8 ? 'High' : 
                                 item.json.similarity_score > 0.6 ? 'Medium' : 'Low';
  }
});

return items;
```

### 🔄 Split In Batches Node
- **Batch Size:** 5 (AI işlemi yavaş olduğu için küçük batch)
- **Options:** "Reset" aktif

## 📈 Performans Optimizasyonu

### ⚡ Hızlandırma İpuçları
1. **Batch Processing:** Çok sayıda kural için batch'lerde işleyin
2. **Caching:** Sık kullanılan sonuçları cache'leyin
3. **Threshold:** Yüksek threshold (0.7+) kullanarak gereksiz işlemleri azaltın
4. **Model Seçimi:** Hız için `llama3.1`, doğruluk için `mistral`

### 🛡️ Rate Limiting
```javascript
// N8N Function Node'da rate limiting
await new Promise(resolve => setTimeout(resolve, 1000)); // 1 saniye bekle
```

## 🔧 Sorun Giderme

### ❌ Yaygın Hatalar

1. **"Ollama bağlantısı kurulamadı"**
   - Çözüm: `ollama serve` komutunu çalıştırın
   - Port kontrolü: `curl http://localhost:11434/api/tags`

2. **"MongoDB bağlantısı kurulamadı"**
   - Çözüm: Bağlantı string'ini kontrol edin
   - Network erişimi kontrol edin

3. **"AI model bulunamadı"**
   - Çözüm: `ollama pull llama3.1` ile model indirin

### 📊 Monitoring

N8N'de monitoring için:
```javascript
// Error handling function
try {
  const response = await $http.request(options);
  return [{ json: { status: 'success', data: response.data } }];
} catch (error) {
  return [{ json: { status: 'error', message: error.message } }];
}
```

## 🎯 Kullanım Senaryoları

### 1. **SOC Analisti Workflow**
- Yeni SIEM uyarısı geldiğinde benzer Sigma kurallarını otomatik bul
- Incident response için ilgili kuralları grupla

### 2. **Threat Hunter Workflow** 
- Yeni threat intelligence'a göre benzer kuralları analiz et
- Coverage gap analizi yap

### 3. **Rule Management Workflow**
- Duplicate kural tespiti
- Kural optimizasyonu önerileri

### 4. **Compliance Reporting**
- Haftalık benzerlik raporu oluştur
- Kural coverage metrikleri

## 🔐 Güvenlik Notları

- API'yi sadece güvenilir ağlardan erişilebilir yapın
- MongoDB bağlantı bilgilerini N8N credential store'da saklayın
- Rate limiting uygulayın
- Log'ları düzenli olarak kontrol edin

Bu entegrasyon ile Sigma kurallarınızın AI destekli benzerlik analizi otomatik olarak N8N workflow'larınızda çalışacaktır! 🚀