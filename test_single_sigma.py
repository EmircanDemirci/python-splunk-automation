#!/usr/bin/env python3

from single_sigma_comparator import SigmaHQComparator
import yaml

def test_single_sigma_comparison():
    """Test single Sigma rule comparison with SigmaHQ rules"""
    
    # Örnek kullanıcı Sigma kuralı
    user_sigma_rule = {
        "title": "Suspicious PowerShell Download Activity",
        "id": "test-rule-001",
        "status": "test",
        "description": "Detects PowerShell scripts that download files from internet",
        "author": "Test User",
        "date": "2024/01/15",
        "level": "medium",
        "logsource": {
            "category": "process_creation",
            "product": "windows"
        },
        "detection": {
            "selection": {
                "Image|endswith": "\\powershell.exe",
                "CommandLine|contains": [
                    "DownloadString",
                    "DownloadFile", 
                    "WebClient",
                    "iex",
                    "Invoke-Expression"
                ]
            },
            "condition": "selection"
        },
        "falsepositives": [
            "Legitimate software updates",
            "IT administration scripts"
        ],
        "tags": [
            "attack.execution",
            "attack.t1059.001",
            "attack.command_and_control",
            "attack.t1071.001"
        ]
    }
    
    print("🚀 SigmaHQ Benzerlik Analizi Test'i")
    print("="*50)
    
    # Kullanıcı kuralını göster
    print("\n🎯 KULLANICI SIGMA KURALI:")
    print("-"*30)
    print(f"📋 Başlık: {user_sigma_rule['title']}")
    print(f"📄 Açıklama: {user_sigma_rule['description']}")
    print(f"🏷️ Tags: {user_sigma_rule['tags']}")
    print(f"📊 Level: {user_sigma_rule['level']}")
    
    # YAML formatında göster
    print("\n📝 YAML Formatı:")
    print(yaml.dump(user_sigma_rule, default_flow_style=False, allow_unicode=True))
    
    # Comparator'ı başlat
    print("🔧 SigmaHQ Comparator başlatılıyor...")
    
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    comparator = SigmaHQComparator(MONGO_CONNECTION)
    
    # Bağlantıları test et
    if not comparator.test_ollama_connection():
        print("❌ Ollama bağlantısı kurulamadı!")
        print("💡 Çözüm: 'ollama serve' komutunu çalıştırın")
        return
    
    if not comparator.connect_mongodb():
        print("❌ MongoDB bağlantısı kurulamadı!")
        return
    
    try:
        # Benzerlik analizi yap
        print("🤖 AI ile SigmaHQ kuralları analiz ediliyor...")
        similar_rules = comparator.find_most_similar_rules(
            input_rule=user_sigma_rule,
            threshold=0.3,
            max_results=5
        )
        
        # Sonuçları göster
        if similar_rules:
            print(f"\n🏆 {len(similar_rules)} BENZER SIGMAHQ KURALI BULUNDU:")
            print("="*60)
            
            for i, result in enumerate(similar_rules, 1):
                print(f"\n{i}. 📋 {result['title']}")
                print(f"   🎯 Benzerlik: {result['similarity_score']:.1%}")
                print(f"   🏷️ Tags: {result['tags'][:3]}...")  # İlk 3 tag
                print(f"   📊 Level: {result['level']}")
                print(f"   👤 Author: {result['author']}")
                print(f"   🤖 AI Analizi: {result.get('ai_summary', 'Özet yok')[:100]}...")
                
        else:
            print("\n❌ Benzer kural bulunamadı!")
            print("💡 Threshold'u düşürmeyi deneyin (örn: 0.2)")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
    finally:
        comparator.close_connection()

def test_yaml_input():
    """YAML string input testi"""
    
    yaml_input = """
title: Malicious Process Creation
description: Detects creation of suspicious processes
author: Security Team
date: 2024/01/15
level: high
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
            - 'systeminfo'
    condition: selection
tags:
    - attack.discovery
    - attack.t1033
    - attack.t1082
"""
    
    print("\n" + "="*50)
    print("🧪 YAML STRING INPUT TESТİ")
    print("="*50)
    
    comparator = SigmaHQComparator("mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/")
    
    # YAML'ı parse et
    rule = comparator.load_sigma_rule_from_text(yaml_input)
    
    if rule:
        print("✅ YAML başarıyla parse edildi!")
        print(f"📋 Başlık: {rule.get('title')}")
        print(f"📄 Açıklama: {rule.get('description')}")
        
        # Bu kuralı da analiz edebiliriz
        if comparator.test_ollama_connection() and comparator.connect_mongodb():
            print("\n🔍 Bu kural için de SigmaHQ analizi yapılıyor...")
            similar = comparator.find_most_similar_rules(rule, threshold=0.3, max_results=3)
            
            if similar:
                print(f"🎯 {len(similar)} benzer kural bulundu!")
                for i, s in enumerate(similar, 1):
                    print(f"   {i}. {s['title']} ({s['similarity_score']:.1%})")
            else:
                print("❌ Benzer kural bulunamadı")
                
            comparator.close_connection()
    else:
        print("❌ YAML parse edilemedi!")

if __name__ == "__main__":
    print("🎯 SigmaHQ Tek Kural Benzerlik Analizi")
    print("Bu test MongoDB'deki SigmaHQ kuralları ile karşılaştırma yapar")
    print()
    
    try:
        # Ana test
        test_single_sigma_comparison()
        
        # YAML test
        test_yaml_input()
        
        print("\n✅ Test tamamlandı!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")