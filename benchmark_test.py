#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sigma Karşılaştırıcı Benchmark ve Test Scripti
Performans ve doğruluk testleri
"""

import time
import asyncio
import statistics
from typing import List, Dict
import yaml
from advanced_sigma_comparator import SigmaComparator, main

# Test YAML kuralları
TEST_RULES = {
    "web_attack": """
title: Web Application Attack Detected
description: Detects various web application attacks
logsource:
    category: webserver
    product: nginx
detection:
    selection:
        - cs-uri-query|contains:
            - "union select"
            - "drop table"
            - "script>"
            - "../../../"
    condition: selection
level: high
tags:
    - attack.initial_access
    - attack.t1190
""",
    
    "powershell_attack": """
title: Suspicious PowerShell Execution
description: Detects suspicious PowerShell command execution
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: "\\powershell.exe"
        CommandLine|contains:
            - "-encodedcommand"
            - "-noprofile"
            - "-windowstyle hidden"
    condition: selection
level: medium
tags:
    - attack.execution
    - attack.t1059.001
""",
    
    "file_creation": """
title: Suspicious File Creation
description: Detects creation of suspicious files
logsource:
    category: file_event
    product: windows
detection:
    selection:
        TargetFilename|endswith:
            - ".exe"
            - ".scr"
            - ".bat"
        TargetFilename|contains: "\\temp\\"
    condition: selection
level: low
tags:
    - attack.persistence
    - attack.t1547
"""
}

class BenchmarkRunner:
    """Benchmark test sınıfı"""
    
    def __init__(self):
        self.comparator = SigmaComparator()
        self.results = []
    
    def create_test_files(self):
        """Test YAML dosyalarını oluştur"""
        for name, content in TEST_RULES.items():
            filename = f"test_{name}.yml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Test dosyası oluşturuldu: {filename}")
    
    def cleanup_test_files(self):
        """Test dosyalarını temizle"""
        import os
        for name in TEST_RULES.keys():
            filename = f"test_{name}.yml"
            if os.path.exists(filename):
                os.remove(filename)
                print(f"🗑️  Test dosyası silindi: {filename}")
    
    async def run_performance_test(self, yaml_file: str, rule_counts: List[int]):
        """Performans testi çalıştır"""
        print(f"\n🚀 Performans testi başlatılıyor: {yaml_file}")
        print("="*60)
        
        performance_results = []
        
        for count in rule_counts:
            print(f"\n📊 {count} kural ile test ediliyor...")
            
            # 3 kez çalıştır ve ortalama al
            times = []
            for run in range(3):
                start_time = time.time()
                
                try:
                    results = await self.comparator.main_async(yaml_file, count, save_results=False)
                    end_time = time.time()
                    
                    elapsed = end_time - start_time
                    times.append(elapsed)
                    
                    print(f"   Run {run+1}: {elapsed:.2f}s")
                    
                except Exception as e:
                    print(f"   Run {run+1}: HATA - {e}")
                    continue
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                performance_results.append({
                    'rule_count': count,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'rules_per_second': count / avg_time
                })
                
                print(f"   ⏱️  Ortalama: {avg_time:.2f}s")
                print(f"   📈 Kural/saniye: {count/avg_time:.1f}")
        
        return performance_results
    
    def print_performance_summary(self, results: List[Dict]):
        """Performans özeti yazdır"""
        print("\n" + "="*80)
        print("🏁 PERFORMANS TEST SONUÇLARI")
        print("="*80)
        
        print(f"\n{'Kural Sayısı':<12} {'Ortalama':<12} {'Min':<10} {'Max':<10} {'Kural/sn':<12}")
        print("-" * 60)
        
        for result in results:
            print(f"{result['rule_count']:<12} "
                  f"{result['avg_time']:<12.2f} "
                  f"{result['min_time']:<10.2f} "
                  f"{result['max_time']:<10.2f} "
                  f"{result['rules_per_second']:<12.1f}")
        
        if results:
            best_throughput = max(results, key=lambda x: x['rules_per_second'])
            print(f"\n🏆 En iyi performans: {best_throughput['rules_per_second']:.1f} kural/saniye "
                  f"({best_throughput['rule_count']} kural ile)")
    
    async def run_accuracy_test(self):
        """Doğruluk testi çalıştır"""
        print("\n🎯 Doğruluk testi başlatılıyor...")
        print("="*60)
        
        self.create_test_files()
        
        try:
            # Her test dosyasını kendisiyle karşılaştır (100% benzerlik beklenir)
            for name in TEST_RULES.keys():
                filename = f"test_{name}.yml"
                print(f"\n🔍 Test ediliyor: {filename}")
                
                results = await self.comparator.main_async(filename, 5, save_results=False)
                
                if results:
                    top_result = results[0]
                    print(f"   En yüksek benzerlik: %{top_result.similarity_score * 100:.1f}")
                    print(f"   Yapısal benzerlik: %{top_result.structural_similarity * 100:.1f}")
                    print(f"   Semantik benzerlik: %{top_result.semantic_similarity * 100:.1f}")
                    
                    # Beklenen sonuçları kontrol et
                    if top_result.similarity_score > 0.7:
                        print("   ✅ BAŞARILI - Yüksek benzerlik tespit edildi")
                    else:
                        print("   ⚠️  UYARI - Düşük benzerlik skoru")
                else:
                    print("   ❌ HATA - Sonuç alınamadı")
        
        finally:
            self.cleanup_test_files()
    
    async def run_concurrent_test(self, yaml_file: str, concurrent_requests: int):
        """Eşzamanlı istek testi"""
        print(f"\n⚡ Eşzamanlı test başlatılıyor: {concurrent_requests} paralel istek")
        print("="*60)
        
        async def single_comparison():
            return await self.comparator.main_async(yaml_file, 5, save_results=False)
        
        start_time = time.time()
        
        # Eşzamanlı istekler başlat
        tasks = [single_comparison() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Sonuçları analiz et
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = concurrent_requests - successful
        
        print(f"⏱️  Toplam süre: {total_time:.2f} saniye")
        print(f"✅ Başarılı: {successful}/{concurrent_requests}")
        print(f"❌ Başarısız: {failed}/{concurrent_requests}")
        print(f"📈 İstek/saniye: {concurrent_requests/total_time:.1f}")
        
        return {
            'concurrent_requests': concurrent_requests,
            'total_time': total_time,
            'successful': successful,
            'failed': failed,
            'requests_per_second': concurrent_requests / total_time
        }

async def main_benchmark():
    """Ana benchmark fonksiyonu"""
    print("🧪 Sigma Karşılaştırıcı Benchmark Testi")
    print("="*80)
    
    runner = BenchmarkRunner()
    
    # Test dosyası oluştur
    test_yaml = "benchmark_test.yml"
    with open(test_yaml, 'w', encoding='utf-8') as f:
        f.write(TEST_RULES['web_attack'])
    
    try:
        # 1. Performans testi
        rule_counts = [5, 10, 15, 20]
        perf_results = await runner.run_performance_test(test_yaml, rule_counts)
        runner.print_performance_summary(perf_results)
        
        # 2. Doğruluk testi
        await runner.run_accuracy_test()
        
        # 3. Eşzamanlı test
        concurrent_results = []
        for concurrent in [2, 4, 6]:
            result = await runner.run_concurrent_test(test_yaml, concurrent)
            concurrent_results.append(result)
        
        # Eşzamanlı test sonuçları
        print("\n⚡ EŞZAMANLI TEST SONUÇLARI")
        print("="*60)
        print(f"{'Paralel':<8} {'Süre':<10} {'Başarılı':<10} {'İstek/sn':<12}")
        print("-" * 42)
        
        for result in concurrent_results:
            print(f"{result['concurrent_requests']:<8} "
                  f"{result['total_time']:<10.2f} "
                  f"{result['successful']:<10} "
                  f"{result['requests_per_second']:<12.1f}")
        
        print("\n🎉 Tüm testler tamamlandı!")
        
    finally:
        # Temizlik
        import os
        if os.path.exists(test_yaml):
            os.remove(test_yaml)
        
        runner.comparator.mongo_client.close()

if __name__ == "__main__":
    print("🚀 Benchmark testleri başlatılıyor...")
    print("⚠️  Not: MongoDB ve Ollama servislerinin çalıştığından emin olun!")
    
    asyncio.run(main_benchmark())