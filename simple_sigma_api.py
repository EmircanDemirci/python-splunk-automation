from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import yaml
import logging
from simple_sigma_comparator import SimpleSigmaComparator

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Simple SigmaHQ Similarity API",
    description="Hızlı ve basit Sigma kuralı benzerlik analizi - sadece ilk benzer kuralı bulur",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic modelleri
class SimpleSigmaRequest(BaseModel):
    sigma_rule: Dict[str, Any]  # YAML olarak parse edilmiş Sigma kuralı
    threshold: float = 0.4      # Minimum benzerlik eşiği

class SigmaRuleYAMLRequest(BaseModel):
    sigma_yaml: str             # YAML string olarak Sigma kuralı
    threshold: float = 0.4

class SimilarRuleResult(BaseModel):
    rule_id: str
    title: str
    description: str
    similarity_score: float
    similarity_percentage: int
    tags: list
    level: str
    author: str
    date: str
    explanation: str

class SimpleResponse(BaseModel):
    success: bool
    input_rule_title: str
    input_rule_description: str
    similar_rule: Optional[SimilarRuleResult]
    processing_time_seconds: float
    threshold_used: float
    message: str

class HealthResponse(BaseModel):
    status: str
    mongodb_connected: bool
    sigmahq_rules_count: int
    version: str

# Global konfigürasyon
MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
DATABASE_NAME = "sigmaDB"
COLLECTION_NAME = "rules"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basit sistem sağlık kontrolü"""
    
    # Test comparator oluştur
    comparator = SimpleSigmaComparator(MONGO_CONNECTION)
    
    # MongoDB kontrolü ve kural sayısı
    mongodb_connected = comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME)
    rules_count = 0
    
    if mongodb_connected:
        try:
            rules_count = comparator.collection.count_documents({})
        except:
            rules_count = 0
        comparator.close_connection()
    
    return HealthResponse(
        status="healthy" if mongodb_connected else "error",
        mongodb_connected=mongodb_connected,
        sigmahq_rules_count=rules_count,
        version="2.0.0-simple"
    )

@app.post("/find-similar", response_model=SimpleResponse)
async def find_similar_rule(request: SimpleSigmaRequest):
    """
    Tek Sigma kuralını analiz et ve ilk benzer SigmaHQ kuralını bul (hızlı)
    """
    
    import time
    start_time = time.time()
    
    # Comparator'ı başlat
    comparator = SimpleSigmaComparator(MONGO_CONNECTION)
    
    # Bağlantıyı kontrol et
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        # Input kuralını doğrula
        input_rule = request.sigma_rule
        if not input_rule or 'detection' not in input_rule:
            raise HTTPException(status_code=400, detail="Geçersiz Sigma kuralı - 'detection' bölümü gerekli")
        
        # İlk benzer kuralı bul
        similar_rule = comparator.find_first_similar_rule(
            input_rule=input_rule,
            threshold=request.threshold
        )
        
        processing_time = time.time() - start_time
        
        # Sonucu formatla
        result = None
        message = "Benzer kural bulunamadı"
        
        if similar_rule:
                         # Detection odaklı açıklama
            score = similar_rule['similarity_score']
            
            # Field ve value benzerliğini analiz et
            input_fields = comparator.extract_field_names(input_rule.get('detection', {}))
            sigmahq_fields = comparator.extract_field_names(similar_rule['rule'].get('detection', {}))
            common_fields = input_fields.intersection(sigmahq_fields)
            
            input_values = comparator.extract_detection_values(input_rule.get('detection', {}))
            sigmahq_values = comparator.extract_detection_values(similar_rule['rule'].get('detection', {}))
            common_values = input_values.intersection(sigmahq_values)
            
            explanation_parts = []
            
            if score > 0.8:
                explanation_parts.append("Çok yüksek detection benzerliği")
            elif score > 0.6:
                explanation_parts.append("Yüksek detection benzerliği")
            elif score > 0.4:
                explanation_parts.append("Orta detection benzerliği")
            else:
                explanation_parts.append("Düşük detection benzerliği")
            
            if common_fields:
                explanation_parts.append(f"Ortak field: {', '.join(list(common_fields)[:2])}")
            
            if common_values:
                explanation_parts.append(f"Ortak değer: {', '.join(list(common_values)[:1])}")
            
            explanation = " - ".join(explanation_parts)
            
            result = SimilarRuleResult(
                rule_id=similar_rule['rule_id'],
                title=similar_rule['title'],
                description=similar_rule['description'],
                similarity_score=similar_rule['similarity_score'],
                similarity_percentage=int(similar_rule['similarity_score'] * 100),
                tags=similar_rule['tags'] if isinstance(similar_rule['tags'], list) else [],
                level=similar_rule['level'],
                author=similar_rule['author'],
                date=similar_rule['date'],
                explanation=explanation
            )
            message = "Benzer kural bulundu"
        
        return SimpleResponse(
            success=True,
            input_rule_title=input_rule.get('title', 'No title'),
            input_rule_description=input_rule.get('description', 'No description'),
            similar_rule=result,
            processing_time_seconds=round(processing_time, 2),
            threshold_used=request.threshold,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analiz hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
    finally:
        comparator.close_connection()

@app.post("/find-similar-yaml", response_model=SimpleResponse)
async def find_similar_yaml(request: SigmaRuleYAMLRequest):
    """
    YAML string olarak Sigma kuralını analiz et (hızlı)
    """
    
    try:
        # YAML'ı parse et
        sigma_rule = yaml.safe_load(request.sigma_yaml)
        
        # Dict formatına çevir ve normal endpoint'e yönlendir
        converted_request = SimpleSigmaRequest(
            sigma_rule=sigma_rule,
            threshold=request.threshold
        )
        
        return await find_similar_rule(converted_request)
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parse hatası: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")

@app.get("/stats")
async def get_quick_stats():
    """Hızlı istatistikler"""
    
    comparator = SimpleSigmaComparator(MONGO_CONNECTION)
    
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        # Sadece toplam sayı (hızlı)
        total_rules = comparator.collection.count_documents({})
        
        return {
            "success": True,
            "total_sigmahq_rules": total_rules,
            "api_version": "2.0.0-simple",
            "features": [
                "Hızlı string benzerlik analizi",
                "İlk benzer kuralı bul ve dur",
                "MITRE tag filtreleme",
                "AI yok - sadece algoritma"
            ]
        }
        
    except Exception as e:
        logger.error(f"İstatistik hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İstatistik hatası: {str(e)}")
    finally:
        comparator.close_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Farklı port