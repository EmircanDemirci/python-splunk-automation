# 🎯 N8N - Tek Sigma Kuralı SigmaHQ Benzerlik Analizi

## 📋 Genel Bakış

Bu sistem tek bir Sigma kuralı alır ve MongoDB'deki **SigmaHQ kuralları** ile AI destekli benzerlik analizi yapar. Amacı, kullanıcının yazdığı kurala en benzer olan SigmaHQ kurallarını bulmaktır.

## 🚀 Hızlı Başlangıç

### 1. Ollama Kurulumu
```bash
# Ollama'yı kurun
curl -fsSL https://ollama.ai/install.sh | sh

# AI model indirin
ollama pull llama3.1

# Ollama'yı başlatın
ollama serve
```

### 2. API Sunucusunu Başlatın
```bash
source venv/bin/activate
python single_sigma_api.py
```

API adresi: `http://localhost:8000`

## 📡 API Endpoints

### 🏥 Sistem Durumu
```
GET /health
```

**Yanıt:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "mongodb_connected": true,
  "available_models": ["llama3.1", "mistral"],
  "sigmahq_rules_count": 2847
}
```

### 🎯 Ana Endpoint: Sigma Analizi
```
POST /analyze-sigma
```

**Request (JSON Format):**
```json
{
  "sigma_rule": {
    "title": "Suspicious PowerShell Activity",
    "description": "Detects malicious PowerShell usage",
    "level": "medium",
    "logsource": {
      "category": "process_creation",
      "product": "windows"
    },
    "detection": {
      "selection": {
        "Image|endswith": "\\powershell.exe",
        "CommandLine|contains": ["DownloadString", "iex"]
      },
      "condition": "selection"
    },
    "tags": ["attack.execution", "attack.t1059.001"]
  },
  "threshold": 0.3,
  "max_results": 5,
  "model_name": "llama3.1"
}
```

**Request (YAML Format):**
```
POST /analyze-sigma-yaml
```

```json
{
  "sigma_yaml": "title: Suspicious PowerShell\ndescription: Detects malicious usage\ndetection:\n  selection:\n    Image|endswith: '\\powershell.exe'\n  condition: selection",
  "threshold": 0.3,
  "max_results": 5
}
```

**Yanıt:**
```json
{
  "success": true,
  "input_rule_title": "Suspicious PowerShell Activity",
  "input_rule_description": "Detects malicious PowerShell usage",
  "similar_rules": [
    {
      "rule_id": "64a1b2c3d4e5f6789abcdef1",
      "title": "PowerShell Download Cradle",
      "description": "Detects PowerShell download commands",
      "similarity_score": 0.87,
      "similarity_percentage": 87,
      "tags": ["attack.execution", "attack.t1059.001"],
      "level": "high",
      "author": "Florian Roth",
      "date": "2023/05/15",
      "ai_summary": "Bu kural da PowerShell ile download aktivitelerini tespit eder. Detection mantığı ve MITRE teknikleri çok benzer."
    }
  ],
  "total_analyzed": 2847,
  "processing_time_seconds": 24.5,
  "ai_model_used": "llama3.1",
  "threshold_used": 0.3
}
```

### 📊 SigmaHQ İstatistikleri
```
GET /sigmahq-stats
```

**Yanıt:**
```json
{
  "success": true,
  "total_rules": 2847,
  "level_distribution": {
    "medium": 1234,
    "high": 891,
    "low": 567,
    "critical": 155
  },
  "top_tags": {
    "attack.execution": 456,
    "attack.t1059.001": 234,
    "attack.persistence": 189
  },
  "top_authors": {
    "Florian Roth": 1123,
    "Nasreddine Bencherchali": 567
  }
}
```

## 🔄 N8N Workflow Örnekleri

### 📊 Workflow 1: Basit Sigma Analizi

```json
{
  "name": "Single Sigma SigmaHQ Analysis",
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
        "url": "http://localhost:8000/analyze-sigma",
        "jsonParameters": true,
        "options": {
          "bodyContentType": "json"
        },
        "bodyParametersJson": "{\n  \"sigma_rule\": {{ $json.sigma_rule }},\n  \"threshold\": {{ $json.threshold || 0.3 }},\n  \"max_results\": {{ $json.max_results || 5 }}\n}"
      },
      "name": "Analyze Sigma Rule",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "functionCode": "// AI sonuçlarını formatla\nconst response = items[0].json;\n\nif (!response.success) {\n  throw new Error('Sigma analizi başarısız');\n}\n\n// Her benzer kural için ayrı output\nconst results = [];\n\nresponse.similar_rules.forEach((rule, index) => {\n  results.push({\n    json: {\n      rank: index + 1,\n      input_rule: response.input_rule_title,\n      similar_rule_id: rule.rule_id,\n      similar_rule_title: rule.title,\n      similarity_score: rule.similarity_score,\n      similarity_percentage: rule.similarity_percentage,\n      similarity_level: rule.similarity_percentage > 80 ? 'High' : \n                       rule.similarity_percentage > 60 ? 'Medium' : 'Low',\n      tags: rule.tags,\n      level: rule.level,\n      author: rule.author,\n      ai_explanation: rule.ai_summary,\n      processing_time: response.processing_time_seconds,\n      total_sigmahq_rules: response.total_analyzed\n    }\n  });\n});\n\nreturn results;"
      },
      "name": "Format Results",
      "type": "n8n-nodes-base.function",
      "position": [650, 300]
    }
  ],
  "connections": {
    "Health Check": {
      "main": [[{"node": "Analyze Sigma Rule", "type": "main", "index": 0}]]
    },
    "Analyze Sigma Rule": {
      "main": [[{"node": "Format Results", "type": "main", "index": 0}]]
    }
  }
}
```

### 🚨 Workflow 2: YAML Input ile Analiz

```json
{
  "name": "YAML Sigma Analysis",
  "nodes": [
    {
      "parameters": {
        "functionCode": "// YAML string'i hazırla\nconst yamlContent = `\ntitle: {{ $json.title }}\ndescription: {{ $json.description }}\nlevel: {{ $json.level }}\nlogsource:\n  category: {{ $json.log_category }}\n  product: {{ $json.log_product }}\ndetection:\n  selection:\n    Image|endswith: '{{ $json.process_path }}'\n    CommandLine|contains:\n      - '{{ $json.command_1 }}'\n      - '{{ $json.command_2 }}'\n  condition: selection\ntags:\n  - {{ $json.mitre_tag }}\n`;\n\nreturn [{\n  json: {\n    sigma_yaml: yamlContent,\n    threshold: 0.4,\n    max_results: 3\n  }\n}];"
      },
      "name": "Build YAML",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/analyze-sigma-yaml",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"sigma_yaml\": \"{{ $json.sigma_yaml }}\",\n  \"threshold\": {{ $json.threshold }},\n  \"max_results\": {{ $json.max_results }}\n}"
      },
      "name": "Analyze YAML",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    }
  ]
}
```

### 📈 Workflow 3: Batch Sigma Analysis

```json
{
  "name": "Batch Sigma Rules Analysis",
  "nodes": [
    {
      "parameters": {
        "functionCode": "// Birden fazla Sigma kuralını işle\nconst sigmaRules = [\n  {\n    \"title\": \"PowerShell Execution\",\n    \"detection\": {\n      \"selection\": {\n        \"Image|endswith\": \"\\\\powershell.exe\"\n      },\n      \"condition\": \"selection\"\n    }\n  },\n  {\n    \"title\": \"CMD Execution\", \n    \"detection\": {\n      \"selection\": {\n        \"Image|endswith\": \"\\\\cmd.exe\"\n      },\n      \"condition\": \"selection\"\n    }\n  }\n];\n\nconst results = [];\nsigmaRules.forEach((rule, index) => {\n  results.push({\n    json: {\n      batch_index: index,\n      sigma_rule: rule,\n      threshold: 0.3,\n      max_results: 3\n    }\n  });\n});\n\nreturn results;"
      },
      "name": "Prepare Batch",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "batchSize": 1,
        "options": {\n          \"reset\": true\n        }
      },
      "name": "Split In Batches",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [450, 300]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/analyze-sigma",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"sigma_rule\": {{ $json.sigma_rule }},\n  \"threshold\": {{ $json.threshold }},\n  \"max_results\": {{ $json.max_results }}\n}"
      },
      "name": "Analyze Each Rule",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "functionCode": "// 5 saniye bekle (AI rate limiting)\nawait new Promise(resolve => setTimeout(resolve, 5000));\nreturn items;"
      },
      "name": "Rate Limit",
      "type": "n8n-nodes-base.function",
      "position": [850, 300]
    }
  ]
}
```

### 🔔 Workflow 4: High Similarity Alert

```json
{
  "name": "High Similarity Alert System",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "http://localhost:8000/analyze-sigma",
        "jsonParameters": true,
        "bodyParametersJson": "{{ $json }}"
      },
      "name": "Analyze Rule",
      "type": "n8n-nodes-base.httpRequest",
      "position": [250, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "{{ $json.similar_rules[0].similarity_percentage }}",
              "operation": "larger",
              "value2": 85
            }
          ]
        }
      },
      "name": "High Similarity?",
      "type": "n8n-nodes-base.if",
      "position": [450, 300]
    },
    {
      "parameters": {
        "subject": "🚨 Yüksek Benzerlikli Sigma Kuralı Tespit Edildi",
        "message": "Kullanıcı kuralı '{{ $json.input_rule_title }}' SigmaHQ'da çok benzer bir kurala sahip:\n\n📋 Benzer Kural: {{ $json.similar_rules[0].title }}\n🎯 Benzerlik: {{ $json.similar_rules[0].similarity_percentage }}%\n👤 Author: {{ $json.similar_rules[0].author }}\n🤖 AI Analizi: {{ $json.similar_rules[0].ai_summary }}\n\nBu kuralın zaten mevcut olabileceğini gösterir.",
        "options": {
          "allowUnauthorizedCerts": true
        }
      },
      "name": "Send Alert",
      "type": "n8n-nodes-base.emailSend",
      "position": [650, 300]
    }
  ]
}
```

## 🎯 Kullanım Senaryoları

### 1. **SOC Rule Development**
- Yeni yazılan kural zaten var mı kontrolü
- Benzer kurallardan ilham alma
- Rule optimization önerileri

### 2. **Threat Intelligence Integration**
- Yeni IOC'lar için benzer detection mantığı arama
- Coverage gap analizi
- Rule effectiveness comparison

### 3. **Security Training**
- Sigma rule yazma eğitiminde referans bulma
- Best practice örnekleri
- Community rule'larından öğrenme

### 4. **Compliance & Coverage**
- MITRE ATT&CK coverage kontrolü
- Detection capability assessment
- Rule redundancy analizi

## ⚙️ N8N Konfigürasyonu

### 🌐 HTTP Request Node Ayarları
- **Method:** POST
- **URL:** `http://localhost:8000/analyze-sigma`
- **Content-Type:** `application/json`
- **Timeout:** 60 seconds (AI işlemi uzun sürebilir)

### 📊 Function Node Örnekleri

**Benzerlik Seviyesi Hesaplama:**
```javascript
// Benzerlik seviyesini kategorize et
items.forEach(item => {
  const score = item.json.similarity_percentage;
  
  if (score >= 90) {
    item.json.similarity_category = 'Neredeyse İdentik';
    item.json.alert_level = 'critical';
  } else if (score >= 80) {
    item.json.similarity_category = 'Çok Benzer';
    item.json.alert_level = 'high';
  } else if (score >= 60) {
    item.json.similarity_category = 'Benzer';
    item.json.alert_level = 'medium';
  } else {
    item.json.similarity_category = 'Düşük Benzerlik';
    item.json.alert_level = 'low';
  }
});

return items;
```

**YAML Builder:**
```javascript
// Dinamik YAML oluştur
const yamlTemplate = `
title: {{ title }}
description: {{ description }}
level: {{ level }}
detection:
  selection:
    {{ field_name }}:
      - '{{ value_1 }}'
      - '{{ value_2 }}'
  condition: selection
tags:
  - {{ mitre_tag }}
`;

return [{
  json: {
    sigma_yaml: yamlTemplate
      .replace('{{ title }}', $input.first().json.rule_title)
      .replace('{{ description }}', $input.first().json.rule_desc)
      .replace('{{ level }}', $input.first().json.severity)
      .replace('{{ field_name }}', $input.first().json.log_field)
      .replace('{{ value_1 }}', $input.first().json.pattern_1)
      .replace('{{ value_2 }}', $input.first().json.pattern_2)
      .replace('{{ mitre_tag }}', $input.first().json.attack_technique)
  }
}];
```

## 📈 Performans İpuçları

### ⚡ Hızlandırma
1. **Threshold Ayarı:** Yüksek threshold (0.5+) daha az kural analiz eder
2. **Max Results:** Sadece ihtiyacınız kadar sonuç alın
3. **Batch Size:** Büyük batch'lerde 1-2 kuraldan fazla işlemeyin
4. **Model Seçimi:** `llama3.1` hızlı, `mistral` daha detaylı

### 🛡️ Rate Limiting
```javascript
// N8N Function Node'da
await new Promise(resolve => setTimeout(resolve, 3000)); // 3 saniye bekle
```

## 🔧 Troubleshooting

### ❌ Yaygın Hatalar

1. **"detection bölümü gerekli"**
   - Çözüm: Sigma rule'da mutlaka `detection` field'ı olmalı

2. **"Ollama AI bağlantısı kurulamadı"**
   - Çözüm: `ollama serve` komutunu çalıştırın
   - Test: `curl http://localhost:11434/api/tags`

3. **"Timeout"**
   - Çözüm: N8N timeout'u 60+ saniyeye çıkarın
   - Rate limiting ekleyin

4. **"AI özet oluşturulamadı"**
   - Normal durum, algoritma devam eder
   - Model performansına bağlı

## 📊 Monitoring

```javascript
// N8N'de monitoring
const startTime = Date.now();

// API çağrısından sonra
const processingTime = Date.now() - startTime;

return [{
  json: {
    ...items[0].json,
    processing_time_ms: processingTime,
    timestamp: new Date().toISOString(),
    success_rate: items[0].json.similar_rules.length > 0 ? 100 : 0
  }
}];
```

Bu sistem ile N8N workflow'larınızda SigmaHQ kuralları ile AI destekli karşılaştırma yapabilirsiniz! 🚀