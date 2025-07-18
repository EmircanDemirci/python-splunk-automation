#!/usr/bin/env python3

from single_sigma_comparator import SigmaHQComparator
import time

def test_ai_detection_focus():
    """AI tabanlı detection odaklı test"""
    
    print("🤖 AI Destekli Detection Odaklı Sigma Testi")
    print("="*50)
    
    # Test kuralı
    test_rule = {
        "title": "PowerShell Suspicious Download",
        "description": "Detects PowerShell download activities",
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
    print(f"🔍 Detection: PowerShell process + download commands")
    
    # AI formatını test et
    comparator = SigmaHQComparator("test://connection")
    
    detection_format = comparator.format_detection_for_ai(test_rule)
    print(f"\n📝 AI DETECTION FORMAT:")
    print(detection_format)
    
    # Benzer kural simüle et
    similar_rule = {
        "title": "PowerShell Download Cradle Detection",
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
    
    print(f"\n🔄 BENZER KURAL:")
    print(f"📋 Başlık: {similar_rule['title']}")
    similar_format = comparator.format_detection_for_ai(similar_rule)
    print(f"📝 Detection Format: {similar_format}")
    
    # AI prompt'u göster
    print(f"\n🤖 AI PROMPT ÖRNEĞİ:")
    print("="*30)
    print("İki Sigma kuralının DETECTION mantığını karşılaştır...")
    print("SADECE DETECTION mantığına odaklan:")
    print("- Field isimleri (Image, CommandLine, EventID)")
    print("- Field değerleri (powershell.exe, cmd.exe)")
    print("- Condition mantığı (selection, filter)")
    print("")
    print("KULLANICI DETECTION:")
    print(detection_format[:100] + "...")
    print("")
    print("SIGMAHQ DETECTION:")
    print(similar_format[:100] + "...")
    print("")
    print("Sadece sayısal skor ver (örnek: 0.75)")
    print("="*30)
    
    print(f"\n✅ AI DETECTION ODAKLI TEST TAMAMLANDI!")
    print(f"🎯 Sistem sadece detection mantığına odaklanıyor")
    print(f"⚡ İlk benzer kuralı bulunca duracak")
    print(f"🤖 AI ile semantik analiz yapacak")

if __name__ == "__main__":
    test_ai_detection_focus()