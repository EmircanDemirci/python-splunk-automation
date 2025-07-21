#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gelişmiş Sigma Kural Karşılaştırıcısı
Hızlı, paralel ve detaylı analiz ile Sigma kurallarını karşılaştırır
"""

import yaml
import os
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import difflib
import hashlib

# Logging yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Konfigürasyon
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "sigmaDB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rules")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
RULE_LIMIT = int(os.getenv("RULE_LIMIT", "10"))

@dataclass
class SigmaRule:
    """Sigma kuralı veri modeli"""
    id: str
    title: str
    description: str
    detection: Dict[str, Any]
    level: str
    tags: List[str]
    author: str
    date: str
    logsource: Dict[str, Any]
    references: List[str] = None
    falsepositives: List[str] = None

@dataclass
class ComparisonResult:
    """Karşılaştırma sonucu"""
    rule_id: str
    rule_title: str
    similarity_score: float
    structural_similarity: float
    semantic_similarity: float
    ai_analysis: str
    detailed_comparison: Dict[str, Any]
    processing_time: float
    comparison_date: str

class SigmaComparator:
    """Ana karşılaştırıcı sınıf"""
    
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.cache = {}
        
    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """YAML dosyasını yükler"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                logger.info(f"YAML dosyası başarıyla yüklendi: {file_path}")
                return content
        except Exception as e:
            logger.error(f"YAML yükleme hatası: {e}")
            raise

    def fetch_rules_from_mongo(self, limit: int = RULE_LIMIT) -> List[SigmaRule]:
        """MongoDB'den kuralları çeker"""
        try:
            pipeline = [
                {"$sort": {"_id": -1}},  # En son eklenenler önce
                {"$limit": limit}
            ]
            
            rules_data = list(self.collection.aggregate(pipeline))
            rules = []
            
            for rule_data in rules_data:
                rule = SigmaRule(
                    id=str(rule_data.get("_id", "")),
                    title=rule_data.get("title", ""),
                    description=rule_data.get("description", ""),
                    detection=rule_data.get("detection", {}),
                    level=rule_data.get("level", "medium"),
                    tags=rule_data.get("tags", []),
                    author=rule_data.get("author", ""),
                    date=rule_data.get("date", ""),
                    logsource=rule_data.get("logsource", {}),
                    references=rule_data.get("references", []),
                    falsepositives=rule_data.get("falsepositives", [])
                )
                rules.append(rule)
            
            logger.info(f"MongoDB'den {len(rules)} kural çekildi")
            return rules
            
        except Exception as e:
            logger.error(f"MongoDB bağlantı hatası: {e}")
            raise

    def calculate_structural_similarity(self, rule1: Dict, rule2: Dict) -> float:
        """Yapısal benzerlik hesaplar"""
        def extract_features(rule):
            features = set()
            
            # Detection kısmından özellikler çıkar
            detection = rule.get("detection", {})
            for key, value in detection.items():
                if isinstance(value, dict):
                    for subkey in value.keys():
                        features.add(f"detection.{key}.{subkey}")
                elif isinstance(value, list):
                    features.add(f"detection.{key}.list")
                else:
                    features.add(f"detection.{key}")
            
            # Logsource özellikleri
            logsource = rule.get("logsource", {})
            for key in logsource.keys():
                features.add(f"logsource.{key}")
            
            # Diğer özellikler
            features.add(f"level.{rule.get('level', 'unknown')}")
            
            for tag in rule.get("tags", []):
                features.add(f"tag.{tag}")
                
            return features
        
        features1 = extract_features(rule1)
        features2 = extract_features(rule2)
        
        if not features1 and not features2:
            return 1.0
        if not features1 or not features2:
            return 0.0
            
        intersection = len(features1.intersection(features2))
        union = len(features1.union(features2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_semantic_similarity(self, rule1: Dict, rule2: Dict) -> float:
        """Semantik benzerlik hesaplar"""
        def get_text_content(rule):
            texts = []
            texts.append(rule.get("title", ""))
            texts.append(rule.get("description", ""))
            
            # Detection içindeki string değerler
            detection = rule.get("detection", {})
            for value in detection.values():
                if isinstance(value, str):
                    texts.append(value)
                elif isinstance(value, dict):
                    for subvalue in value.values():
                        if isinstance(subvalue, str):
                            texts.append(subvalue)
                        elif isinstance(subvalue, list):
                            texts.extend([str(item) for item in subvalue if isinstance(item, str)])
            
            return " ".join(texts).lower()
        
        text1 = get_text_content(rule1)
        text2 = get_text_content(rule2)
        
        # Basit kelime tabanlı benzerlik
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def create_detailed_comparison(self, rule1: Dict, rule2: Dict) -> Dict[str, Any]:
        """Detaylı karşılaştırma raporu oluşturur"""
        comparison = {
            "common_elements": [],
            "differences": [],
            "logsource_match": False,
            "level_match": False,
            "tag_overlap": [],
            "detection_analysis": {}
        }
        
        # Logsource karşılaştırması
        ls1 = rule1.get("logsource", {})
        ls2 = rule2.get("logsource", {})
        comparison["logsource_match"] = ls1 == ls2
        
        # Level karşılaştırması
        comparison["level_match"] = rule1.get("level") == rule2.get("level")
        
        # Tag overlap
        tags1 = set(rule1.get("tags", []))
        tags2 = set(rule2.get("tags", []))
        comparison["tag_overlap"] = list(tags1.intersection(tags2))
        
        # Detection analizi
        det1 = rule1.get("detection", {})
        det2 = rule2.get("detection", {})
        
        common_keys = set(det1.keys()).intersection(set(det2.keys()))
        comparison["detection_analysis"]["common_keys"] = list(common_keys)
        comparison["detection_analysis"]["unique_to_rule1"] = list(set(det1.keys()) - set(det2.keys()))
        comparison["detection_analysis"]["unique_to_rule2"] = list(set(det2.keys()) - set(det1.keys()))
        
        return comparison

    async def ask_ollama_async(self, content1: Dict, content2: Dict, session: aiohttp.ClientSession) -> str:
        """Async Ollama API çağrısı"""
        prompt = f"""Sen bir siber güvenlik uzmanısın. İki Sigma kuralını derinlemesine analiz et.

### KURAL 1:
{yaml.dump(content1, default_flow_style=False)}

### KURAL 2:
{yaml.dump(content2, default_flow_style=False)}

ANALİZ KRİTERLERİ:
1. Tespit ettikleri saldırı teknikleri
2. Kullandıkları log kaynakları
3. Detection mantığı ve koşulları
4. Hedeflenen davranış kalıpları
5. Risk seviyeleri
6. MITRE ATT&CK teknikleri

YANIT FORMATI (Türkçe):
🎯 Benzerlik Derecesi: [Çok Yüksek/Yüksek/Orta/Düşük/Çok Düşük]
🔍 Ana Ortak Noktalar: [3-5 madde]
⚡ Temel Farklılıklar: [3-5 madde]
🧠 Teknik Analiz: [Detaylı açıklama]
📊 Sonuç: [1-2 cümle özet]"""

        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
            
            async with session.post(OLLAMA_URL, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "AI analizi yapılamadı")
                else:
                    return f"API Hatası: {response.status}"
                    
        except Exception as e:
            logger.error(f"Ollama API hatası: {e}")
            return f"Bağlantı hatası: {str(e)}"

    async def compare_with_rule_async(self, target_rule: Dict, rule: SigmaRule, session: aiohttp.ClientSession) -> ComparisonResult:
        """Tek bir kuralla async karşılaştırma"""
        start_time = time.time()
        
        try:
            # Yapısal benzerlik
            structural_sim = self.calculate_structural_similarity(target_rule, asdict(rule))
            
            # Semantik benzerlik
            semantic_sim = self.calculate_semantic_similarity(target_rule, asdict(rule))
            
            # Genel benzerlik skoru (ağırlıklı ortalama)
            overall_similarity = (structural_sim * 0.6) + (semantic_sim * 0.4)
            
            # Detaylı karşılaştırma
            detailed_comparison = self.create_detailed_comparison(target_rule, asdict(rule))
            
            # AI analizi
            ai_analysis = await self.ask_ollama_async(target_rule, asdict(rule), session)
            
            processing_time = time.time() - start_time
            
            result = ComparisonResult(
                rule_id=rule.id,
                rule_title=rule.title,
                similarity_score=overall_similarity,
                structural_similarity=structural_sim,
                semantic_similarity=semantic_sim,
                ai_analysis=ai_analysis,
                detailed_comparison=detailed_comparison,
                processing_time=processing_time,
                comparison_date=datetime.now().isoformat()
            )
            
            logger.info(f"Karşılaştırma tamamlandı: {rule.title[:50]}... (%.2f sn)", processing_time)
            return result
            
        except Exception as e:
            logger.error(f"Karşılaştırma hatası: {e}")
            return None

    async def compare_all_async(self, target_rule: Dict, rules: List[SigmaRule]) -> List[ComparisonResult]:
        """Tüm kurallarla paralel karşılaştırma"""
        results = []
        
        connector = aiohttp.TCPConnector(limit=MAX_WORKERS)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 dakika timeout
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for rule in rules:
                task = self.compare_with_rule_async(target_rule, rule, session)
                tasks.append(task)
            
            logger.info(f"{len(tasks)} paralel karşılaştırma başlatılıyor...")
            
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_results:
                if isinstance(result, ComparisonResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Task hatası: {result}")
        
        # Benzerlik skoruna göre sırala
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results

    def save_results_to_file(self, results: List[ComparisonResult], filename: str = None):
        """Sonuçları dosyaya kaydet"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sigma_comparison_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([asdict(result) for result in results], f, ensure_ascii=False, indent=2)
            logger.info(f"Sonuçlar kaydedildi: {filename}")
        except Exception as e:
            logger.error(f"Dosya kaydetme hatası: {e}")

    def print_results(self, results: List[ComparisonResult], top_n: int = 5):
        """Sonuçları güzel formatta yazdır"""
        print("\n" + "="*100)
        print("🔍 SIGMA KURAL KARŞILAŞTIRMA SONUÇLARI")
        print("="*100)
        
        print(f"\n📊 Toplam {len(results)} kural analiz edildi")
        print(f"⏱️  Ortalama işlem süresi: {sum(r.processing_time for r in results) / len(results):.2f} saniye")
        print(f"🏆 En yüksek benzerlik: %{results[0].similarity_score * 100:.1f}" if results else "Sonuç yok")
        
        print(f"\n🎯 EN BENZER {min(top_n, len(results))} KURAL:")
        print("-" * 100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. KURAL: {result.rule_title}")
            print(f"   ID: {result.rule_id}")
            print(f"   📊 Genel Benzerlik: %{result.similarity_score * 100:.1f}")
            print(f"   🏗️  Yapısal Benzerlik: %{result.structural_similarity * 100:.1f}")
            print(f"   🧠 Semantik Benzerlik: %{result.semantic_similarity * 100:.1f}")
            print(f"   ⏱️  İşlem Süresi: {result.processing_time:.2f}s")
            
            # Detaylı analiz
            details = result.detailed_comparison
            if details.get("tag_overlap"):
                print(f"   🏷️  Ortak Etiketler: {', '.join(details['tag_overlap'])}")
            if details.get("logsource_match"):
                print(f"   📋 Log Kaynağı: ✅ Eşleşiyor")
            else:
                print(f"   📋 Log Kaynağı: ❌ Farklı")
            
            print(f"\n   🤖 AI ANALİZİ:")
            print("   " + "\n   ".join(result.ai_analysis.split("\n")))
            print("-" * 100)

    async def main_async(self, yaml_path: str, rule_limit: int = RULE_LIMIT, save_results: bool = True):
        """Ana async fonksiyon"""
        start_time = time.time()
        
        try:
            # Target rule yükle
            logger.info(f"Hedef kural yükleniyor: {yaml_path}")
            target_rule = self.load_yaml(yaml_path)
            
            # MongoDB'den kuralları çek
            logger.info(f"MongoDB'den {rule_limit} kural çekiliyor...")
            rules = self.fetch_rules_from_mongo(rule_limit)
            
            if not rules:
                logger.warning("MongoDB'de kural bulunamadı!")
                return
            
            # Paralel karşılaştırma başlat
            logger.info("Paralel karşılaştırma başlatılıyor...")
            results = await self.compare_all_async(target_rule, rules)
            
            total_time = time.time() - start_time
            logger.info(f"Toplam işlem süresi: {total_time:.2f} saniye")
            
            # Sonuçları göster
            self.print_results(results)
            
            # Sonuçları kaydet
            if save_results:
                self.save_results_to_file(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Ana işlem hatası: {e}")
            raise
        finally:
            self.mongo_client.close()

def main(yaml_path: str, rule_limit: int = RULE_LIMIT):
    """Ana fonksiyon - sync wrapper"""
    comparator = SigmaComparator()
    return asyncio.run(comparator.main_async(yaml_path, rule_limit))

if __name__ == "__main__":
    import sys
    
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else "deneme_kural.yml"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else RULE_LIMIT
    
    print(f"🚀 Gelişmiş Sigma Karşılaştırıcı başlatılıyor...")
    print(f"📁 Hedef dosya: {yaml_file}")
    print(f"🔢 Karşılaştırma limiti: {limit}")
    print(f"⚡ Paralel worker sayısı: {MAX_WORKERS}")
    
    main(yaml_file, limit)