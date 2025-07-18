import yaml
import pymongo
import re
import json
from difflib import SequenceMatcher
from collections import Counter
from mongodb_connection import MongoConnector
import logging
import requests
import time
from typing import List, Dict, Any, Optional

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSigmaRuleComparator:
    def __init__(self, collection, ollama_url="http://localhost:11434", model_name="deepseek-r1:8b"):
        self.collection = collection
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.api_endpoint = f"{ollama_url}/api/generate"
        
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
        
    def clean_field(self, field):
        """Field isimlerinden gereksiz Sigma yapılarını temizle"""
        if not isinstance(field, str):
            return str(field)
        
        # Temizlenecek field prefixleri ve suffixleri
        field_patterns_to_remove = [
            # Sigma detection yapıları
            'selection', 'filter', 'condition', 'timeframe',
            # Selection varyantları  
            'selection_', 'sel_', 'select_',
            # Filter varyantları
            'filter_', 'filt_', 'exclude_',
            # Diğer yaygın Sigma yapıları
            'keywords', 'keyword_', 'pattern_', 'rule_',
            'detection_', 'detect_', 'match_', 'search_',
            # Suffix'ler için
            '_selection', '_filter', '_condition', '_rule'
        ]
        
        cleaned_field = field.lower().strip()
        
        # Önce sayısal suffix'leri kaldır (selection1, filter2 gibi)
        cleaned_field = re.sub(r'_?\d+$', '', cleaned_field)
        
        # Prefix'leri kaldır
        for pattern in field_patterns_to_remove:
            if pattern.endswith('_'):  # Prefix pattern
                if cleaned_field.startswith(pattern):
                    cleaned_field = cleaned_field[len(pattern):]
                    break  # İlk eşleşmede dur
            elif pattern.startswith('_'):  # Suffix pattern  
                if cleaned_field.endswith(pattern):
                    cleaned_field = cleaned_field[:-len(pattern)]
                    break  # İlk eşleşmede dur
            else:  # Tam eşleşme
                if cleaned_field == pattern:
                    return ""  # Tamamen gereksiz field, boş döndür
        
        # Pipe characters ve modifiers'ı temizle (Image|endswith → image)
        if '|' in cleaned_field:
            cleaned_field = cleaned_field.split('|')[0]
        
        # Wildcard ve regex karakterlerini temizle
        cleaned_field = re.sub(r'[\*\?\[\]{}()^$|\\]', '', cleaned_field)
        
        # Birden fazla underscore'u tek underscore'a çevir
        cleaned_field = re.sub(r'_+', '_', cleaned_field)
        
        # Başındaki ve sonundaki underscore'ları kaldır
        cleaned_field = cleaned_field.strip('_')
        
        return cleaned_field if cleaned_field else field  # Eğer tamamen boş kaldıysa orijinalini döndür
        
    def extract_detection_components(self, detection_dict):
        """Detection bölümünden field'ları ve değerleri ayrı ayrı çıkar"""
        fields = set()
        values = []

        def recursive_extract(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'condition':  # condition'ı skip et
                        continue

                    # Field ismini temizle ve ekle
                    cleaned_field = self.clean_field(key)
                    if cleaned_field:  # Boş değilse ekle
                        fields.add(cleaned_field)

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
            # Tek karakterli stringler için özel kurallar
            if min_length == 1:
                # Tek karakter sadece kendisiyle tam eşleşirse kabul edilir
                return s1_clean == s2_clean
            
            # 2 karakterli stringler için
            if min_length == 2:
                # Baştan eşleşme varsa ve score yüksekse kabul et
                if s1_clean.startswith(s2_clean) or s2_clean.startswith(s1_clean):
                    return score > 0.8  # Çok yüksek threshold
                # Tam eşleşme dışında kabul etme
                return s1_clean == s2_clean
            
            # Kısa string uzun stringin içindeyse ve baştan eşleşmiyorsa suspicious
            if max_length > 5:
                return False
            # İkisi de çok kısaysa sadece tam eşleşmeyi kabul et
            return s1_clean == s2_clean
            
        # Length ratio kontrolü - çok farklı uzunluklardaysa skip et
        length_ratio = min_length / max_length if max_length > 0 else 0
        if length_ratio < 0.4:  # Biri diğerinin %40'ından kısaysa
            return False
            
        # Kısa substring eşleşmelerini filtrele (3-5 karakter)
        if min_length <= 5 and min_length >= 3:
            # Baştan eşleşme varsa kabul et (daha gevşek kontrol)
            if s1_clean.startswith(s2_clean) or s2_clean.startswith(s1_clean):
                return score > 0.6  # Baştan eşleşmelerde makul threshold
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

                # Akıllı substring bonus - sadece anlamlı durumlarda ver
                substring_bonus = 0.0
                if s1_clean in s2_clean or s2_clean in s1_clean:
                    min_len = min(len(s1_clean), len(s2_clean))
                    max_len = max(len(s1_clean), len(s2_clean))
                    
                    # Sadece uzunluk oranı makul ise bonus ver
                    length_ratio = min_len / max_len if max_len > 0 else 0
                    if length_ratio >= 0.5:  # En az %50 uzunluk oranı olmalı
                        substring_bonus = 0.1  # Daha düşük bonus
                    elif length_ratio >= 0.3:  # Orta seviye
                        substring_bonus = 0.05  # Çok düşük bonus

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

    def query_ollama(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Ollama API'yi sorgula"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                }
                
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    timeout=60,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.warning(f"Ollama API hatası (Status {response.status_code}): {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Ollama sorgusu zaman aşımına uğradı (Deneme {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Ollama sorgusu hatası (Deneme {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

    def create_analysis_prompt(self, yaml_rule: Dict, similar_rules: List[Dict]) -> str:
        """Ollama için analiz prompt'u oluştur"""
        
        # YAML kuralının temel bilgilerini çıkar
        yaml_title = yaml_rule.get('title', 'Untitled')
        yaml_description = yaml_rule.get('description', 'No description')
        yaml_detection = yaml_rule.get('detection', {})
        
        prompt = f"""
Cyber Security Expert olarak, aşağıdaki Sigma kuralını analiz etmenizi ve en benzer kuralları değerlendirmenizi istiyorum.

## ANALİZ EDİLECEK KURAL:
**Başlık:** {yaml_title}
**Açıklama:** {yaml_description}
**Detection Bölümü:** {json.dumps(yaml_detection, indent=2)}

## VERİTABANINDAKİ EN BENZER KURALLAR:
"""
        
        for i, rule in enumerate(similar_rules[:5], 1):  # İlk 5 kuralı analiz et
            prompt += f"""
### {i}. BENZER KURAL (Benzerlik: {rule['weighted_similarity']:.1%})
**ID:** {rule['rule_id']}
**Başlık:** {rule['title']}
**Field Benzerliği:** {rule['field_similarity']:.1%}
**Value Benzerliği:** {rule['value_similarity']:.1%}
**MongoDB Fields:** {rule['mongo_fields']}
**MongoDB Values:** {rule['mongo_values'][:10]}  # İlk 10 value
---
"""

        prompt += """
## LÜTFEN ŞUNLARI ANALİZ EDİN:

1. **EN BENZERİ:** Hangi kural gerçekten en benzer ve neden?

2. **BENZERLIK TİPLERİ:** 
   - Aynı saldırı türünü mü tespit ediyorlar?
   - Aynı log kaynaklarını mı kullanıyorlar?
   - Benzer IOC'ler (Indicators of Compromise) var mı?

3. **FARKLILIKLARI:**
   - Hangi önemli farklılıklar var?
   - Birbirini tamamlayıcı özellikler var mı?

4. **ÖNERİLER:**
   - Bu kurallar birleştirilebilir mi?
   - Hangi kural daha kapsamlı/etkili?
   - Yeni kuralın avantajları neler?

5. **SONUÇ:** En benzer kuralın ID'si ve bu seçimin gerekçesi.

Lütfen teknik detaylarla, siber güvenlik perspektifinden profesyonel bir analiz yapın.
"""
        
        return prompt

    def analyze_with_ollama(self, yaml_rule: Dict, similar_rules: List[Dict]) -> Dict[str, Any]:
        """Ollama ile benzer kuralları analiz et"""
        
        if not self.test_ollama_connection():
            logger.error("❌ Ollama bağlantısı başarısız, AI analizi yapılamıyor")
            return {
                "success": False,
                "error": "Ollama bağlantısı başarısız",
                "analysis": None
            }
        
        if not similar_rules:
            return {
                "success": False,
                "error": "Analiz edilecek benzer kural bulunamadı",
                "analysis": None
            }
        
        print("🤖 Ollama AI ile analiz başlatılıyor...")
        
        # Analiz prompt'unu oluştur
        prompt = self.create_analysis_prompt(yaml_rule, similar_rules)
        
        # Ollama'ya sor
        analysis_result = self.query_ollama(prompt)
        
        if analysis_result:
            return {
                "success": True,
                "analysis": analysis_result,
                "analyzed_rules_count": len(similar_rules[:5]),
                "prompt_used": prompt
            }
        else:
            return {
                "success": False,
                "error": "Ollama'dan yanıt alınamadı",
                "analysis": None
            }

    def compare_with_mongodb_and_analyze(self, yaml_file_path: str, top_n: int = 10) -> Dict[str, Any]:
        """YAML dosyasını MongoDB'deki kurallarla karşılaştır ve Ollama ile analiz et"""

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
                    "mongo_values": mongo_values,
                    "full_rule": doc  # Tam kuralı da sakla
                })

            except Exception as e:
                logger.warning(f"Kural {idx} işlenirken hata: {e}")
                continue
        
        # Benzerlik filtreleme
        filtered = [m for m in similarity_results if m['weighted_similarity'] >= 0.5]
        if not filtered:
            top_matches = []
        else:
            # En yüksek benzerlikten başlayarak top_n kadar al
            top_matches = sorted(filtered, key=lambda x: x['weighted_similarity'], reverse=True)[:top_n]

        # Geleneksel sonuçları yazdır
        print(f"\n🏆 EN BENZERLİK GÖSTEREN {len(top_matches)} KURAL:")
        print("=" * 80)

        for i, match in enumerate(top_matches, 1):
            print(f"\n{i}. 📋 {match['title']}")
            print(f"   🆔 Rule ID: {match['rule_id']}")
            print(f"   📊 TOPLAM BENZERLİK: {match['weighted_similarity']:.1%}")
            print(f"   🔤 Value Benzerliği:  {match['value_similarity']:.1%}")
            print(f"   🏷️  Field Benzerliği:  {match['field_similarity']:.1%}")

        # Ollama AI analizi
        ai_analysis = self.analyze_with_ollama(yaml_rule, top_matches)
        
        # AI analiz sonuçlarını yazdır
        if ai_analysis["success"]:
            print("\n" + "=" * 80)
            print("🤖 OLLAMA AI ANALİZ SONUÇLARI:")
            print("=" * 80)
            print(ai_analysis["analysis"])
            print("=" * 80)
        else:
            print(f"\n❌ AI analizi başarısız: {ai_analysis['error']}")

        # Kapsamlı sonuç döndür
        return {
            "yaml_rule": yaml_rule,
            "yaml_fields": yaml_fields,
            "yaml_values": yaml_values,
            "top_matches": top_matches,
            "ai_analysis": ai_analysis,
            "total_rules_analyzed": len(documents),
            "similar_rules_found": len(filtered)
        }

def main():
    try:
        # MongoDB bağlantı string'ini buraya girin
        mongo_connection = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
        connect_mongo = MongoConnector(mongo_connection, "sigmaDB", "rules")
        collect = connect_mongo.connect()

        # Enhanced Comparator'ı başlat
        comparator = EnhancedSigmaRuleComparator(collect)

        # YAML dosyasını karşılaştır ve AI ile analiz et
        results = comparator.compare_with_mongodb_and_analyze("deneme_kural.yml", top_n=10)

        # Özet istatistikler
        if results["top_matches"]:
            print(f"\n📈 ÖZET İSTATİSTİKLER:")
            print(f"   📁 Toplam veritabanı kuralı: {results['total_rules_analyzed']}")
            print(f"   ✅ Benzer kural sayısı (>50%): {results['similar_rules_found']}")
            print(f"   🏆 En yüksek benzerlik: {results['top_matches'][0]['weighted_similarity']:.1%}")
            print(f"   📊 Analiz edilen top kural: {len(results['top_matches'])}")
            print(f"   🤖 AI analizi: {'✅ Başarılı' if results['ai_analysis']['success'] else '❌ Başarısız'}")
            
            if results['ai_analysis']['success']:
                print(f"   🔍 AI tarafından analiz edilen kural sayısı: {results['ai_analysis']['analyzed_rules_count']}")
        else:
            print("❌ Hiç benzer kural bulunamadı!")

    except FileNotFoundError:
        print("❌ 'deneme_kural.yml' dosyası bulunamadı!")
    except ConnectionError as e:
        print(f"❌ MongoDB bağlantı hatası: {e}")
    except Exception as e:
        print(f"❌ Beklenmeyen hata oluştu: {e}")
        logger.exception("Detaylı hata bilgisi:")

if __name__ == "__main__":
    main()