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

    def format_detection_for_ai(self, rule: Dict[str, Any]) -> str:
        """Sadece detection mantığını AI için hazırla (basit ve odaklı)"""
        
        if 'detection' not in rule:
            return "DETECTION: None"
        
        detection = rule['detection']
        detection_yaml = yaml.dump(detection, default_flow_style=False, indent=2)
        
        # Sadece detection + kısa açıklama
        title = rule.get('title', 'Unknown Rule')
        
        return f"RULE: {title}\nDETECTION:\n{detection_yaml}"

    def calculate_detection_similarity(self, input_rule: Dict[str, Any], sigmahq_rule: Dict[str, Any]) -> float:
        """İki Sigma kuralının detection benzerliğini AI ile hesapla (sadece detection odaklı)"""
        
        input_detection = self.format_detection_for_ai(input_rule)
        sigmahq_detection = self.format_detection_for_ai(sigmahq_rule)
        
        prompt = f"""
İki Sigma kuralının DETECTION mantığını karşılaştır ve 0.0-1.0 arasında benzerlik skoru ver.

SADECE DETECTION mantığına odaklan:
- Field isimleri (Image, CommandLine, EventID, vb.)
- Field değerleri (powershell.exe, cmd.exe, vb.) 
- Condition mantığı (selection, filter, vb.)
- Detection yapısı (selection1, selection2, vb.)

Benzerlik seviyeleri:
1.0 = Neredeyse aynı detection mantığı
0.8-0.9 = Aynı field'ları kullanıyor, benzer değerler
0.6-0.7 = Benzer field'lar, farklı değerler
0.4-0.5 = Farklı field'lar ama benzer amaç
0.2-0.3 = Az ortak özellik
0.0-0.1 = Tamamen farklı detection

KULLANICI DETECTION:
{input_detection}

SIGMAHQ DETECTION:
{sigmahq_detection}

Sadece sayısal skor ver (örnek: 0.75):
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

    def generate_detection_summary(self, input_rule: Dict[str, Any], similar_rule: Dict[str, Any], score: float) -> str:
        """İki kuralın detection benzerliği hakkında AI özeti oluştur"""
        
        input_detection = self.format_detection_for_ai(input_rule)
        similar_detection = self.format_detection_for_ai(similar_rule)
        
        prompt = f"""
İki Sigma kuralının DETECTION mantığını karşılaştır. Neden benzer olduklarını 1-2 cümleyle açıkla.

Detection benzerlik skoru: {score:.2f}

KULLANICI DETECTION:
{input_detection}

BENZER KURAL DETECTION:
{similar_detection}

Hangi field'lar ortak, hangi değerler benzer? Kısa açıkla:
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

    def find_first_similar_rule(self, input_rule: Dict[str, Any], threshold: float = 0.4) -> Optional[Dict[str, Any]]:
        """İlk benzer kuralı bul ve dur (hızlı ve basit)"""
        
        if not self.collection:
            logger.error("❌ MongoDB bağlantısı yok!")
            return None
        
        logger.info("🔍 İlk benzer kural aranıyor (AI ile detection analizi)...")
        
        try:
            # Detection odaklı filtreleme
            rules_cursor = self.collection.find({"detection": {"$exists": True}})
            
            for idx, sigmahq_rule in enumerate(rules_cursor, 1):
                if idx % 50 == 0:
                    logger.info(f"📊 İşlenen: {idx} kural")
                
                try:
                    # AI ile detection benzerliği hesapla
                    similarity_score = self.calculate_detection_similarity(input_rule, sigmahq_rule)
                    
                    if similarity_score >= threshold:
                        logger.info(f"✅ Benzer kural bulundu: {similarity_score:.1%} detection benzerliği")
                        
                        # AI özeti oluştur
                        ai_summary = self.generate_detection_summary(input_rule, sigmahq_rule, similarity_score)
                        
                        return {
                            'rule': sigmahq_rule,
                            'similarity_score': similarity_score,
                            'rule_id': str(sigmahq_rule.get('_id', '')),
                            'title': sigmahq_rule.get('title', 'No title'),
                            'description': sigmahq_rule.get('description', ''),
                            'tags': sigmahq_rule.get('tags', []),
                            'level': sigmahq_rule.get('level', ''),
                                                     'author': sigmahq_rule.get('author', ''),
                             'date': sigmahq_rule.get('date', ''),
                             'ai_summary': ai_summary
                         }
                    
                    # Rate limiting
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Kural {idx} analiz hatası: {e}")
                    continue
            
            logger.info("❌ Benzer kural bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"❌ Arama hatası: {e}")
            return None

    def display_result(self, input_rule: Dict[str, Any], similar_rule: Optional[Dict[str, Any]]):
        """Basit sonuç gösterimi (tek kural için)"""
        
        print("\n" + "="*60)
        print("🎯 KULLANICI KURALI (Detection Odaklı):")
        print("="*60)
        print(f"📋 Başlık: {input_rule.get('title', 'No title')}")
        print(f"📄 Açıklama: {input_rule.get('description', 'No description')[:80]}...")
        
        if similar_rule:
            print(f"\n🏆 BENZER SIGMAHQ KURALI BULUNDU:")
            print("="*60)
            print(f"📋 Başlık: {similar_rule['title']}")
            print(f"🆔 Rule ID: {similar_rule['rule_id']}")
            print(f"🎯 Detection Benzerliği: {similar_rule['similarity_score']:.1%}")
            print(f"📄 Açıklama: {similar_rule['description'][:80]}...")
            print(f"🏷️ Tags: {similar_rule['tags'][:3]}...")  # İlk 3 tag
            print(f"📊 Level: {similar_rule['level']}")
            print(f"👤 Author: {similar_rule['author']}")
            print(f"📅 Date: {similar_rule['date']}")
            print(f"🤖 AI Detection Analizi: {similar_rule.get('ai_summary', 'Özet oluşturulamadı')}")
        else:
            print("\n❌ BENZER KURAL BULUNAMADI!")
            print("💡 Threshold'u düşürmeyi deneyin (örn: 0.3)")
            print("🔍 Sistem sadece detection mantığına odaklanıyor")

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
        
        # Detection benzerlik parametresi
        try:
            threshold = float(input("\n🎯 Minimum detection benzerlik eşiği (0.0-1.0) [varsayılan: 0.4]: ") or "0.4")
        except ValueError:
            threshold = 0.4
        
        # Basit detection analizi
        print(f"\n🤖 AI ile detection odaklı analiz başlıyor (eşik: {threshold:.1f})...")
        similar_rule = comparator.find_first_similar_rule(input_rule, threshold)
        
        # Sonucu göster
        comparator.display_result(input_rule, similar_rule)
        
    except KeyboardInterrupt:
        print("\n⏹️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"❌ Ana işlem hatası: {e}")
    finally:
        comparator.close_connection()

if __name__ == "__main__":
    main()