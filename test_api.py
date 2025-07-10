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

def main():
    """Ana test fonksiyonu"""
    print("🚀 Sigma to Splunk API Test Başlatılıyor...")
    print("=" * 50)

    # Tüm testleri çalıştır
    test_health_check()
    test_example_endpoint()
    test_backends_endpoint()
    test_convert_endpoint()
    test_batch_convert()

    print("🎉 Tüm testler tamamlandı!")

if __name__ == "__main__":
    main()