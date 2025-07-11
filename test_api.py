#!/usr/bin/env python3
"""
Sigma to Splunk API Test Script
Bu script API'nin çalışıp çalışmadığını test eder.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Health check endpoint'ini test et"""
    print("🔄 Health check testi...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check başarılı!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check başarısız: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check hatası: {e}")
    print("-" * 50)

def test_example_endpoint():
    """Example endpoint'ini test et"""
    print("🔄 Example endpoint testi...")
    try:
        response = requests.get(f"{BASE_URL}/example")
        if response.status_code == 200:
            print("✅ Example endpoint başarılı!")
            data = response.json()
            print(f"Örnek Sigma kuralı alındı: {len(data['example_sigma_rule'])} karakter")
        else:
            print(f"❌ Example endpoint başarısız: {response.status_code}")
    except Exception as e:
        print(f"❌ Example endpoint hatası: {e}")
    print("-" * 50)

def test_list_files_endpoint():
    """List Sigma files endpoint'ini test et"""
    print("🔄 List Sigma files testi...")
    try:
        response = requests.get(f"{BASE_URL}/list-sigma-files")
        if response.status_code == 200:
            print("✅ List files endpoint başarılı!")
            data = response.json()
            print(f"📁 Bulunan dosya sayısı: {data.get('total_count', 0)}")
            if data.get('files'):
                print(f"📋 İlk birkaç dosya:")
                for i, file in enumerate(data['files'][:3]):
                    print(f"  {i+1}. {file['name']} ({file['size']} bytes)")
        else:
            print(f"❌ List files endpoint başarısız: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ List files endpoint hatası: {e}")
    print("-" * 50)

def test_search_sigma_endpoint():
    """Search Sigma endpoint'ini test et"""
    print("🔄 Search Sigma endpoint testi...")
    
    # Bilinen bir Sigma ID'si ile test (gerçek bir ID olması gerekiyor)
    # Bu ID'yi list-sigma-files endpoint'inden alınan gerçek bir dosyadan alabiliriz
    test_id = "7efd2c8d-8b18-45b7-947d-adfe9ed04f61"  # Örnek ID
    
    payload = {
        "target_id": test_id,
        "metadata": {
            "request_id": "search-test-123",
            "user": "test_user",
            "timestamp": int(time.time())
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/search-sigma",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Search Sigma endpoint başarılı!")
            data = response.json()
            print(f"📊 Arama sonucu: {data['message']}")
            
            if data['success'] and data.get('found_rule'):
                found_rule = data['found_rule']
                print(f"📄 Bulunan dosya: {found_rule['filename']}")
                print(f"🆔 ID: {found_rule['id']}")
                print(f"📐 Dosya boyutu: {found_rule['file_size']} bytes")
                print(f"📝 İçerik önizleme: {found_rule['content'][:200]}...")
            
            stats = data.get('search_stats', {})
            print(f"\n📈 Arama istatistikleri:")
            print(f"  - Toplam dosya: {stats.get('total_files', 0)}")
            print(f"  - Aranan dosya: {stats.get('searched_files', 0)}")
            print(f"  - Atlanan dosya: {stats.get('skipped_files', 0)}")
                
        else:
            print(f"❌ Search Sigma endpoint başarısız: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Search Sigma endpoint hatası: {e}")
    print("-" * 50)

def test_search_and_convert_endpoint():
    """Search and convert endpoint'ini test et"""
    print("🔄 Search and Convert endpoint testi...")
    
    # Bilinen bir Sigma ID'si ile test
    test_id = "7efd2c8d-8b18-45b7-947d-adfe9ed04f61"
    
    payload = {
        "target_id": test_id,
        "metadata": {
            "request_id": "search-convert-123",
            "user": "test_user",
            "timestamp": int(time.time())
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/search-and-convert",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Search and Convert endpoint başarılı!")
            data = response.json()
            print(f"📊 Sonuç: {data['message']}")
            
            if data['success']:
                search_result = data.get('search_result', {})
                conversion_result = data.get('conversion_result', {})
                
                if search_result.get('found_rule'):
                    print(f"🔍 Bulunan dosya: {search_result['found_rule']['filename']}")
                
                if conversion_result and conversion_result.get('queries'):
                    print(f"🔧 Dönüştürülen sorgu sayısı: {len(conversion_result['queries'])}")
                    print(f"📋 İlk Splunk sorgusu:")
                    print(f"```\n{conversion_result['queries'][0]}\n```")
                
        else:
            print(f"❌ Search and Convert endpoint başarısız: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Search and Convert endpoint hatası: {e}")
    print("-" * 50)

def test_convert_endpoint():
    """Convert endpoint'ini test et"""
    print("🔄 Convert endpoint testi...")
    
    # Örnek Sigma kuralı
    sigma_rule = """title: Suspicious CMD Usage
description: Detects suspicious command line usage
status: experimental
author: Test User
date: 2023/01/01
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\cmd.exe'
        CommandLine|contains: 
            - 'whoami'
            - 'net user'
    condition: selection
falsepositives:
    - Administrative tasks
level: medium
tags:
    - attack.discovery
    - attack.t1057"""
    
    # Request payload
    payload = {
        "sigma_rule": sigma_rule,
        "metadata": {
            "request_id": "test-123",
            "user": "test_user",
            "timestamp": int(time.time())
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/convert",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Convert endpoint başarılı!")
            data = response.json()
            print(f"📊 Sonuç: {data['message']}")
            print(f"📋 Oluşturulan sorgu sayısı: {len(data['queries'])}")
            
            for i, query in enumerate(data['queries'], 1):
                print(f"\n🔍 Splunk Query {i}:")
                print(f"```\n{query}\n```")
            
            print(f"\n📝 Kural bilgileri:")
            for key, value in data['rule_info'].items():
                print(f"  - {key}: {value}")
                
        else:
            print(f"❌ Convert endpoint başarısız: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Convert endpoint hatası: {e}")
    print("-" * 50)

def test_batch_convert():
    """Batch convert endpoint'ini test et"""
    print("🔄 Batch convert endpoint testi...")
    
    # Birden fazla Sigma kuralı
    sigma_rules = [
        {
            "sigma_rule": """title: Process Creation Rule 1
description: Detects cmd.exe usage
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\cmd.exe'
    condition: selection
level: low""",
            "metadata": {"rule_id": "rule1"}
        },
        {
            "sigma_rule": """title: Process Creation Rule 2
description: Detects powershell.exe usage
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\powershell.exe'
    condition: selection
level: medium""",
            "metadata": {"rule_id": "rule2"}
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/convert-batch",
            json=sigma_rules,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Batch convert endpoint başarılı!")
            data = response.json()
            print(f"📊 İşlenen kural sayısı: {len(data)}")
            
            for i, result in enumerate(data, 1):
                print(f"\n📋 Kural {i} Sonucu:")
                print(f"  - Başarılı: {result['success']}")
                print(f"  - Mesaj: {result['message']}")
                if result['queries']:
                    print(f"  - Sorgu sayısı: {len(result['queries'])}")
                    print(f"  - İlk sorgu: {result['queries'][0][:100]}...")
                
        else:
            print(f"❌ Batch convert endpoint başarısız: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Batch convert endpoint hatası: {e}")
    print("-" * 50)

def test_backends_endpoint():
    """Backends endpoint'ini test et"""
    print("🔄 Backends endpoint testi...")
    try:
        response = requests.get(f"{BASE_URL}/backends")
        if response.status_code == 200:
            print("✅ Backends endpoint başarılı!")
            data = response.json()
            print(f"Desteklenen backend'ler: {data['supported_backends']}")
            print(f"Varsayılan backend: {data['default_backend']}")
        else:
            print(f"❌ Backends endpoint başarısız: {response.status_code}")
    except Exception as e:
        print(f"❌ Backends endpoint hatası: {e}")
    print("-" * 50)

def test_uuid_endpoint():
    """UUID kontrol endpoint'ini test et"""
    print("🔄 UUID kontrol endpoint testi...")
    
    # Test veri setleri
    test_cases = [
        {
            "value": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
            "expected": True,
            "description": "Geçerli UUID v4"
        },
        {
            "value": "550e8400-e29b-41d4-a716-446655440000", 
            "expected": True,
            "description": "Geçerli UUID v1"
        },
        {
            "value": "invalid-uuid-format",
            "expected": False,
            "description": "Geçersiz UUID formatı"
        },
        {
            "value": "12345",
            "expected": False,
            "description": "Sayı - UUID değil"
        },
        {
            "value": "",
            "expected": False,
            "description": "Boş string"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        
        payload = {
            "value": test_case["value"],
            "metadata": {
                "test_case": i,
                "description": test_case["description"]
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/is-uuid",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data["is_valid_uuid"]
                
                if is_valid == test_case["expected"]:
                    print(f"✅ Test başarılı!")
                    print(f"   Sonuç: {data['message']}")
                    if data.get('uuid_version'):
                        print(f"   UUID Version: {data['uuid_version']}")
                else:
                    print(f"❌ Test başarısız!")
                    print(f"   Beklenen: {test_case['expected']}, Alınan: {is_valid}")
                    print(f"   Mesaj: {data['message']}")
            else:
                print(f"❌ HTTP Hatası: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test hatası: {e}")
    
    print("-" * 50)

def main():
    """Ana test fonksiyonu"""
    print("🚀 Sigma to Splunk API Test Başlatılıyor...")
    print("=" * 50)
    
    # Tüm testleri çalıştır
    test_health_check()
    test_example_endpoint()
    test_backends_endpoint()
    test_uuid_endpoint()
    test_list_files_endpoint()
    test_search_sigma_endpoint()
    test_search_and_convert_endpoint()
    test_convert_endpoint()
    test_batch_convert()
    
    print("🎉 Tüm testler tamamlandı!")

if __name__ == "__main__":
    main()