#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML Karşılaştırma Uygulaması
MongoDB ve Ollama AI kullanarak YAML dosyalarını karşılaştırır
"""

import yaml
import json
import difflib
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pymongo import MongoClient
import ollama
import hashlib
from datetime import datetime
import logging

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
    comparison_date: datetime

class YamlComparator:
    """YAML dosyalarını karşılaştıran ana sınıf"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/", 
                 db_name: str = "yaml_rules", 
                 collection_name: str = "rules",
                 ollama_model: str = "llama2"):
        """
        Başlatıcı
        
        Args:
            mongo_uri: MongoDB bağlantı URI'si
            db_name: Veritabanı adı
            collection_name: Koleksiyon adı
            ollama_model: Kullanılacak Ollama modeli
        """
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        self.ollama_model = ollama_model
        
    def initialize_sample_rules(self):
        """Örnek YAML kuralları ile veritabanını başlatır"""
        sample_rules = [
            {
                "_id": "rule_1",
                "name": "Web Server Konfigürasyonu",
                "yaml_content": """
server:
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
  format: json
""",
                "description": "Web sunucu konfigürasyon dosyası",
                "tags": ["web", "server", "config"]
            },
            {
                "_id": "rule_2", 
                "name": "Docker Compose Yapılandırması",
                "yaml_content": """
version: '3.8'
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
      - "3306:3306"
""",
                "description": "Docker Compose servis tanımları",
                "tags": ["docker", "compose", "containers"]
            },
            {
                "_id": "rule_3",
                "name": "Kubernetes Deployment",
                "yaml_content": """
apiVersion: apps/v1
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
            cpu: "500m"
""",
                "description": "Kubernetes deployment konfigürasyonu",
                "tags": ["kubernetes", "deployment", "containers"]
            },
            {
                "_id": "rule_4",
                "name": "CI/CD Pipeline",
                "yaml_content": """
name: Build and Deploy
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
        echo "Deploying to production"
""",
                "description": "GitHub Actions CI/CD pipeline",
                "tags": ["ci", "cd", "github", "actions"]
            },
            {
                "_id": "rule_5",
                "name": "Monitoring Konfigürasyonu",
                "yaml_content": """
global:
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
          - localhost:9093
""",
                "description": "Prometheus monitoring konfigürasyonu", 
                "tags": ["monitoring", "prometheus", "metrics"]
            }
        ]
        
        # Mevcut kuralları temizle ve yeni kuralları ekle
        self.collection.drop()
        self.collection.insert_many(sample_rules)
        logger.info(f"{len(sample_rules)} örnek kural veritabanına eklendi")
    
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
    
    def get_ai_analysis(self, yaml1_content: str, yaml2_content: str, 
                       similarities: List[str], differences: List[str]) -> str:
        """Ollama AI kullanarak benzerlik analizi yapar"""
        prompt = f"""
        İki YAML dosyasını karşılaştır ve benzerliklerini analiz et:

        YAML 1 (Kullanıcı Girdisi):
        ```yaml
        {yaml1_content}
        ```

        YAML 2 (Kural):
        ```yaml  
        {yaml2_content}
        ```

        Tespit edilen benzerlikler:
        {chr(10).join(similarities[:5])}  # İlk 5 benzerlik

        Tespit edilen farklar:
        {chr(10).join(differences[:5])}  # İlk 5 fark

        Lütfen bu iki YAML dosyası arasındaki benzerlikleri analiz et ve şunları açıkla:
        1. Bu dosyalar neden benzer?
        2. Hangi yapısal özellikler ortak?
        3. Kullanım amaçları açısından ne tür benzerlikler var?
        4. Benzerlik skorunu haklı çıkaran ana faktörler neler?

        Cevabını Türkçe ver ve maksimum 300 kelime kullan.
        """
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama AI hatası: {e}")
            return f"AI analizi yapılamadı: {str(e)}"
    
    def compare_with_rules(self, input_yaml_content: str) -> List[YamlComparison]:
        """Girdi YAML'ini veritabanındaki kurallarla karşılaştırır"""
        input_yaml = self.parse_yaml(input_yaml_content)
        if not input_yaml:
            logger.error("Girdi YAML'i parse edilemedi")
            return []
        
        results = []
        rules = list(self.collection.find())
        
        for rule in rules:
            rule_yaml = self.parse_yaml(rule['yaml_content'])
            if not rule_yaml:
                continue
            
            # Benzerlik skorunu hesapla
            similarity_score = self.calculate_similarity_score(input_yaml, rule_yaml)
            
            # Fark ve benzerlikleri bul
            differences, similarities = self.find_differences_and_similarities(input_yaml, rule_yaml)
            
            # AI analizi yap
            ai_analysis = self.get_ai_analysis(
                input_yaml_content, 
                rule['yaml_content'],
                similarities,
                differences
            )
            
            comparison = YamlComparison(
                rule_id=rule['_id'],
                rule_name=rule['name'],
                similarity_score=similarity_score,
                differences=differences,
                similarities=similarities,
                ai_analysis=ai_analysis,
                comparison_date=datetime.now()
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
    print("YAML Karşılaştırma Uygulaması Başlatılıyor...")
    
    # Comparator'ı başlat
    comparator = YamlComparator()
    
    # Örnek kuralları yükle
    print("Örnek kurallar veritabanına yükleniyor...")
    comparator.initialize_sample_rules()
    
    # Kullanıcıdan YAML girişi al
    print("\nLütfen karşılaştırmak istediğiniz YAML içeriğini girin:")
    print("(Girişi bitirmek için boş bir satırda 'END' yazın)")
    
    yaml_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        yaml_lines.append(line)
    
    input_yaml = "\n".join(yaml_lines)
    
    if not input_yaml.strip():
        print("Geçerli bir YAML içeriği girilmedi!")
        return
    
    print("\nKarşılaştırma yapılıyor...")
    
    # Karşılaştırma yap
    results = comparator.compare_with_rules(input_yaml)
    
    # Sonuçları göster
    comparator.print_comparison_results(results)

if __name__ == "__main__":
    main()