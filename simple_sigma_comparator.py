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

    def extract_detection_content(self, rule: Dict[str, Any]) -> str:
        """Detection içeriğini çıkar ve temizle (ana odak noktası)"""
        detection_parts = []
        
        if 'detection' not in rule:
            return ""
        
        detection = rule['detection']
        if not isinstance(detection, dict):
            return str(detection).lower()
        
        # Selection kısmı (en önemli)
        if 'selection' in detection:
            selection = detection['selection']
            if isinstance(selection, dict):
                for key, value in selection.items():
                    # Field adını temizle (Image|endswith -> image)
                    clean_key = key.split('|')[0].lower()
                    detection_parts.append(clean_key)
                    
                    # Value'ları ekle
                    if isinstance(value, list):
                        detection_parts.extend([str(v).lower() for v in value])
                    else:
                        detection_parts.append(str(value).lower())
            else:
                detection_parts.append(str(selection).lower())
        
        # Filter kısmı
        if 'filter' in detection:
            filter_part = detection['filter']
            if isinstance(filter_part, dict):
                for key, value in filter_part.items():
                    clean_key = key.split('|')[0].lower()
                    detection_parts.append(f"not_{clean_key}")
                    if isinstance(value, list):
                        detection_parts.extend([f"not_{str(v).lower()}" for v in value])
                    else:
                        detection_parts.append(f"not_{str(value).lower()}")
        
        # Condition (ve, veya mantığı)
        if 'condition' in detection:
            condition = str(detection['condition']).lower()
            detection_parts.append(condition)
        
        # Diğer selection'lar (selection1, selection2, vb.)
        for key, value in detection.items():
            if key.startswith('selection') and key != 'selection':
                if isinstance(value, dict):
                    for field, field_value in value.items():
                        clean_field = field.split('|')[0].lower()
                        detection_parts.append(clean_field)
                        if isinstance(field_value, list):
                            detection_parts.extend([str(v).lower() for v in field_value])
                        else:
                            detection_parts.append(str(field_value).lower())
        
        return " ".join(detection_parts)

    def extract_field_names(self, detection: Dict[str, Any]) -> set:
        """Detection'dan field adlarını çıkar (Image, CommandLine, EventID, vb.)"""
        fields = set()
        
        for key, value in detection.items():
            if key in ['selection', 'filter'] or key.startswith('selection'):
                if isinstance(value, dict):
                    for field_name in value.keys():
                        # Pipe'ı temizle: Image|endswith -> Image
                        clean_field = field_name.split('|')[0].lower()
                        fields.add(clean_field)
        
        return fields

    def extract_detection_values(self, detection: Dict[str, Any]) -> set:
        """Detection'dan değerleri çıkar (powershell.exe, cmd.exe, vb.)"""
        values = set()
        
        for key, value in detection.items():
            if key in ['selection', 'filter'] or key.startswith('selection'):
                if isinstance(value, dict):
                    for field_value in value.values():
                        if isinstance(field_value, list):
                            for item in field_value:
                                # Dosya uzantısı veya önemli string'leri al
                                item_str = str(item).lower()
                                if any(ext in item_str for ext in ['.exe', '.dll', '.ps1', '.bat', '.cmd']):
                                    values.add(item_str)
                                elif len(item_str) > 3:  # Kısa string'leri filtrele
                                    values.add(item_str)
                        else:
                            value_str = str(field_value).lower()
                            if len(value_str) > 3:
                                values.add(value_str)
        
        return values

    def calculate_detection_similarity(self, input_rule: Dict[str, Any], sigmahq_rule: Dict[str, Any]) -> float:
        """Detection mantığı benzerliği hesapla (ana odak)"""
        
        input_detection = self.extract_detection_content(input_rule)
        sigmahq_detection = self.extract_detection_content(sigmahq_rule)
        
        if not input_detection or not sigmahq_detection:
            return 0.0
        
        # Ana benzerlik: Detection içeriği
        detection_similarity = SequenceMatcher(None, input_detection, sigmahq_detection).ratio()
        
        # Bonus 1: Aynı field'lar kullanılıyor mu? (Image, CommandLine, EventID, vb.)
        input_fields = self.extract_field_names(input_rule.get('detection', {}))
        sigmahq_fields = self.extract_field_names(sigmahq_rule.get('detection', {}))
        
        field_bonus = 0.0
        if input_fields and sigmahq_fields:
            common_fields = input_fields.intersection(sigmahq_fields)
            field_bonus = len(common_fields) / len(input_fields.union(sigmahq_fields))
        
        # Bonus 2: Aynı value'lar var mı? (powershell.exe, cmd.exe, vb.)
        input_values = self.extract_detection_values(input_rule.get('detection', {}))
        sigmahq_values = self.extract_detection_values(sigmahq_rule.get('detection', {}))
        
        value_bonus = 0.0
        if input_values and sigmahq_values:
            common_values = input_values.intersection(sigmahq_values)
            if common_values:
                value_bonus = len(common_values) / len(input_values.union(sigmahq_values))
        
        # Final score: %70 detection, %20 field, %10 value
        final_score = (detection_similarity * 0.7) + (field_bonus * 0.2) + (value_bonus * 0.1)
        
        return min(1.0, final_score)

    def find_first_similar_rule(self, input_rule: Dict[str, Any], threshold: float = 0.4) -> Optional[Dict[str, Any]]:
        """İlk benzer kuralı bul ve dur (çok hızlı)"""
        
        if self.collection is None:
            logger.error("❌ MongoDB bağlantısı yok!")
            return None
        
        logger.info("🔍 İlk benzer kural aranıyor...")
        
        try:
            # Önce detection field'larına göre akıllı filtreleme
            input_fields = self.extract_field_names(input_rule.get('detection', {}))
            
            # İlk arama: Ana field'lara göre filtrele (daha hızlı)
            query = {}
            if input_fields:
                # Detection'da kullanılan field'ları MongoDB'de ara
                field_queries = []
                for field in input_fields:
                    # MongoDB'de field adı geçen kuralları bul
                    field_queries.append({f"detection.selection.{field}": {"$exists": True}})
                    field_queries.append({f"detection.selection.{field}|endswith": {"$exists": True}})
                    field_queries.append({f"detection.selection.{field}|contains": {"$exists": True}})
                
                if field_queries:
                    query = {"$or": field_queries}
                    logger.info(f"🔍 Detection field filtresi: {list(input_fields)}")
            
            # Eğer field filtresi yoksa, en azından detection'ı olan kuralları al
            if not query:
                query = {"detection": {"$exists": True}}
                logger.info("📋 Tüm detection'lı kurallar aranıyor...")
            
            rules_cursor = self.collection.find(query)
            
            for sigmahq_rule in rules_cursor:
                try:
                    # Detection odaklı benzerlik hesapla
                    similarity_score = self.calculate_detection_similarity(input_rule, sigmahq_rule)
                    
                    if similarity_score >= threshold:
                        logger.info(f"✅ Benzer kural bulundu: {similarity_score:.1%} detection benzerliği")
                        
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
            
            # Field filtresinde bulunamadıysa, threshold'u düşürüp tekrar dene
            if input_fields and threshold > 0.2:
                logger.info(f"🔍 Field filtresi sonuçsuz, threshold düşürülüyor: {threshold} -> {threshold-0.1}")
                return self.find_first_similar_rule(input_rule, threshold - 0.1)
            
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
            
            # Detection odaklı açıklama
            score = similar_rule['similarity_score']
            
            # Field ve value benzerliğini kontrol et
            input_fields = self.extract_field_names(input_rule.get('detection', {}))
            sigmahq_fields = self.extract_field_names(similar_rule['rule'].get('detection', {}))
            common_fields = input_fields.intersection(sigmahq_fields)
            
            input_values = self.extract_detection_values(input_rule.get('detection', {}))
            sigmahq_values = self.extract_detection_values(similar_rule['rule'].get('detection', {}))
            common_values = input_values.intersection(sigmahq_values)
            
            explanation_parts = []
            
            if score > 0.8:
                explanation_parts.append("🔥 Çok yüksek benzerlik")
            elif score > 0.6:
                explanation_parts.append("✅ Yüksek benzerlik")
            elif score > 0.4:
                explanation_parts.append("📊 Orta benzerlik")
            else:
                explanation_parts.append("🔍 Düşük benzerlik")
            
            if common_fields:
                explanation_parts.append(f"Ortak field'lar: {', '.join(list(common_fields)[:3])}")
            
            if common_values:
                explanation_parts.append(f"Ortak değerler: {', '.join(list(common_values)[:2])}")
            
            explanation = " - ".join(explanation_parts)
            print(f"🤖 Detection Analizi: {explanation}")
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