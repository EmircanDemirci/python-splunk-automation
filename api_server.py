from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml
from typing import List, Dict, Any
import logging

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI uygulaması oluştur
app = FastAPI(
    title="Sigma to Splunk Converter API",
    description="Sigma kurallarını Splunk sorgularına dönüştüren REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request modeli
class SigmaConvertRequest(BaseModel):
    sigma_rule: str
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "sigma_rule": """title: Test Rule
description: A test detection rule
status: test
author: Test Author
date: 2023/01/01
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\cmd.exe'
        CommandLine|contains: 'whoami'
    condition: selection
falsepositives:
    - Unknown
level: medium""",
                "metadata": {
                    "request_id": "12345",
                    "user": "test_user"
                }
            }
        }

# Response modeli
class SigmaConvertResponse(BaseModel):
    success: bool
    message: str
    queries: List[str] = []
    rule_info: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# Health check endpoint
@app.get("/health")
async def health_check():
    """API sağlık durumu kontrolü"""
    return {"status": "healthy", "service": "sigma-to-splunk-converter"}

# Ana dönüştürme endpoint'i
@app.post("/convert", response_model=SigmaConvertResponse)
async def convert_sigma_to_splunk(request: SigmaConvertRequest):
    """
    Sigma kuralını Splunk sorgusuna dönüştür
    
    Args:
        request: SigmaConvertRequest - Sigma kuralı ve metadata içeren istek
        
    Returns:
        SigmaConvertResponse - Dönüştürülmüş Splunk sorguları ve bilgiler
    """
    
    logger.info(f"Sigma dönüştürme isteği alındı. Metadata: {request.metadata}")
    
    try:
        # YAML parse et
        try:
            sigma_dict = yaml.safe_load(request.sigma_rule)
            if not sigma_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Boş veya geçersiz YAML formatı"
                )
        except yaml.YAMLError as e:
            logger.error(f"YAML parse hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YAML parse hatası: {str(e)}"
            )
        
        # SigmaRule objesi oluştur
        try:
            sigma_rule = SigmaRule.from_dict(sigma_dict)
        except Exception as e:
            logger.error(f"SigmaRule oluşturma hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz Sigma kuralı formatı: {str(e)}"
            )
        
        # SigmaCollection oluştur
        collection = SigmaCollection([sigma_rule])
        
        # Splunk backend oluştur
        backend = SplunkBackend()
        
        # Sigma'yı Splunk'a dönüştür
        try:
            queries = backend.convert(collection)
            splunk_queries = [str(query) for query in queries]
        except Exception as e:
            logger.error(f"Sigma dönüştürme hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sigma dönüştürme hatası: {str(e)}"
            )
        
        # Kural bilgilerini topla
        rule_info = {
            "title": getattr(sigma_rule, 'title', 'N/A'),
            "description": getattr(sigma_rule, 'description', 'N/A'),
            "author": getattr(sigma_rule, 'author', 'N/A'),
            "status": getattr(sigma_rule, 'status', 'N/A'),
            "level": getattr(sigma_rule, 'level', 'N/A'),
            "logsource": getattr(sigma_rule, 'logsource', {}).__dict__ if hasattr(getattr(sigma_rule, 'logsource', {}), '__dict__') else str(getattr(sigma_rule, 'logsource', {})),
            "tags": getattr(sigma_rule, 'tags', [])
        }
        
        logger.info(f"Başarıyla {len(splunk_queries)} Splunk sorgusu oluşturuldu")
        
        return SigmaConvertResponse(
            success=True,
            message=f"Sigma kuralı başarıyla {len(splunk_queries)} Splunk sorgusuna dönüştürüldü",
            queries=splunk_queries,
            rule_info=rule_info,
            metadata=request.metadata
        )
        
    except HTTPException:
        # HTTPException'ları tekrar fırlat
        raise
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sunucu hatası: {str(e)}"
        )

# Batch dönüştürme endpoint'i
@app.post("/convert-batch", response_model=List[SigmaConvertResponse])
async def convert_batch_sigma_to_splunk(requests: List[SigmaConvertRequest]):
    """
    Birden fazla Sigma kuralını toplu olarak Splunk sorgularına dönüştür
    
    Args:
        requests: List[SigmaConvertRequest] - Sigma kuralları listesi
        
    Returns:
        List[SigmaConvertResponse] - Dönüştürülmüş Splunk sorguları listesi
    """
    
    logger.info(f"Toplu dönüştürme isteği alındı. {len(requests)} kural")
    
    results = []
    
    for i, request in enumerate(requests):
        try:
            result = await convert_sigma_to_splunk(request)
            results.append(result)
        except HTTPException as e:
            # Hatalı kurallar için hata response'u ekle
            error_response = SigmaConvertResponse(
                success=False,
                message=f"Kural {i+1} dönüştürme hatası: {e.detail}",
                queries=[],
                rule_info={},
                metadata=request.metadata
            )
            results.append(error_response)
        except Exception as e:
            error_response = SigmaConvertResponse(
                success=False,
                message=f"Kural {i+1} beklenmeyen hata: {str(e)}",
                queries=[],
                rule_info={},
                metadata=request.metadata
            )
            results.append(error_response)
    
    return results

# Supported backends listesi
@app.get("/backends")
async def get_supported_backends():
    """Desteklenen backend'leri listele"""
    return {
        "supported_backends": ["splunk"],
        "default_backend": "splunk",
        "description": "Bu API şu anda yalnızca Splunk backend'ini desteklemektedir"
    }

# Örnek Sigma kuralı endpoint'i
@app.get("/example")
async def get_example_sigma_rule():
    """Örnek Sigma kuralı döndür"""
    example_rule = """title: Suspicious Process Creation
description: Detects suspicious process creation events
status: experimental
author: Security Team
date: 2023/01/01
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: 
            - '\\cmd.exe'
            - '\\powershell.exe'
        CommandLine|contains: 
            - 'whoami'
            - 'net user'
            - 'tasklist'
    condition: selection
falsepositives:
    - Administrative activities
level: medium
tags:
    - attack.discovery
    - attack.t1057"""
    
    return {
        "example_sigma_rule": example_rule,
        "description": "Bu örnekte Windows'ta şüpheli process oluşturma olayları tespit edilir"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)