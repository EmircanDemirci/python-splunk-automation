#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit YAML Karşılaştırma Uygulaması
JSON dosya depolama ve mock AI kullanarak YAML dosyalarını karşılaştırır
"""

import yaml
import json
import difflib
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import os

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class YamlComparison:
    """YAML karşılaştırma sonucu"""
    rule_id: str
    rule_name: str
    similarity_score: float
    differences: List[str]
    similarities: List[str]
    ai_analysis: str
    comparison_date: str

class SimpleYamlComparator:
    """Basit YAML dosyalarını karşılaştıran sınıf"""
    
    def __init__(self, rules_file: str = "yaml_rules.json"):
        """
        Başlatıcı
        
        Args:
            rules_file: YAML kurallarının saklandığı JSON dosya
        """
        self.rules_file = rules_file
        self.rules = []
        self.load_rules()
        
    def load_rules(self):
        """JSON dosyasından kuralları yükler"""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        else:
            self.initialize_sample_rules()
    
    def save_rules(self):
        """Kuralları JSON dosyasına kaydeder"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=2, ensure_ascii=False)
        
    def initialize_sample_rules(self):
        """Örnek YAML kuralları ile dosyayı başlatır"""
        sample_rules = [
            {
                "id": "rule_1",
                "name": "Web Server Konfigürasyonu",
                "yaml_content": """server:
  host: 0.0.0.0
  port: 8080
  ssl: true
  timeout: 30
database:
  type: mysql
  host: localhost
  port: 3306
  name: webapp_db
logging:
  level: info
  format: json""",
                "description": "Web sunucu konfigürasyon dosyası",
                "tags": ["web", "server", "config"]
            },
            {
                "id": "rule_2", 
                "name": "Docker Compose Yapılandırması",
                "yaml_content": """version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./html:/usr/share/nginx/html
  database:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: myapp
    ports:
      - "3306:3306" """,
                "description": "Docker Compose servis tanımları",
                "tags": ["docker", "compose", "containers"]
            },
            {
                "id": "rule_3",
                "name": "Kubernetes Deployment",
                "yaml_content": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-container
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m" """,
                "description": "Kubernetes deployment konfigürasyonu",
                "tags": ["kubernetes", "deployment", "containers"]
            },
            {
                "id": "rule_4",
                "name": "CI/CD Pipeline",
                "yaml_content": """name: Build and Deploy
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest
    - name: Deploy
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Deploying to production" """,
                "description": "GitHub Actions CI/CD pipeline",
                "tags": ["ci", "cd", "github", "actions"]
            },
            {
                "id": "rule_5",
                "name": "Monitoring Konfigürasyonu",
                "yaml_content": """global:
  scrape_interval: 15s
  evaluation_interval: 15s
rule_files:
  - "rules/*.yml"
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'web-app'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 5s
    metrics_path: /metrics
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093 """,
                "description": "Prometheus monitoring konfigürasyonu", 
                "tags": ["monitoring", "prometheus", "metrics"]
            }
        ]
        
        self.rules = sample_rules
        self.save_rules()
        logger.info(f"{len(sample_rules)} örnek kural dosyaya kaydedildi")
    
    def parse_yaml(self, yaml_content: str) -> Dict[Any, Any]:
        """YAML içeriğini parse eder"""
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.error(f"YAML parse hatası: {e}")
            return {}
    
    def calculate_similarity_score(self, yaml1: Dict, yaml2: Dict) -> float:
        """İki YAML yapısı arasındaki benzerlik skorunu hesaplar"""
        def dict_to_string_set(d: Dict, prefix: str = "") -> set:
            """Dictionary'yi string set'e çevirir"""
            result = set()
            for key, value in d.items():
                current_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    result.update(dict_to_string_set(value, current_key))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            result.update(dict_to_string_set(item, f"{current_key}[{i}]"))
                        else:
                            result.add(f"{current_key}[{i}]={str(item)}")
                else:
                    result.add(f"{current_key}={str(value)}")
            return result
        
        set1 = dict_to_string_set(yaml1)
        set2 = dict_to_string_set(yaml2)
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_differences_and_similarities(self, yaml1: Dict, yaml2: Dict) -> Tuple[List[str], List[str]]:
        """İki YAML arasındaki farkları ve benzerlikleri bulur"""
        def flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
            """Dictionary'yi düzleştirir"""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                        else:
                            items.append((f"{new_key}[{i}]", item))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flat1 = flatten_dict(yaml1)
        flat2 = flatten_dict(yaml2)
        
        similarities = []
        differences = []
        
        # Ortak anahtarları bul
        common_keys = set(flat1.keys()).intersection(set(flat2.keys()))
        for key in common_keys:
            if flat1[key] == flat2[key]:
                similarities.append(f"Ortak: {key} = {flat1[key]}")
            else:
                differences.append(f"Farklı: {key} -> Girdi: {flat1[key]}, Kural: {flat2[key]}")
        
        # Sadece birinde olan anahtarlar
        only_in_1 = set(flat1.keys()) - set(flat2.keys())
        only_in_2 = set(flat2.keys()) - set(flat1.keys())
        
        for key in only_in_1:
            differences.append(f"Sadece girdide: {key} = {flat1[key]}")
        
        for key in only_in_2:
            differences.append(f"Sadece kuralda: {key} = {flat2[key]}")
        
        return differences, similarities
    
    def get_mock_ai_analysis(self, rule_name: str, similarity_score: float, 
                           similarities: List[str], differences: List[str]) -> str:
        """Mock AI analizi yapar"""
        
        # Benzerlik skoruna göre analiz
        if similarity_score >= 0.8:
            level = "çok yüksek"
            reason = "Yapısal ve değer bazında neredeyse tamamen eşleşiyor"
        elif similarity_score >= 0.6:
            level = "yüksek"
            reason = "Ana yapısal özellikler büyük ölçüde uyumlu"
        elif similarity_score >= 0.4:
            level = "orta"
            reason = "Bazı temel yapısal benzerlikler mevcut"
        elif similarity_score >= 0.2:
            level = "düşük"
            reason = "Sınırlı sayıda ortak özellik bulunuyor"
        else:
            level = "çok düşük"
            reason = "Minimal yapısal benzerlik var"
        
        # Kural türüne göre özel analiz
        analysis_templates = {
            "Web Server": "Bu dosyalar web sunucu konfigürasyonu açısından benzerlik gösteriyor",
            "Docker": "Container teknolojileri ve servis tanımları bağlamında ortak noktalar var", 
            "Kubernetes": "Kubernetes deployment ve container orkestrasyon yapısında benzerlikler mevcut",
            "CI/CD": "Sürekli entegrasyon ve dağıtım pipeline'ları açısından paralel özellikler gösteriyor",
            "Monitoring": "İzleme ve metrik toplama konfigürasyonları bakımından benzer yapıda"
        }
        
        context = "genel konfigürasyon"
        for key, template in analysis_templates.items():
            if key.lower() in rule_name.lower():
                context = template
                break
        
        # Benzerlik sayısına göre ek bilgi
        sim_count = len(similarities)
        diff_count = len(differences)
        
        if sim_count > 5:
            detail = f"Toplam {sim_count} ortak özellik tespit edildi, bu da güçlü bir yapısal benzerlik gösteriyor."
        elif sim_count > 2:
            detail = f"{sim_count} adet ortak özellik bulundu, makul bir benzerlik seviyesi."
        else:
            detail = f"Sadece {sim_count} ortak özellik var, benzerlik sınırlı."
        
        if diff_count > 10:
            detail += f" Ancak {diff_count} adet fark da mevcut, bu da önemli yapısal farklılıklar olduğunu gösteriyor."
        elif diff_count > 5:
            detail += f" {diff_count} adet fark var, bazı konfigürasyon farklılıkları mevcut."
        elif diff_count > 0:
            detail += f" {diff_count} adet küçük fark tespit edildi."
        
        analysis = f"""
{context}. Benzerlik seviyesi {level} (%{similarity_score*100:.1f}).

Ana Değerlendirme:
{reason}. {detail}

Öneriler:
- Ortak konfigürasyon yapılarını standartlaştırabilirsiniz
- Farklılıklar özel gereksinimlerden kaynaklanıyor olabilir
- Bu konfigürasyonları bir template olarak kullanmayı düşünebilirsiniz
        """.strip()
        
        return analysis
    
    def compare_with_rules(self, input_yaml_content: str) -> List[YamlComparison]:
        """Girdi YAML'ini kurallarla karşılaştırır"""
        input_yaml = self.parse_yaml(input_yaml_content)
        if not input_yaml:
            logger.error("Girdi YAML'i parse edilemedi")
            return []
        
        results = []
        
        for rule in self.rules:
            rule_yaml = self.parse_yaml(rule['yaml_content'])
            if not rule_yaml:
                continue
            
            # Benzerlik skorunu hesapla
            similarity_score = self.calculate_similarity_score(input_yaml, rule_yaml)
            
            # Fark ve benzerlikleri bul
            differences, similarities = self.find_differences_and_similarities(input_yaml, rule_yaml)
            
            # Mock AI analizi yap
            ai_analysis = self.get_mock_ai_analysis(
                rule['name'],
                similarity_score,
                similarities,
                differences
            )
            
            comparison = YamlComparison(
                rule_id=rule['id'],
                rule_name=rule['name'],
                similarity_score=similarity_score,
                differences=differences,
                similarities=similarities,
                ai_analysis=ai_analysis,
                comparison_date=datetime.now().isoformat()
            )
            
            results.append(comparison)
        
        # Benzerlik skoruna göre sırala (yüksekten düşüğe)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results
    
    def print_comparison_results(self, results: List[YamlComparison]):
        """Karşılaştırma sonuçlarını yazdırır"""
        print("\n" + "="*80)
        print("YAML KARŞILAŞTIRMA SONUÇLARI")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. KURAL: {result.rule_name}")
            print(f"Kural ID: {result.rule_id}")
            print(f"Benzerlik Skoru: {result.similarity_score:.3f} ({result.similarity_score*100:.1f}%)")
            print("-" * 60)
            
            print(f"\n📋 BENZERLİKLER ({len(result.similarities)} adet):")
            for similarity in result.similarities[:3]:  # İlk 3 benzerlik
                print(f"  ✓ {similarity}")
            if len(result.similarities) > 3:
                print(f"  ... ve {len(result.similarities)-3} adet daha")
            
            print(f"\n📋 FARKLAR ({len(result.differences)} adet):")
            for diff in result.differences[:3]:  # İlk 3 fark
                print(f"  ✗ {diff}")
            if len(result.differences) > 3:
                print(f"  ... ve {len(result.differences)-3} adet daha")
            
            print(f"\n🤖 AI ANALİZİ:")
            print(f"  {result.ai_analysis}")
            
            print("\n" + "-"*80)

def main():
    """Ana fonksiyon"""
    print("🔍 Basit YAML Karşılaştırma Uygulaması")
    print("="*60)
    
    # Comparator'ı başlat
    comparator = SimpleYamlComparator()
    
    print(f"\n✅ {len(comparator.rules)} kural yüklendi")
    
    # Kullanıcıdan YAML girişi al
    print("\nLütfen karşılaştırmak istediğiniz YAML içeriğini girin:")
    print("(Girişi bitirmek için boş bir satırda 'END' yazın)")
    
    yaml_lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            yaml_lines.append(line)
        except KeyboardInterrupt:
            print("\n\n👋 Uygulama durduruldu")
            return
        except EOFError:
            break
    
    input_yaml = "\n".join(yaml_lines)
    
    if not input_yaml.strip():
        print("❌ Geçerli bir YAML içeriği girilmedi!")
        return
    
    print("\n🔄 Karşılaştırma yapılıyor...")
    
    # Karşılaştırma yap
    results = comparator.compare_with_rules(input_yaml)
    
    # Sonuçları göster
    comparator.print_comparison_results(results)

if __name__ == "__main__":
    main()