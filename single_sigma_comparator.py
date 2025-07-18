import requests
import json
import pymongo
from pymongo import MongoClient
import yaml
import logging
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SigmaHQComparator:
    def __init__(self, mongo_connection: str, ollama_url="http://localhost:11434", model_name="llama3.1"):
        """
        SigmaHQ kuralları ile tek kural karşılaştırıcısı
        
        Args:
            mongo_connection (str): MongoDB bağlantı string'i
            ollama_url (str): Ollama API URL'i
            model_name (str): Kullanılacak AI model
        """
        self.mongo_connection = mongo_connection
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.api_endpoint = f"{ollama_url}/api/generate"
        self.client = None
        self.collection = None
        
    def connect_mongodb(self, database_name="sigmaDB", collection_name="rules"):
        """MongoDB'ye bağlan"""
        try:
            self.client = MongoClient(self.mongo_connection)
            self.client.admin.command('ping')
            self.collection = self.client[database_name][collection_name]
            logger.info("✅ MongoDB bağlantısı başarılı")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB bağlantı hatası: {e}")
            return False
    
    def test_ollama_connection(self):
        """Ollama bağlantısını test et"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                logger.info(f"✅ Ollama bağlantısı başarılı. Mevcut modeller: {available_models}")
                
                if self.model_name not in available_models:
                    logger.warning(f"⚠️ Model '{self.model_name}' bulunamadı.")
                    if available_models:
                        self.model_name = available_models[0]
                        logger.info(f"📋 '{self.model_name}' modeli kullanılacak")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ollama bağlantı hatası: {e}")
            return False

    def load_sigma_rule_from_file(self, file_path: str) -> Dict[str, Any]:
        """YAML dosyasından Sigma kuralını yükle"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule = yaml.safe_load(f)
            logger.info(f"✅ Sigma kuralı yüklendi: {rule.get('title', 'No title')}")
            return rule
        except Exception as e:
            logger.error(f"❌ YAML dosyası yüklenemedi: {e}")
            return {}

    def load_sigma_rule_from_text(self, yaml_text: str) -> Dict[str, Any]:
        """YAML string'den Sigma kuralını yükle"""
        try:
            rule = yaml.safe_load(yaml_text)
            logger.info(f"✅ Sigma kuralı parse edildi: {rule.get('title', 'No title')}")
            return rule
        except Exception as e:
            logger.error(f"❌ YAML text parse edilemedi: {e}")
            return {}

    def format_rule_for_ai(self, rule: Dict[str, Any]) -> str:
        """Sigma kuralını AI için optimize edilmiş formatta hazırla"""
        formatted_parts = []
        
        # Başlık ve açıklama
        if 'title' in rule:
            formatted_parts.append(f"TITLE: {rule['title']}")
        if 'description' in rule:
            formatted_parts.append(f"DESCRIPTION: {rule['description']}")
        
        # MITRE ATT&CK tags
        if 'tags' in rule:
            tags = rule['tags'] if isinstance(rule['tags'], list) else [rule['tags']]
            formatted_parts.append(f"MITRE_TAGS: {', '.join(tags)}")
        
        # Seviye
        if 'level' in rule:
            formatted_parts.append(f"LEVEL: {rule['level']}")
        
        # Detection mantığı - en önemli kısım
        if 'detection' in rule:
            formatted_parts.append("DETECTION_LOGIC:")
            detection_yaml = yaml.dump(rule['detection'], default_flow_style=False, indent=2)
            formatted_parts.append(detection_yaml)
        
        # Log source
        if 'logsource' in rule:
            formatted_parts.append("LOG_SOURCE:")
            logsource_yaml = yaml.dump(rule['logsource'], default_flow_style=False, indent=2)
            formatted_parts.append(logsource_yaml)
        
        return "\n".join(formatted_parts)

    def calculate_content_similarity(self, input_rule: Dict[str, Any], sigmahq_rule: Dict[str, Any]) -> float:
        """İki Sigma kuralı arasındaki içerik benzerliğini AI ile hesapla"""
        
        input_text = self.format_rule_for_ai(input_rule)
        sigmahq_text = self.format_rule_for_ai(sigmahq_rule)
        
        prompt = f"""
İki Sigma güvenlik kuralının içerik benzerliğini analiz et ve 0.0-1.0 arasında bir skor ver.

Değerlendirme kriterleri:
- Detection mantığı benzerliği (en önemli - %50)
- MITRE ATT&CK teknik benzerliği (%20)
- Log source benzerliği (%15)
- Saldırı türü/amaç benzerliği (%15)

Benzerlik seviyeleri:
1.0 = Neredeyse identik kurallar
0.8-0.9 = Aynı saldırı tekniğini farklı şekilde tespit ediyor
0.6-0.7 = Benzer saldırı kategorisi, farklı implementation
0.4-0.5 = Aynı MITRE technique, farklı yaklaşım
0.2-0.3 = Aynı log source, farklı amaç
0.0-0.1 = Tamamen farklı

KULLANICI KURALI:
{input_text[:1500]}

SIGMAHQ KURALI:
{sigmahq_text[:1500]}

Sadece sayısal benzerlik skoru ver (örnek: 0.75):
"""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Tutarlı skorlar için düşük
                        "max_tokens": 10
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                score_text = result.get('response', '0.0').strip()
                
                # Sayısal skoru çıkar
                import re
                score_match = re.search(r'(\d+\.?\d*)', score_text)
                if score_match:
                    score = float(score_match.group(1))
                    return min(1.0, max(0.0, score))
                    
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ AI benzerlik hesaplama hatası: {e}")
            return 0.0

    def generate_comparison_summary(self, input_rule: Dict[str, Any], similar_rule: Dict[str, Any], score: float) -> str:
        """İki kural arasındaki benzerliğin AI özetini oluştur"""
        
        input_text = self.format_rule_for_ai(input_rule)
        similar_text = self.format_rule_for_ai(similar_rule)
        
        prompt = f"""
İki Sigma kuralını karşılaştır ve benzerliklerini açıkla. 2-3 cümlelik özet yap.

Benzerlik skoru: {score:.2f}

KULLANICI KURALI:
{input_text[:800]}

BENZER KURAL:
{similar_text[:800]}

Neden benzer olduklarını açıkla (detection mantığı, MITRE technique, log source vb.):
"""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 150
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                return summary
                
            return "AI özet oluşturulamadı."
            
        except Exception as e:
            logger.warning(f"⚠️ AI özet hatası: {e}")
            return "AI özet oluşturulamadı."

    def find_most_similar_rules(self, input_rule: Dict[str, Any], threshold: float = 0.3, max_results: int = 10) -> List[Dict[str, Any]]:
        """Verilen Sigma kuralına en benzer SigmaHQ kurallarını bul"""
        
        if not self.collection:
            logger.error("❌ MongoDB bağlantısı yok!")
            return []
        
        # MongoDB'den tüm SigmaHQ kurallarını getir
        logger.info("🔍 SigmaHQ kuralları MongoDB'den getiriliyor...")
        try:
            all_rules = list(self.collection.find())
            logger.info(f"📊 {len(all_rules)} SigmaHQ kuralı bulundu")
        except Exception as e:
            logger.error(f"❌ MongoDB'den veri alınamadı: {e}")
            return []
        
        if not all_rules:
            logger.warning("⚠️ MongoDB'de kural bulunamadı!")
            return []
        
        # Her kural ile benzerlik hesapla
        similarity_results = []
        
        logger.info(f"🤖 AI ile {len(all_rules)} kural karşılaştırılıyor...")
        
        for idx, sigmahq_rule in enumerate(all_rules, 1):
            if idx % 50 == 0:
                logger.info(f"📊 İşlenen: {idx}/{len(all_rules)}")
            
            try:
                # AI ile benzerlik hesapla
                similarity_score = self.calculate_content_similarity(input_rule, sigmahq_rule)
                
                if similarity_score >= threshold:
                    similarity_results.append({
                        'rule': sigmahq_rule,
                        'similarity_score': similarity_score,
                        'rule_id': str(sigmahq_rule.get('_id', '')),
                        'title': sigmahq_rule.get('title', 'No title'),
                        'description': sigmahq_rule.get('description', ''),
                        'tags': sigmahq_rule.get('tags', []),
                        'level': sigmahq_rule.get('level', ''),
                        'author': sigmahq_rule.get('author', ''),
                        'date': sigmahq_rule.get('date', '')
                    })
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ Kural {idx} analiz hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala
        similarity_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # En iyi sonuçlar için AI özeti oluştur
        for result in similarity_results[:max_results]:
            logger.info(f"📝 AI özeti oluşturuluyor: {result['title']}")
            result['ai_summary'] = self.generate_comparison_summary(
                input_rule, 
                result['rule'], 
                result['similarity_score']
            )
        
        logger.info(f"✅ {len(similarity_results)} benzer kural bulundu")
        return similarity_results[:max_results]

    def display_results(self, input_rule: Dict[str, Any], similar_rules: List[Dict[str, Any]]):
        """Sonuçları güzel formatta göster"""
        
        print("\n" + "="*80)
        print("🎯 KULLANICI KURALI:")
        print("="*80)
        print(f"📋 Başlık: {input_rule.get('title', 'No title')}")
        print(f"📄 Açıklama: {input_rule.get('description', 'No description')}")
        print(f"🏷️ Tags: {input_rule.get('tags', [])}")
        print(f"📊 Level: {input_rule.get('level', 'Unknown')}")
        
        if not similar_rules:
            print("\n❌ Benzer kural bulunamadı!")
            return
        
        print(f"\n🏆 EN BENZER {len(similar_rules)} SIGMAHQ KURALI:")
        print("="*80)
        
        for i, result in enumerate(similar_rules, 1):
            print(f"\n{i}. 📋 {result['title']}")
            print(f"   🆔 Rule ID: {result['rule_id']}")
            print(f"   🎯 Benzerlik Skoru: {result['similarity_score']:.1%}")
            print(f"   📄 Açıklama: {result['description'][:100]}...")
            print(f"   🏷️ Tags: {result['tags']}")
            print(f"   📊 Level: {result['level']}")
            print(f"   👤 Author: {result['author']}")
            print(f"   📅 Date: {result['date']}")
            print(f"   🤖 AI Karşılaştırma: {result.get('ai_summary', 'Özet oluşturulamadı')}")
            print("-" * 60)

    def close_connection(self):
        """MongoDB bağlantısını kapat"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB bağlantısı kapatıldı")

def main():
    """Ana fonksiyon"""
    
    # Konfigürasyon
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    DATABASE_NAME = "sigmaDB"
    COLLECTION_NAME = "rules"
    OLLAMA_URL = "http://localhost:11434"
    MODEL_NAME = "llama3.1"
    
    # Comparator'ı başlat
    comparator = SigmaHQComparator(MONGO_CONNECTION, OLLAMA_URL, MODEL_NAME)
    
    # Bağlantıları test et
    if not comparator.test_ollama_connection():
        print("❌ Ollama bağlantısı kurulamadı. Lütfen 'ollama serve' komutunu çalıştırın.")
        return
    
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        print("❌ MongoDB bağlantısı kurulamadı.")
        return
    
    try:
        print("🚀 SigmaHQ Benzerlik Analizi Başlatılıyor...")
        print("="*50)
        
        # Kullanıcı kuralını al
        print("\n📥 Sigma kuralınızı nasıl vermek istiyorsunuz?")
        print("1. YAML dosyası yolu")
        print("2. Doğrudan YAML metni")
        
        choice = input("\nSeçiminiz (1/2): ").strip()
        
        input_rule = {}
        
        if choice == "1":
            file_path = input("📁 YAML dosyası yolu: ").strip()
            input_rule = comparator.load_sigma_rule_from_file(file_path)
        elif choice == "2":
            print("📝 YAML metnini yapıştırın (Ctrl+D ile bitirin):")
            yaml_lines = []
            try:
                while True:
                    line = input()
                    yaml_lines.append(line)
            except EOFError:
                yaml_text = "\n".join(yaml_lines)
                input_rule = comparator.load_sigma_rule_from_text(yaml_text)
        else:
            print("❌ Geçersiz seçim!")
            return
        
        if not input_rule:
            print("❌ Kural yüklenemedi!")
            return
        
        # Benzerlik parametreleri
        try:
            threshold = float(input("\n🎯 Minimum benzerlik eşiği (0.0-1.0) [varsayılan: 0.3]: ") or "0.3")
            max_results = int(input("📊 Maksimum sonuç sayısı [varsayılan: 10]: ") or "10")
        except ValueError:
            threshold = 0.3
            max_results = 10
        
        # Benzerlik analizi yap
        print(f"\n🤖 AI ile SigmaHQ kuralları analiz ediliyor (eşik: {threshold:.1f})...")
        similar_rules = comparator.find_most_similar_rules(input_rule, threshold, max_results)
        
        # Sonuçları göster
        comparator.display_results(input_rule, similar_rules)
        
        # Özet istatistikler
        if similar_rules:
            print(f"\n📈 ÖZET İSTATİSTİKLER:")
            print(f"   🥇 En yüksek benzerlik: {similar_rules[0]['similarity_score']:.1%}")
            print(f"   📊 Ortalama benzerlik: {sum(r['similarity_score'] for r in similar_rules) / len(similar_rules):.1%}")
            print(f"   🔍 Toplam analiz edilen kural sayısı: MongoDB'deki tüm SigmaHQ kuralları")
        
    except KeyboardInterrupt:
        print("\n⏹️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"❌ Ana işlem hatası: {e}")
    finally:
        comparator.close_connection()

if __name__ == "__main__":
    main()