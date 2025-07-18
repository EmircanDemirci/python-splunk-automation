from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from ollama_sigma_analyzer import OllamaSigmaAnalyzer, MongoSigmaManager

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ollama Sigma Similarity API",
    description="N8N entegrasyonu için Ollama AI destekli Sigma kural benzerlik API'si",
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
class SimilarityRequest(BaseModel):
    rule_id: Optional[str] = None
    rule_content: Optional[Dict[str, Any]] = None
    threshold: float = 0.7
    max_results: int = 5
    ollama_url: str = "http://localhost:11434"
    model_name: str = "llama3.1"

class SimilarityResponse(BaseModel):
    success: bool
    target_rule_title: str
    target_rule_id: Optional[str]
    similar_rules: List[Dict[str, Any]]
    total_rules_analyzed: int
    processing_time_seconds: float
    ai_model_used: str

class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    mongodb_connected: bool
    available_models: List[str]

# Global konfigürasyon
MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
DATABASE_NAME = "sigmaDB"
COLLECTION_NAME = "rules"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Sistem sağlık kontrolü - N8N için"""
    
    # MongoDB kontrolü
    mongo_manager = MongoSigmaManager(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)
    mongodb_connected = mongo_manager.connect()
    if mongodb_connected:
        mongo_manager.close()
    
    # Ollama kontrolü
    ai_analyzer = OllamaSigmaAnalyzer()
    ollama_connected = ai_analyzer.test_ollama_connection()
    
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
        available_models=available_models
    )

@app.post("/find-similar", response_model=SimilarityResponse)
async def find_similar_rules(request: SimilarityRequest):
    """
    N8N için benzer Sigma kurallarını bul
    
    İki kullanım şekli:
    1. rule_id ile: MongoDB'den kuralı getir ve benzerlerini bul
    2. rule_content ile: Gönderilen kuralın benzerlerini bul
    """
    
    import time
    start_time = time.time()
    
    # MongoDB bağlantısı
    mongo_manager = MongoSigmaManager(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)
    if not mongo_manager.connect():
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    # Ollama AI analyzer
    ai_analyzer = OllamaSigmaAnalyzer(request.ollama_url, request.model_name)
    if not ai_analyzer.test_ollama_connection():
        raise HTTPException(status_code=500, detail="Ollama bağlantısı kurulamadı")
    
    try:
        # Hedef kuralı belirle
        if request.rule_id:
            # MongoDB'den ID ile kural getir
            target_rule = mongo_manager.get_rule_by_id(request.rule_id)
            if not target_rule:
                raise HTTPException(status_code=404, detail="Kural bulunamadı")
        elif request.rule_content:
            # Gönderilen kuralı kullan
            target_rule = request.rule_content
        else:
            raise HTTPException(status_code=400, detail="rule_id veya rule_content gerekli")
        
        # Tüm kuralları getir
        all_rules = mongo_manager.get_all_rules()
        if not all_rules:
            raise HTTPException(status_code=404, detail="Veritabanında kural bulunamadı")
        
        # Hedef kuralı listeden çıkar (kendisiyle karşılaştırmasın)
        filtered_rules = [rule for rule in all_rules if str(rule.get('_id')) != str(target_rule.get('_id'))]
        
        # AI ile benzerlik analizi
        similar_rules = ai_analyzer.find_similar_rules(
            target_rule=target_rule,
            all_rules=filtered_rules,
            threshold=request.threshold,
            max_results=request.max_results
        )
        
        # Sonuçları formatla
        formatted_results = []
        for result in similar_rules:
            rule = result['rule']
            formatted_results.append({
                "rule_id": str(rule.get('_id')),
                "title": rule.get('title', 'No title'),
                "description": rule.get('description', ''),
                "author": rule.get('author', ''),
                "tags": rule.get('tags', []),
                "similarity_score": result['similarity_score'],
                "ai_summary": result['ai_summary'],
                "detection": rule.get('detection', {}),
                "creation_date": rule.get('date', ''),
                "level": rule.get('level', '')
            })
        
        processing_time = time.time() - start_time
        
        return SimilarityResponse(
            success=True,
            target_rule_title=target_rule.get('title', 'No title'),
            target_rule_id=str(target_rule.get('_id')) if target_rule.get('_id') else None,
            similar_rules=formatted_results,
            total_rules_analyzed=len(filtered_rules),
            processing_time_seconds=round(processing_time, 2),
            ai_model_used=request.model_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")
    finally:
        mongo_manager.close()

@app.get("/rules")
async def list_rules(limit: int = 50, skip: int = 0):
    """N8N için kural listesi"""
    
    mongo_manager = MongoSigmaManager(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)
    if not mongo_manager.connect():
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        rules = list(mongo_manager.collection.find().skip(skip).limit(limit))
        
        formatted_rules = []
        for rule in rules:
            formatted_rules.append({
                "rule_id": str(rule.get('_id')),
                "title": rule.get('title', 'No title'),
                "description": rule.get('description', ''),
                "author": rule.get('author', ''),
                "tags": rule.get('tags', []),
                "level": rule.get('level', ''),
                "date": rule.get('date', '')
            })
        
        return {
            "success": True,
            "rules": formatted_rules,
            "count": len(formatted_rules),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Kural listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")
    finally:
        mongo_manager.close()

@app.get("/rule/{rule_id}")
async def get_rule(rule_id: str):
    """N8N için tek kural getirme"""
    
    mongo_manager = MongoSigmaManager(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)
    if not mongo_manager.connect():
        raise HTTPException(status_code=500, detail="MongoDB bağlantısı kurulamadı")
    
    try:
        rule = mongo_manager.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Kural bulunamadı")
        
        # MongoDB ObjectId'yi string'e çevir
        rule['_id'] = str(rule['_id'])
        
        return {
            "success": True,
            "rule": rule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kural getirme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")
    finally:
        mongo_manager.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)