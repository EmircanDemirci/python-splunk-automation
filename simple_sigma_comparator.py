import pymongo
from pymongo import MongoClient
import yaml
import logging
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleSigmaComparator:
    def __init__(self, mongo_connection: str):
        """
        Basit ve hızlı Sigma karşılaştırıcısı - sadece ilk benzer kuralı bulur
        
        Args:
            mongo_connection (str): MongoDB bağlantı string'i
        """
        self.mongo_connection = mongo_connection
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

    def extract_key_fields(self, rule: Dict[str, Any]) -> str:
        """Kuraldan anahtar alanları çıkar (hızlı karşılaştırma için)"""
        key_parts = []
        
        # Title benzerliği
        if 'title' in rule:
            key_parts.append(rule['title'].lower())
        
        # Detection mantığını basitleştir
        if 'detection' in rule:
            detection = rule['detection']
            if isinstance(detection, dict):
                # Sadece selection kısmını al
                if 'selection' in detection:
                    selection = str(detection['selection']).lower()
                    key_parts.append(selection)
        
        # MITRE tags
        if 'tags' in rule:
            tags = rule['tags'] if isinstance(rule['tags'], list) else [rule['tags']]
            key_parts.extend([tag.lower() for tag in tags])
        
        # Log source
        if 'logsource' in rule:
            logsource = str(rule['logsource']).lower()
            key_parts.append(logsource)
        
        return " ".join(key_parts)

    def calculate_simple_similarity(self, input_rule: Dict[str, Any], sigmahq_rule: Dict[str, Any]) -> float:
        """Basit string benzerliği hesapla (AI olmadan)"""
        
        input_text = self.extract_key_fields(input_rule)
        sigmahq_text = self.extract_key_fields(sigmahq_rule)
        
        if not input_text or not sigmahq_text:
            return 0.0
        
        # SequenceMatcher ile hızlı benzerlik
        similarity = SequenceMatcher(None, input_text, sigmahq_text).ratio()
        
        # MITRE tag bonus
        input_tags = set(input_rule.get('tags', []))
        sigmahq_tags = set(sigmahq_rule.get('tags', []))
        
        if input_tags and sigmahq_tags:
            tag_overlap = len(input_tags.intersection(sigmahq_tags)) / len(input_tags.union(sigmahq_tags))
            similarity = (similarity * 0.7) + (tag_overlap * 0.3)
        
        return similarity

    def find_first_similar_rule(self, input_rule: Dict[str, Any], threshold: float = 0.4) -> Optional[Dict[str, Any]]:
        """İlk benzer kuralı bul ve dur (çok hızlı)"""
        
        if self.collection is None:
            logger.error("❌ MongoDB bağlantısı yok!")
            return None
        
        logger.info("🔍 İlk benzer kural aranıyor...")
        
        try:
            # Önce MITRE tag'e göre filtreleme yap (hızlandırma)
            input_tags = input_rule.get('tags', [])
            
            if input_tags:
                # Tag'i olan kuralları önce ara
                query = {"tags": {"$in": input_tags}}
                logger.info(f"🏷️ MITRE tag filtresi: {input_tags}")
            else:
                # Tüm kuralları ara
                query = {}
            
            rules_cursor = self.collection.find(query)
            
            for sigmahq_rule in rules_cursor:
                try:
                    # Hızlı benzerlik hesapla
                    similarity_score = self.calculate_simple_similarity(input_rule, sigmahq_rule)
                    
                    if similarity_score >= threshold:
                        logger.info(f"✅ Benzer kural bulundu: {similarity_score:.1%} benzerlik")
                        
                        return {
                            'rule': sigmahq_rule,
                            'similarity_score': similarity_score,
                            'rule_id': str(sigmahq_rule.get('_id', '')),
                            'title': sigmahq_rule.get('title', 'No title'),
                            'description': sigmahq_rule.get('description', ''),
                            'tags': sigmahq_rule.get('tags', []),
                            'level': sigmahq_rule.get('level', ''),
                            'author': sigmahq_rule.get('author', ''),
                            'date': sigmahq_rule.get('date', '')
                        }
                        
                except Exception as e:
                    logger.warning(f"⚠️ Kural analiz hatası: {e}")
                    continue
            
            # MITRE tag filtresinde bulunamadıysa, tüm kuralları dene
            if input_tags:
                logger.info("🔍 MITRE tag filtresi sonuçsuz, tüm kurallar aranıyor...")
                return self.find_first_similar_rule(input_rule, threshold)
            
            logger.info("❌ Benzer kural bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"❌ Arama hatası: {e}")
            return None

    def display_simple_result(self, input_rule: Dict[str, Any], similar_rule: Optional[Dict[str, Any]]):
        """Basit sonuç gösterimi"""
        
        print("\n" + "="*60)
        print("🎯 KULLANICI KURALI:")
        print("="*60)
        print(f"📋 Başlık: {input_rule.get('title', 'No title')}")
        print(f"📄 Açıklama: {input_rule.get('description', 'No description')[:100]}...")
        print(f"🏷️ Tags: {input_rule.get('tags', [])}")
        
        if similar_rule:
            print(f"\n🏆 BENZER SIGMAHQ KURALI BULUNDU:")
            print("="*60)
            print(f"📋 Başlık: {similar_rule['title']}")
            print(f"🆔 Rule ID: {similar_rule['rule_id']}")
            print(f"🎯 Benzerlik: {similar_rule['similarity_score']:.1%}")
            print(f"📄 Açıklama: {similar_rule['description'][:100]}...")
            print(f"🏷️ Tags: {similar_rule['tags']}")
            print(f"📊 Level: {similar_rule['level']}")
            print(f"👤 Author: {similar_rule['author']}")
            print(f"📅 Date: {similar_rule['date']}")
            
            # Basit benzerlik açıklaması
            score = similar_rule['similarity_score']
            if score > 0.8:
                explanation = "🔥 Çok yüksek benzerlik - Neredeyse aynı kural!"
            elif score > 0.6:
                explanation = "✅ Yüksek benzerlik - Benzer detection mantığı"
            elif score > 0.4:
                explanation = "📊 Orta benzerlik - Aynı kategori, farklı yaklaşım"
            else:
                explanation = "🔍 Düşük benzerlik - Benzer özellikler mevcut"
            
            print(f"🤖 Açıklama: {explanation}")
        else:
            print("\n❌ BENZER KURAL BULUNAMADI!")
            print("💡 Threshold'u düşürmeyi deneyin (örn: 0.3)")

    def close_connection(self):
        """MongoDB bağlantısını kapat"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB bağlantısı kapatıldı")

def main():
    """Ana fonksiyon - Basit ve hızlı"""
    
    # Konfigürasyon
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    DATABASE_NAME = "sigmaDB"
    COLLECTION_NAME = "rules"
    
    # Basit comparator başlat
    comparator = SimpleSigmaComparator(MONGO_CONNECTION)
    
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        print("❌ MongoDB bağlantısı kurulamadı.")
        return
    
    try:
        print("🚀 Basit SigmaHQ Benzerlik Analizi")
        print("="*40)
        
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
        
        # Threshold al
        try:
            threshold = float(input("\n🎯 Minimum benzerlik eşiği (0.0-1.0) [varsayılan: 0.4]: ") or "0.4")
        except ValueError:
            threshold = 0.4
        
        # Hızlı analiz
        print(f"\n⚡ Hızlı benzerlik analizi başlıyor (eşik: {threshold:.1f})...")
        similar_rule = comparator.find_first_similar_rule(input_rule, threshold)
        
        # Sonucu göster
        comparator.display_simple_result(input_rule, similar_rule)
        
    except KeyboardInterrupt:
        print("\n⏹️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"❌ Ana işlem hatası: {e}")
    finally:
        comparator.close_connection()

if __name__ == "__main__":
    main()