import yaml
import pymongo
import re
from difflib import SequenceMatcher
from collections import Counter
from mongodb_connection import MongoConnector
import logging

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SigmaRuleComparator:
    def __init__(self, collection):
        self.collection = collection

    def tokenize_string(self, text):
        """String'i kelime ve özel karakterlere ayır"""
        if not text:
            return []

        # Kelimeler, sayılar, özel karakterleri ayrı ayrı yakala
        tokens = re.findall(r'\b\w+\b|[^\w\s]', str(text).lower())
        return [token for token in tokens if token.strip()]

    def is_number(self, text):
        """String'in sayı olup olmadığını kontrol et"""
        try:
            float(text)
            return True
        except ValueError:
            return False

    def clean_value(self, value):
        """Value'lardan dosya uzantılarını ve gereksiz karakterleri temizle"""
        if not isinstance(value, str):
            return str(value)
        
        # Dosya uzantılarını kaldır (executable, script, archive, document formats)
        file_extensions = [
            # Executable files
            '.exe', '.dll', '.sys', '.drv', '.ocx', '.cpl', '.scr', '.com', '.pif',
            # Script files  
            '.bat', '.cmd', '.ps1', '.psm1', '.psd1', '.vbs', '.vbe', '.js', '.jse',
            '.wsh', '.wsf', '.hta', '.py', '.pl', '.php', '.rb', '.sh',
            # Archive files
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.cab', '.msi',
            # Document files
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.rtf',
            # Log and config files
            '.txt', '.log', '.cfg', '.conf', '.ini', '.xml', '.json', '.yaml', '.yml',
            # Image files
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            # Other common files
            '.tmp', '.temp', '.bak', '.old', '.orig'
        ]
        
        cleaned_value = value.lower().strip()
        
        # Uzantıları kaldır
        for ext in file_extensions:
            if cleaned_value.endswith(ext):
                cleaned_value = cleaned_value[:-len(ext)]
                break
        
        # Gereksiz karakterleri temizle
        cleaned_value = re.sub(r'[\\\/\'"]+', '', cleaned_value)  # Path separators ve quotes
        cleaned_value = re.sub(r'\s+', ' ', cleaned_value)  # Çoklu boşlukları tek boşluğa çevir
        cleaned_value = cleaned_value.strip()
        
        return cleaned_value if cleaned_value else value  # Eğer tamamen boş kaldıysa orijinalini döndür

    def extract_detection_components(self, detection_dict):
        """Detection bölümünden field'ları ve değerleri ayrı ayrı çıkar"""
        fields = set()
        values = []

        def recursive_extract(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'condition':  # condition'ı skip et
                        continue

                    # Field ismini ekle
                    fields.add(key)

                    if isinstance(value, (str, int, float)):
                        cleaned_val = self.clean_value(str(value))
                        if cleaned_val:  # Boş değilse ekle
                            values.append(cleaned_val)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, (str, int, float)):
                                cleaned_val = self.clean_value(str(item))
                                if cleaned_val:  # Boş değilse ekle
                                    values.append(cleaned_val)
                            elif isinstance(item, dict):
                                recursive_extract(item, key)
                    elif isinstance(value, dict):
                        recursive_extract(value, key)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_extract(item, parent_key)

        recursive_extract(detection_dict)
        return list(fields), values

    def is_meaningful_match(self, s1, s2, score):
        """Eşleşmenin anlamlı olup olmadığını kontrol et"""
        s1_clean = str(s1).lower().strip()
        s2_clean = str(s2).lower().strip()
        
        # Boş stringler
        if not s1_clean or not s2_clean:
            return False
        
        min_length = min(len(s1_clean), len(s2_clean))
        max_length = max(len(s1_clean), len(s2_clean))
        
        # Çok kısa stringler için sıkı kontrol (3 karakter altı)
        if min_length < 3:
            # Baştan eşleşme varsa kabul et
            if s1_clean.startswith(s2_clean) or s2_clean.startswith(s1_clean):
                return score > 0.6
            # Kısa string uzun stringin içindeyse ve baştan eşleşmiyorsa suspicious
            if max_length > 5:
                return False
            # İkisi de çok kısaysa sadece tam eşleşmeyi kabul et
            return s1_clean == s2_clean
            
        # Length ratio kontrolü - çok farklı uzunluklardaysa skip et
        length_ratio = min_length / max_length if max_length > 0 else 0
        if length_ratio < 0.4:  # Biri diğerinin %40'ından kısaysa
            return False
            
        # Kısa substring eşleşmelerini filtrele
        if min_length <= 5:
            # Baştan eşleşme varsa kabul et (daha gevşek kontrol)
            if s1_clean.startswith(s2_clean) or s2_clean.startswith(s1_clean):
                return score > 0.5  # Baştan eşleşmelerde daha düşük threshold
            else:
                # Baştan eşleşme yoksa sıkı kontrol
                if score < 0.85:
                    return False
                # Ve mutlaka tam substring olmalı
                if not (s1_clean in s2_clean or s2_clean in s1_clean):
                    return False
                
        # Orta uzunlukta stringler için (6-10 karakter)
        elif min_length <= 10:
            if score < 0.6:
                return False
        
        # Uzun stringler için daha esnek olabiliriz
        else:
            if score < 0.5:
                return False
        
        # Son kontrol: Anagram benzeri durumlar (urtlfef vs rtf)
        # Eğer karakterler çok benzer ama kelime başlangıçları farklıysa suspicious
        if score > 0.5 and score < 0.8:
            s1_chars = set(s1_clean)
            s2_chars = set(s2_clean)
            char_overlap = len(s1_chars & s2_chars) / max(len(s1_chars), len(s2_chars))
            
            if char_overlap > 0.7 and s1_clean[0] != s2_clean[0]:
                return False
        
        return True

    def fuzzy_similarity(self, strings1, strings2):
        """İki string listesi arasındaki benzerliği hesapla (kelime/sayı benzerliği cezası dahil)"""
        # Input'ları liste haline getir
        if isinstance(strings1, str):
            strings1 = [strings1]
        if isinstance(strings2, str):
            strings2 = [strings2]
            
        if not strings1 or not strings2:
            return 0.0

        total_score = 0.0
        comparisons = 0

        for s1 in strings1:
            best_score = 0.0
            for s2 in strings2:
                s1_clean = str(s1).lower()
                s2_clean = str(s2).lower()

                fuzzy_score = SequenceMatcher(None, s1_clean, s2_clean).ratio()

                # Substring bonus
                substring_bonus = 0.2 if s1_clean in s2_clean or s2_clean in s1_clean else 0.0

                # Kelime/sayı ortaklığı varsa ve substring değilse -> ceza
                penalty = 0.0
                if substring_bonus == 0.0:
                    s1_tokens = set(re.findall(r'\w+', s1_clean))
                    s2_tokens = set(re.findall(r'\w+', s2_clean))
                    common_tokens = s1_tokens & s2_tokens

                    if any(token.isdigit() or token.isalpha() for token in common_tokens):
                        penalty = 0.3  # ceza uygula

                combined_score = max(0.0, min(1.0, fuzzy_score + substring_bonus - penalty))
                
                # Anlamlı eşleşme kontrolü - saçma eşleşmeleri filtrele
                if not self.is_meaningful_match(s1, s2, combined_score):
                    combined_score = 0.0

                if combined_score > best_score:
                    best_score = combined_score

            total_score += best_score
            comparisons += 1

        return total_score / comparisons

    def calculate_field_similarity(self, fields1, fields2):
        """Field isimlerinin benzerliği (Jaccard)"""
        if not fields1 or not fields2:
            return 0.0

        set1, set2 = set(fields1), set(fields2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def compare_with_mongodb(self, yaml_file_path, top_n=10):
        """YAML dosyasını MongoDB'deki kurallarla karşılaştır"""

        # YAML dosyasını oku
        print("📄 YAML dosyası okunuyor...")
        try:
            with open(yaml_file_path, "r", encoding='utf-8') as f:
                yaml_rule = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML dosyası bulunamadı: {yaml_file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML dosyası okunamadı: {e}")

        yaml_detection = yaml_rule.get("detection", {})
        yaml_fields, yaml_values = self.extract_detection_components(yaml_detection)

        print(f"🔍 YAML'dan çıkarılan:")
        print(f"   Fields: {yaml_fields}")
        print(f"   Values: {yaml_values}")
        print("-" * 60)

        # MongoDB'den tüm kuralları al
        print("🔍 MongoDB'den kurallar getiriliyor...")
        try:
            documents = list(self.collection.find())
            print(f"📊 Toplam {len(documents)} kural bulundu")
        except Exception as e:
            raise ConnectionError(f"MongoDB'den veri alınamadı: {e}")

        similarity_results = []

        for idx, doc in enumerate(documents, start=1):
            try:
                # MongoDB dokümanından detection bilgilerini çıkar
                mongo_detection = doc.get("detection", {})
                mongo_fields, mongo_values = self.extract_detection_components(mongo_detection)

                # Benzerlik hesapla
                field_sim = self.calculate_field_similarity(yaml_fields, mongo_fields)
                value_sim = self.fuzzy_similarity(yaml_values, mongo_values)

                # Ağırlıklı toplam (%80 value, %20 field)
                weighted_similarity = (value_sim * 0.8) + (field_sim * 0.2)

                similarity_results.append({
                    "index": idx,
                    "rule_id": str(doc.get("_id")),
                    "title": doc.get("title", "Untitled"),
                    "field_similarity": field_sim,
                    "value_similarity": value_sim,
                    "weighted_similarity": weighted_similarity,
                    "mongo_fields": mongo_fields,
                    "mongo_values": mongo_values
                })

            except Exception as e:
                logger.warning(f"Kural {idx} işlenirken hata: {e}")
                continue

        # En yüksek benzerliği sırala
        top_matches = sorted(similarity_results, key=lambda x: x['weighted_similarity'], reverse=True)[:top_n]

        print(f"\n🏆 EN BENZERLİK GÖSTEREN {top_n} KURAL:")
        print("=" * 80)

        for i, match in enumerate(top_matches, 1):
            print(f"\n{i}. 📋 {match['title']}")
            print(f"   🆔 Rule ID: {match['rule_id']}")
            print(f"   📊 TOPLAM BENZERLİK: {match['weighted_similarity']:.1%}")
            print(f"   🔤 Value Benzerliği:  {match['value_similarity']:.1%}")
            print(f"   🏷️  Field Benzerliği:  {match['field_similarity']:.1%}")

            # Detayları göster
            print(f"   🔍 MongoDB Fields: {match['mongo_fields']}")
            print(f"   🔍 MongoDB Values: {match['mongo_values'][:5]}...")

            # En iyi value eşleşmelerini göster
            if match['value_similarity'] > 0.4:  # Daha yüksek threshold
                print("   🎯 En İyi Value Eşleşmeleri:")
                for yaml_val in yaml_values[:3]:  # İlk 3 YAML value
                    best_match = ""
                    best_score = 0.0
                    for mongo_val in match['mongo_values']:
                        score = self.fuzzy_similarity([str(yaml_val)], [str(mongo_val)])
                        if score > best_score:
                            best_score = score
                            best_match = mongo_val

                    if best_score > 0.5:  # Daha yüksek threshold - sadece gerçekten iyi eşleşmeleri göster
                        print(f"      '{yaml_val}' ↔ '{best_match}' ({best_score:.1%})")

            print("-" * 60)

        return top_matches

# Kullanım
def main():
    try:
        # MongoDB bağlantı string'ini buraya girin
        mongo_connection = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
        connect_mongo = MongoConnector(mongo_connection, "sigmaDB", "rules")
        collect = connect_mongo.connect()

        # Comparator'ı başlat
        comparator = SigmaRuleComparator(collect)

        # YAML dosyasını karşılaştır
        results = comparator.compare_with_mongodb("deneme_kural.yml", top_n=10)

        # Özet istatistikler
        if results:
            print(f"\n📈 ÖZETİ:")
            print(f"   En yüksek benzerlik: {results[0]['weighted_similarity']:.1%}")
            print(f"   En düşük (top 10): {results[-1]['weighted_similarity']:.1%}")
            print(f"   Ortalama benzerlik: {sum(r['weighted_similarity'] for r in results) / len(results):.1%}")
        else:
            print("❌ Hiç benzer kural bulunamadı!")

        # Bağlantıyı kapat
        connect_mongo.close_connection()

    except FileNotFoundError:
        print("❌ 'deneme_kural.yml' dosyası bulunamadı!")
    except ConnectionError as e:
        print(f"❌ MongoDB bağlantı hatası: {e}")
    except Exception as e:
        print(f"❌ Beklenmeyen hata oluştu: {e}")
        logger.exception("Detaylı hata bilgisi:")

if __name__ == "__main__":
    main()