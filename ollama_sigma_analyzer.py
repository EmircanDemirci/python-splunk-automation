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

class OllamaSigmaAnalyzer:
    def __init__(self, ollama_url="http://localhost:11434", model_name="llama3.1"):
        """
        Ollama AI ile Sigma kural analizi
        
        Args:
            ollama_url (str): Ollama API URL'i
            model_name (str): Kullanılacak AI model (llama3.1, mistral, codellama vb.)
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.api_endpoint = f"{ollama_url}/api/generate"
        
    def test_ollama_connection(self):
        """Ollama bağlantısını test et"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                logger.info(f"✅ Ollama bağlantısı başarılı. Mevcut modeller: {available_models}")
                
                if self.model_name not in available_models:
                    logger.warning(f"⚠️ Model '{self.model_name}' bulunamadı. İlk model kullanılacak: {available_models[0] if available_models else 'Hiç model yok'}")
                    if available_models:
                        self.model_name = available_models[0]
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ollama bağlantı hatası: {e}")
            return False

    def generate_rule_summary(self, sigma_rule: Dict[str, Any]) -> str:
        """
        Sigma kuralının AI destekli özetini oluştur
        
        Args:
            sigma_rule (dict): Sigma rule dictionary
            
        Returns:
            str: AI tarafından oluşturulan özet
        """
        
        # Sigma kuralını anlaşılır formatta hazırla
        rule_text = self._format_rule_for_ai(sigma_rule)
        
        prompt = f"""
Aşağıdaki Sigma güvenlik kuralını analiz et ve kısa, öz bir açıklama yap. 
Kuralın ne tespit ettiğini, hangi saldırı türünü yakaladığını ve önemli anahtar kelimelerini belirt.
Maksimum 2-3 cümle kullan, teknik detaylara girme:

SIGMA KURAL:
{rule_text}

AÇIKLAMA:
"""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Daha tutarlı sonuçlar için düşük
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                logger.info(f"✅ AI özet oluşturuldu: {summary[:100]}...")
                return summary
            else:
                logger.error(f"❌ Ollama API hatası: {response.status_code}")
                return self._fallback_summary(sigma_rule)
                
        except Exception as e:
            logger.error(f"❌ AI özet hatası: {e}")
            return self._fallback_summary(sigma_rule)

    def find_similar_rules(self, target_rule: Dict[str, Any], all_rules: List[Dict[str, Any]], 
                          threshold: float = 0.7, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        AI destekli benzerlik analizi ile benzer kuralları bul
        
        Args:
            target_rule (dict): Hedef Sigma kuralı
            all_rules (list): Tüm kurallar listesi
            threshold (float): Benzerlik eşiği (0-1)
            max_results (int): Maksimum sonuç sayısı
            
        Returns:
            list: Benzer kurallar listesi
        """
        
        target_summary = self.generate_rule_summary(target_rule)
        target_text = self._format_rule_for_ai(target_rule)
        
        similar_rules = []
        
        logger.info(f"🔍 {len(all_rules)} kural arasında benzerlik analizi başlatılıyor...")
        
        for idx, rule in enumerate(all_rules, 1):
            if idx % 10 == 0:
                logger.info(f"📊 İşlenen: {idx}/{len(all_rules)}")
            
            # Aynı kuralı karşılaştırmayı atla
            if rule.get('_id') == target_rule.get('_id'):
                continue
                
            try:
                similarity_score = self._calculate_ai_similarity(target_text, target_summary, rule)
                
                if similarity_score >= threshold:
                    similar_rules.append({
                        'rule': rule,
                        'similarity_score': similarity_score,
                        'ai_summary': self.generate_rule_summary(rule)
                    })
                    
                # Rate limiting - Ollama'yı yormamak için
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ Kural {idx} analiz hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala
        similar_rules.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"✅ {len(similar_rules)} benzer kural bulundu")
        return similar_rules[:max_results]

    def _calculate_ai_similarity(self, target_text: str, target_summary: str, 
                                compare_rule: Dict[str, Any]) -> float:
        """
        AI ile iki Sigma kuralı arasındaki benzerliği hesapla
        
        Args:
            target_text (str): Hedef kuralın metni
            target_summary (str): Hedef kuralın AI özeti
            compare_rule (dict): Karşılaştırılacak kural
            
        Returns:
            float: Benzerlik skoru (0-1)
        """
        
        compare_text = self._format_rule_for_ai(compare_rule)
        
        prompt = f"""
İki Sigma güvenlik kuralını karşılaştır ve 0.0 ile 1.0 arasında benzerlik skoru ver.
1.0 = neredeyse aynı işlevi yapıyor
0.8-0.9 = çok benzer saldırı türlerini tespit ediyor  
0.6-0.7 = benzer güvenlik alanında ama farklı teknikler
0.3-0.5 = aynı kategori ama farklı yaklaşım
0.0-0.2 = tamamen farklı

HEDEF KURAL ÖZETİ:
{target_summary}

HEDEF KURAL:
{target_text[:1000]}

KARŞILAŞTIRILAN KURAL:
{compare_text[:1000]}

Sadece sayısal skor ver (örnek: 0.85):
"""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Çok düşük - tutarlı skorlar için
                        "max_tokens": 10
                    }
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                score_text = result.get('response', '0.0').strip()
                
                # Sayısal skoru çıkar
                import re
                score_match = re.search(r'(\d+\.?\d*)', score_text)
                if score_match:
                    score = float(score_match.group(1))
                    return min(1.0, max(0.0, score))  # 0-1 arasında sınırla
                    
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ AI benzerlik hesaplama hatası: {e}")
            return 0.0

    def _format_rule_for_ai(self, rule: Dict[str, Any]) -> str:
        """Sigma kuralını AI için uygun formata çevir"""
        
        # Ana alanları çıkar
        formatted = []
        
        if 'title' in rule:
            formatted.append(f"Title: {rule['title']}")
        if 'description' in rule:
            formatted.append(f"Description: {rule['description']}")
        if 'author' in rule:
            formatted.append(f"Author: {rule['author']}")
        if 'tags' in rule:
            formatted.append(f"Tags: {', '.join(rule['tags']) if isinstance(rule['tags'], list) else rule['tags']}")
        
        # Detection bölümü
        if 'detection' in rule:
            formatted.append("Detection:")
            detection_str = yaml.dump(rule['detection'], default_flow_style=False)
            formatted.append(detection_str)
            
        return "\n".join(formatted)

    def _fallback_summary(self, rule: Dict[str, Any]) -> str:
        """AI başarısız olursa manuel özet oluştur"""
        title = rule.get('title', 'Unknown Rule')
        description = rule.get('description', '')
        tags = rule.get('tags', [])
        
        if isinstance(tags, list):
            tags_str = ', '.join(tags[:3])  # İlk 3 tag
        else:
            tags_str = str(tags)
            
        return f"{title}. {description[:100]}... Tags: {tags_str}"

class MongoSigmaManager:
    def __init__(self, connection_string: str, database_name: str, collection_name: str):
        """
        MongoDB Sigma kural yöneticisi
        
        Args:
            connection_string (str): MongoDB bağlantı string'i
            database_name (str): Veritabanı adı
            collection_name (str): Koleksiyon adı
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None

    def connect(self):
        """MongoDB'ye bağlan"""
        try:
            self.client = MongoClient(self.connection_string)
            self.client.admin.command('ping')
            self.collection = self.client[self.database_name][self.collection_name]
            logger.info("✅ MongoDB bağlantısı başarılı")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB bağlantı hatası: {e}")
            return False

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Tüm Sigma kurallarını getir"""
        try:
            rules = list(self.collection.find())
            logger.info(f"📊 {len(rules)} Sigma kuralı getirildi")
            return rules
        except Exception as e:
            logger.error(f"❌ Kurallar getirme hatası: {e}")
            return []

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """ID ile kural getir"""
        try:
            from bson import ObjectId
            rule = self.collection.find_one({"_id": ObjectId(rule_id)})
            if rule:
                logger.info(f"✅ Kural bulundu: {rule.get('title', 'No title')}")
            return rule
        except Exception as e:
            logger.error(f"❌ Kural getirme hatası: {e}")
            return None

    def close(self):
        """Bağlantıyı kapat"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB bağlantısı kapatıldı")

def main():
    """Ana fonksiyon - örnek kullanım"""
    
    # Konfigürasyon
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    DATABASE_NAME = "sigmaDB"
    COLLECTION_NAME = "rules"
    OLLAMA_URL = "http://localhost:11434"
    MODEL_NAME = "llama3.1"  # veya "mistral", "codellama"
    
    # MongoDB bağlantısı
    mongo_manager = MongoSigmaManager(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)
    if not mongo_manager.connect():
        return
    
    # Ollama AI analyzer
    ai_analyzer = OllamaSigmaAnalyzer(OLLAMA_URL, MODEL_NAME)
    if not ai_analyzer.test_ollama_connection():
        print("❌ Ollama bağlantısı kurulamadı. Lütfen Ollama'nın çalıştığından emin olun.")
        return
    
    try:
        # Tüm kuralları getir
        all_rules = mongo_manager.get_all_rules()
        if not all_rules:
            print("❌ Hiç kural bulunamadı!")
            return
        
        # İlk kuralı hedef olarak al (örnek)
        target_rule = all_rules[0]
        print(f"🎯 Hedef kural: {target_rule.get('title', 'No title')}")
        
        # AI ile benzer kuralları bul
        print("🤖 AI ile benzerlik analizi başlatılıyor...")
        similar_rules = ai_analyzer.find_similar_rules(
            target_rule=target_rule,
            all_rules=all_rules[1:],  # Hedef hariç diğerleri
            threshold=0.6,
            max_results=5
        )
        
        # Sonuçları göster
        print("\n🏆 BENZER KURALLAR:")
        print("=" * 80)
        
        for i, result in enumerate(similar_rules, 1):
            rule = result['rule']
            score = result['similarity_score']
            summary = result['ai_summary']
            
            print(f"\n{i}. 📋 {rule.get('title', 'No title')}")
            print(f"   🆔 Rule ID: {rule.get('_id')}")
            print(f"   🎯 Benzerlik Skoru: {score:.1%}")
            print(f"   🤖 AI Özeti: {summary}")
            print(f"   🏷️ Tags: {rule.get('tags', [])}")
            print("-" * 60)
        
        if not similar_rules:
            print("❌ Benzer kural bulunamadı!")
    
    except KeyboardInterrupt:
        print("\n⏹️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"❌ Ana işlem hatası: {e}")
    finally:
        mongo_manager.close()

if __name__ == "__main__":
    main()