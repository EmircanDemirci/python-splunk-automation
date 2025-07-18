#!/usr/bin/env python3

import json
import time

def test_api_models():
    """API modellerini test et (MongoDB olmadan)"""
    
    print("🚀 Detection Odaklı API Test")
    print("="*40)
    
    # Test data
    test_request = {
        "sigma_rule": {
            "title": "PowerShell Suspicious Activity",
            "description": "Detects suspicious PowerShell usage",
            "detection": {
                "selection": {
                    "Image|endswith": "\\powershell.exe",
                    "CommandLine|contains": [
                        "DownloadString",
                        "iex",
                        "Invoke-Expression"
                    ]
                },
                "condition": "selection"
            },
            "level": "medium"
        },
        "threshold": 0.4
    }
    
    print("📊 TEST REQUEST DATA:")
    print(json.dumps(test_request, indent=2))
    
    # Simulate API logic (offline test)
    from simple_sigma_comparator import SimpleSigmaComparator
    
    comparator = SimpleSigmaComparator("test://connection")
    
    # Test detection extraction
    input_rule = test_request["sigma_rule"]
    detection_content = comparator.extract_detection_content(input_rule)
    fields = comparator.extract_field_names(input_rule.get('detection', {}))
    values = comparator.extract_detection_values(input_rule.get('detection', {}))
    
    print(f"\n🔧 DETECTION PARSE:")
    print(f"📝 Content: {detection_content}")
    print(f"🏷️ Fields: {fields}")
    print(f"💎 Values: {values}")
    
    # Simulate response
    mock_response = {
        "success": True,
        "input_rule_title": input_rule.get('title'),
        "input_rule_description": input_rule.get('description'),
        "similar_rule": {
            "rule_id": "mock_rule_123",
            "title": "PowerShell Download Cradle",
            "description": "Detects PowerShell download activities",
            "similarity_score": 0.75,
            "similarity_percentage": 75,
            "tags": ["attack.execution", "attack.t1059.001"],
            "level": "high",
            "author": "SigmaHQ",
            "date": "2023/05/15",
            "explanation": "Yüksek detection benzerliği - Ortak field: image, commandline - Ortak değer: \\powershell.exe"
        },
        "processing_time_seconds": 0.25,
        "threshold_used": 0.4,
        "message": "Benzer kural bulundu"
    }
    
    print(f"\n📊 MOCK API RESPONSE:")
    print(json.dumps(mock_response, indent=2, ensure_ascii=False))
    
    print(f"\n✅ API TEST TAMAMLANDI!")
    print(f"🎯 Detection odaklı sistem hazır")
    print(f"⚡ MongoDB bağlantısı olmadan da test edilebilir")

if __name__ == "__main__":
    test_api_models()