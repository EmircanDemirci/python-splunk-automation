from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import yaml
import logging
from single_sigma_comparator import SigmaHQComparator

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SigmaHQ Similarity API",
    description="Tek Sigma kuralı ile SigmaHQ kuralları arasında AI destekli benzerlik analizi",
    version="1.0.0"
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
class SingleSigmaRequest(BaseModel):
    sigma_rule: Dict[str, Any]  # YAML olarak parse edilmiş Sigma kuralı
    threshold: float = 0.3      # Minimum benzerlik eşiği
    max_results: int = 10       # Maksimum sonuç sayısı
    ollama_url: str = "http://localhost:11434"
    model_name: str = "llama3.1"

class SigmaRuleYAMLRequest(BaseModel):
    sigma_yaml: str             # YAML string olarak Sigma kuralı
    threshold: float = 0.3
    max_results: int = 10
    ollama_url: str = "http://localhost:11434"
    model_name: str = "llama3.1"

class SimilarityResult(BaseModel):
    rule_id: str
    title: str
    description: str
    similarity_score: float
    similarity_percentage: int
    tags: List[str]
    level: str
    author: str
    date: str
    ai_summary: str

class SigmaHQResponse(BaseModel):
    success: bool
    input_rule_title: str
    input_rule_description: str
    similar_rules: List[SimilarityResult]
    total_analyzed: int
    processing_time_seconds: float
    ai_model_used: str
    threshold_used: float

class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    mongodb_connected: bool
    available_models: List[str]
    sigmahq_rules_count: int

# Global konfigürasyon
MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
DATABASE_NAME = "sigmaDB"
COLLECTION_NAME = "rules"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Sistem sağlık kontrolü"""
    
    # Test comparator oluştur
    comparator = SigmaHQComparator(MONGO_CONNECTION)
    
    # Ollama kontrolü
    ollama_connected = comparator.test_ollama_connection()
    
    # MongoDB kontrolü ve kural sayısı
    mongodb_connected = comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME)
    rules_count = 0
    
    if mongodb_connected:
        try:
            rules_count = comparator.collection.count_documents({})
        except:
            rules_count = 0
        comparator.close_connection()
    
    # Mevcut modelleri al
    available_models = []
    if ollama_connected:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
        except:
            pass
    
    return HealthResponse(
        status="healthy" if (mongodb_connected and ollama_connected) else "partial",
        ollama_connected=ollama_connected,
        mongodb_connected=mongodb_connected,
        available_models=available_models,
        sigmahq_rules_count=rules_count
    )

@app.post("/analyze-sigma", response_model=SigmaHQResponse)
async def analyze_sigma_rule(request: SingleSigmaRequest):
    """
    Tek Sigma kuralını analiz et ve SigmaHQ'dan benzer kuralları bul
    """
    
    import time
    start_time = time.time()
    
    # Comparator'ı başlat
    comparator = SigmaHQComparator(
        request.ollama_url if hasattr(request, 'ollama_url') else MONGO_CONNECTION,
        request.ollama_url,
        request.model_name
    )
    
    # Bağlantıları kontrol et
    if not comparator.test_ollama_connection():
        raise HTTPException(status_code=500, detail="Ollama AI bağlantısı kurulamadı")
    
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        # Input kuralını doğrula
        input_rule = request.sigma_rule
        if not input_rule or 'detection' not in input_rule:
            raise HTTPException(status_code=400, detail="Geçersiz Sigma kuralı - 'detection' bölümü gerekli")
        
        # SigmaHQ kuralları ile karşılaştır
        similar_rules = comparator.find_most_similar_rules(
            input_rule=input_rule,
            threshold=request.threshold,
            max_results=request.max_results
        )
        
        # Sonuçları formatla
        formatted_results = []
        for result in similar_rules:
            formatted_results.append(SimilarityResult(
                rule_id=result['rule_id'],
                title=result['title'],
                description=result['description'],
                similarity_score=result['similarity_score'],
                similarity_percentage=int(result['similarity_score'] * 100),
                tags=result['tags'] if isinstance(result['tags'], list) else [],
                level=result['level'],
                author=result['author'],
                date=result['date'],
                ai_summary=result.get('ai_summary', 'AI özet oluşturulamadı')
            ))
        
        processing_time = time.time() - start_time
        
        return SigmaHQResponse(
            success=True,
            input_rule_title=input_rule.get('title', 'No title'),
            input_rule_description=input_rule.get('description', 'No description'),
            similar_rules=formatted_results,
            total_analyzed=comparator.collection.count_documents({}) if comparator.collection else 0,
            processing_time_seconds=round(processing_time, 2),
            ai_model_used=request.model_name,
            threshold_used=request.threshold
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analiz hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
    finally:
        comparator.close_connection()

@app.post("/analyze-sigma-yaml", response_model=SigmaHQResponse)
async def analyze_sigma_yaml(request: SigmaRuleYAMLRequest):
    """
    YAML string olarak Sigma kuralını analiz et
    """
    
    try:
        # YAML'ı parse et
        sigma_rule = yaml.safe_load(request.sigma_yaml)
        
        # Dict formatına çevir ve normal endpoint'e yönlendir
        converted_request = SingleSigmaRequest(
            sigma_rule=sigma_rule,
            threshold=request.threshold,
            max_results=request.max_results,
            ollama_url=request.ollama_url,
            model_name=request.model_name
        )
        
        return await analyze_sigma_rule(converted_request)
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parse hatası: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")

@app.get("/sigmahq-stats")
async def get_sigmahq_stats():
    """SigmaHQ kuralları hakkında istatistikler"""
    
    comparator = SigmaHQComparator(MONGO_CONNECTION)
    
    if not comparator.connect_mongodb(DATABASE_NAME, COLLECTION_NAME):
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        # Toplam kural sayısı
        total_rules = comparator.collection.count_documents({})
        
        # Level dağılımı
        level_stats = list(comparator.collection.aggregate([
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Tag dağılımı (top 10)
        tag_stats = list(comparator.collection.aggregate([
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))
        
        # Author dağılımı (top 10)
        author_stats = list(comparator.collection.aggregate([
            {"$group": {"_id": "$author", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))
        
        return {
            "success": True,
            "total_rules": total_rules,
            "level_distribution": {item['_id']: item['count'] for item in level_stats},
            "top_tags": {item['_id']: item['count'] for item in tag_stats},
            "top_authors": {item['_id']: item['count'] for item in author_stats}
        }
        
    except Exception as e:
        logger.error(f"İstatistik hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İstatistik hatası: {str(e)}")
    finally:
        comparator.close_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)