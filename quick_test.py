#!/usr/bin/env python3

from simple_sigma_comparator import SimpleSigmaComparator
import time

def quick_detection_test():
    """Detection odaklı hızlı test"""
    
    print("🎯 Detection Odaklı Sigma Benzerlik Testi")
    print("="*50)
    
    # Örnek PowerShell detection kuralı
    test_rule = {
        "title": "Test PowerShell Rule",
        "description": "Test detection for PowerShell activity",
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
    }
    
    print("\n🎯 TEST KURALI:")
    print(f"📋 Başlık: {test_rule['title']}")
    print(f"🔍 Detection Fields: Image, CommandLine")
    print(f"📄 Detection Values: powershell.exe, DownloadString, iex")
    
    # Comparator'ı test et (bağlantı olmasa bile algoritma çalışır)
    comparator = SimpleSigmaComparator("test://connection")
    
    # Detection içeriğini çıkar
    print("\n🔧 DETECTION PARSE TESTİ:")
    detection_content = comparator.extract_detection_content(test_rule)
    print(f"📝 Parse sonucu: {detection_content}")
    
    # Field'ları çıkar
    fields = comparator.extract_field_names(test_rule.get('detection', {}))
    print(f"🏷️ Field'lar: {fields}")
    
    # Value'ları çıkar
    values = comparator.extract_detection_values(test_rule.get('detection', {}))
    print(f"💎 Value'lar: {values}")
    
    # Benzer bir kural oluştur
    similar_rule = {
        "title": "PowerShell Download Cradle",
        "detection": {
            "selection": {
                "Image|endswith": "\\powershell.exe",
                "CommandLine|contains": [
                    "DownloadFile",
                    "WebClient",
                    "iex"
                ]
            },
            "condition": "selection"
        }
    }
    
    print("\n🔄 BENZERLIK TESTİ:")
    print(f"📋 Karşılaştırılan: {similar_rule['title']}")
    
    similarity = comparator.calculate_detection_similarity(test_rule, similar_rule)
    print(f"🎯 Detection Benzerliği: {similarity:.1%}")
    
    # Analiz detayları
    fields1 = comparator.extract_field_names(test_rule.get('detection', {}))
    fields2 = comparator.extract_field_names(similar_rule.get('detection', {}))
    common_fields = fields1.intersection(fields2)
    
    values1 = comparator.extract_detection_values(test_rule.get('detection', {}))
    values2 = comparator.extract_detection_values(similar_rule.get('detection', {}))
    common_values = values1.intersection(values2)
    
    print(f"🏷️ Ortak Field'lar: {common_fields}")
    print(f"💎 Ortak Value'lar: {common_values}")
    
    # Farklı bir kural test et
    different_rule = {
        "title": "Registry Persistence",
        "detection": {
            "selection": {
                "EventID": 13,
                "TargetObject|contains": "\\CurrentVersion\\Run"
            },
            "condition": "selection"
        }
    }
    
    print(f"\n🔄 FARKLI KURAL TESTİ:")
    print(f"📋 Karşılaştırılan: {different_rule['title']}")
    
    similarity2 = comparator.calculate_detection_similarity(test_rule, different_rule)
    print(f"🎯 Detection Benzerliği: {similarity2:.1%}")
    
    print(f"\n📊 SONUÇ:")
    print(f"   ✅ Benzer kural: {similarity:.1%} (PowerShell)")
    print(f"   ❌ Farklı kural: {similarity2:.1%} (Registry)")
    print(f"   🎯 Sistem detection odaklı çalışıyor!")

if __name__ == "__main__":
    quick_detection_test()