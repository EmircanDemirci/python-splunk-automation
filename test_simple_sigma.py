#!/usr/bin/env python3

from simple_sigma_comparator import SimpleSigmaComparator
import yaml
import time

def test_simple_comparison():
    """Basit ve hızlı Sigma kural karşılaştırması testi"""
    
    # Örnek kullanıcı Sigma kuralı
    user_sigma_rule = {
        "title": "PowerShell Suspicious Activity",
        "description": "Detects suspicious PowerShell commands",
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
                    "iex",
                    "invoke-expression"
                ]
            },
            "condition": "selection"
        },
        "tags": [
            "attack.execution",
            "attack.t1059.001"
        ]
    }
    
    print("⚡ Basit ve Hızlı SigmaHQ Benzerlik Testi")
    print("="*50)
    
    # Kullanıcı kuralını göster
    print("\n🎯 KULLANICI SIGMA KURALI:")
    print("-"*30)
    print(f"📋 Başlık: {user_sigma_rule['title']}")
    print(f"📄 Açıklama: {user_sigma_rule['description']}")
    print(f"🏷️ Tags: {user_sigma_rule['tags']}")
    print(f"📊 Level: {user_sigma_rule['level']}")
    
    # Comparator'ı başlat
    print("\n🔧 Basit comparator başlatılıyor...")
    
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    comparator = SimpleSigmaComparator(MONGO_CONNECTION)
    
    if not comparator.connect_mongodb():
        print("❌ MongoDB bağlantısı kurulamadı!")
        return
    
    try:
        # Hızlı analiz
        print("⚡ Hızlı benzerlik analizi başlıyor...")
        start_time = time.time()
        
        similar_rule = comparator.find_first_similar_rule(
            input_rule=user_sigma_rule,
            threshold=0.3  # Düşük threshold
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Sonuçları göster
        if similar_rule:
            print(f"\n🏆 BENZER KURAL BULUNDU! (⏱️ {processing_time:.2f} saniye)")
            print("="*50)
            print(f"📋 Başlık: {similar_rule['title']}")
            print(f"🎯 Benzerlik: {similar_rule['similarity_score']:.1%}")
            print(f"🏷️ Tags: {similar_rule['tags'][:3]}...")  # İlk 3 tag
            print(f"📊 Level: {similar_rule['level']}")
            print(f"👤 Author: {similar_rule['author']}")
            
            # Performance info
            print(f"\n📈 PERFORMANS:")
            print(f"   ⚡ İşlem süresi: {processing_time:.2f} saniye")
            print(f"   🔍 Analiz türü: String benzerlik (AI yok)")
            print(f"   🎯 İlk eşleşmede durdu: Evet")
                
        else:
            print(f"\n❌ Benzer kural bulunamadı (⏱️ {processing_time:.2f} saniye)")
            print("💡 Threshold'u daha da düşürmeyi deneyin (örn: 0.2)")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
    finally:
        comparator.close_connection()

def test_multiple_rules():
    """Birden fazla kural ile hız testi"""
    
    test_rules = [
        {
            "title": "CMD Execution",
            "detection": {
                "selection": {
                    "Image|endswith": "\\cmd.exe",
                    "CommandLine|contains": ["whoami", "net user"]
                },
                "condition": "selection"
            },
            "tags": ["attack.discovery"]
        },
        {
            "title": "Registry Modification", 
            "detection": {
                "selection": {
                    "EventID": 13,
                    "TargetObject|contains": "\\CurrentVersion\\Run"
                },
                "condition": "selection"
            },
            "tags": ["attack.persistence"]
        },
        {
            "title": "Suspicious Network Connection",
            "detection": {
                "selection": {
                    "EventID": 3,
                    "DestinationPort": [4444, 8080, 9999]
                },
                "condition": "selection"
            },
            "tags": ["attack.command_and_control"]
        }
    ]
    
    print("\n" + "="*50)
    print("🧪 ÇOKLİ KURAL HIZ TESTİ")
    print("="*50)
    
    comparator = SimpleSigmaComparator("mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/")
    
    if not comparator.connect_mongodb():
        print("❌ MongoDB bağlantısı kurulamadı!")
        return
    
    total_start = time.time()
    results = []
    
    for i, rule in enumerate(test_rules, 1):
        print(f"\n{i}. Test: {rule['title']}")
        
        start_time = time.time()
        similar = comparator.find_first_similar_rule(rule, threshold=0.3)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if similar:
            print(f"   ✅ Benzer bulundu: {similar['similarity_score']:.1%} ({processing_time:.2f}s)")
            results.append(True)
        else:
            print(f"   ❌ Benzer bulunamadı ({processing_time:.2f}s)")
            results.append(False)
    
    total_time = time.time() - total_start
    success_rate = (sum(results) / len(results)) * 100
    
    print(f"\n📈 GENEL PERFORMANS:")
    print(f"   🏆 Başarı oranı: {success_rate:.0f}%")
    print(f"   ⏱️ Toplam süre: {total_time:.2f} saniye")
    print(f"   ⚡ Ortalama süre: {total_time/len(test_rules):.2f} saniye/kural")
    
    comparator.close_connection()

if __name__ == "__main__":
    print("⚡ Basit SigmaHQ Benzerlik Analizi - Hız Testi")
    print("Bu test MongoDB'deki SigmaHQ kuralları ile hızlı karşılaştırma yapar")
    print("🚀 AI YOK - Sadece string algoritması ile çok hızlı!")
    print()
    
    try:
        # Ana test
        test_simple_comparison()
        
        # Çoklu test
        test_multiple_rules()
        
        print("\n✅ Tüm testler tamamlandı!")
        print("💡 Bu sistem AI kullanmadığı için çok daha hızlı çalışır")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")