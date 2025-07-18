#!/usr/bin/env python3
"""
Enhanced Sigma Rule Analysis Runner
Bu script Sigma kurallarını MongoDB veritabanındaki kurallarla karşılaştırır 
ve Ollama AI ile detaylı analiz yapar.
"""

import json
import os
import datetime
from pathlib import Path
from enhanced_sigma_comparator import EnhancedSigmaRuleComparator
from mongodb_connection import MongoConnector
import logging

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalysisRunner:
    def __init__(self, mongo_connection_string, database_name="sigmaDB", collection_name="rules"):
        self.mongo_connection_string = mongo_connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.results_dir = Path("analysis_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_analysis(self, yaml_file_path, top_n=10, save_results=True, ollama_url="http://localhost:11434", model_name="deepseek-r1:8b"):
        """
        Tam analiz sürecini çalıştır
        
        Args:
            yaml_file_path: Analiz edilecek YAML dosya yolu
            top_n: En benzer kaç kural getirileceği
            save_results: Sonuçların dosyaya kaydedilip kaydedilmeyeceği
            ollama_url: Ollama API URL'si
            model_name: Kullanılacak AI model adı
        """
        
        print("🚀 ENHANCED SIGMA RULE ANALYSIS BAŞLATILIYOR")
        print("=" * 60)
        
        try:
            # MongoDB bağlantısı
            print("📡 MongoDB'ye bağlanılıyor...")
            connect_mongo = MongoConnector(self.mongo_connection_string, self.database_name, self.collection_name)
            collection = connect_mongo.connect()
            
            # Comparator'ı başlat
            print("🔧 AI Comparator başlatılıyor...")
            comparator = EnhancedSigmaRuleComparator(
                collection=collection,
                ollama_url=ollama_url,
                model_name=model_name
            )
            
            # Ollama bağlantısını test et
            print("🤖 Ollama AI bağlantısı test ediliyor...")
            if not comparator.test_ollama_connection():
                print("⚠️ Ollama bağlantısı başarısız! AI analizi olmadan devam ediliyor.")
            
            # Ana analizi çalıştır
            print(f"\n📄 YAML dosyası analiz ediliyor: {yaml_file_path}")
            results = comparator.compare_with_mongodb_and_analyze(yaml_file_path, top_n)
            
            # Sonuçları kaydet
            if save_results:
                self._save_results(results, yaml_file_path)
            
            # Özet rapor
            self._print_summary_report(results)
            
            # Bağlantıyı kapat
            connect_mongo.close()
            
            return results
            
        except FileNotFoundError as e:
            logger.error(f"❌ Dosya bulunamadı: {e}")
            return None
        except ConnectionError as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Beklenmeyen hata: {e}")
            logger.exception("Detaylı hata bilgisi:")
            return None
    
    def _save_results(self, results, yaml_file_path):
        """Analiz sonuçlarını dosyaya kaydet"""
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        yaml_name = Path(yaml_file_path).stem
        
        # JSON formatında detaylı sonuçlar
        json_file = self.results_dir / f"{yaml_name}_analysis_{timestamp}.json"
        
        # AI analizini ayrı tutarak JSON serializable hale getir
        save_data = {
            "analysis_timestamp": timestamp,
            "yaml_file": yaml_file_path,
            "yaml_rule": results["yaml_rule"],
            "yaml_fields": results["yaml_fields"],
            "yaml_values": results["yaml_values"],
            "total_rules_analyzed": results["total_rules_analyzed"],
            "similar_rules_found": results["similar_rules_found"],
            "top_matches": [
                {
                    "index": match["index"],
                    "rule_id": match["rule_id"],
                    "title": match["title"],
                    "field_similarity": match["field_similarity"],
                    "value_similarity": match["value_similarity"],
                    "weighted_similarity": match["weighted_similarity"],
                    "mongo_fields": match["mongo_fields"],
                    "mongo_values": match["mongo_values"]
                }
                for match in results["top_matches"]
            ],
            "ai_analysis": {
                "success": results["ai_analysis"]["success"],
                "error": results["ai_analysis"].get("error"),
                "analyzed_rules_count": results["ai_analysis"].get("analyzed_rules_count"),
                "analysis_text": results["ai_analysis"].get("analysis")
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        # Markdown formatında okunabilir rapor
        md_file = self.results_dir / f"{yaml_name}_report_{timestamp}.md"
        self._create_markdown_report(save_data, md_file)
        
        print(f"\n💾 SONUÇLAR KAYDEDİLDİ:")
        print(f"   📄 JSON Detayları: {json_file}")
        print(f"   📋 Markdown Rapor: {md_file}")
    
    def _create_markdown_report(self, data, output_file):
        """Markdown formatında analiz raporu oluştur"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Sigma Rule Analysis Report\n\n")
            f.write(f"**Analysis Date:** {data['analysis_timestamp']}\n\n")
            f.write(f"**Source YAML:** `{data['yaml_file']}`\n\n")
            
            # YAML kural özeti
            yaml_rule = data['yaml_rule']
            f.write(f"## Analyzed Rule\n\n")
            f.write(f"**Title:** {yaml_rule.get('title', 'Untitled')}\n\n")
            f.write(f"**Description:** {yaml_rule.get('description', 'No description')}\n\n")
            f.write(f"**Level:** {yaml_rule.get('level', 'Unknown')}\n\n")
            
            # İstatistikler
            f.write(f"## Analysis Statistics\n\n")
            f.write(f"- **Total Rules in Database:** {data['total_rules_analyzed']}\n")
            f.write(f"- **Similar Rules Found (>50%):** {data['similar_rules_found']}\n")
            f.write(f"- **Top Matches Analyzed:** {len(data['top_matches'])}\n\n")
            
            # Çıkarılan field ve value'lar
            f.write(f"## Extracted Components\n\n")
            f.write(f"**Fields:** {', '.join(data['yaml_fields'])}\n\n")
            f.write(f"**Values:** {', '.join(data['yaml_values'][:10])}{'...' if len(data['yaml_values']) > 10 else ''}\n\n")
            
            # En benzer kurallar
            f.write(f"## Top Similar Rules\n\n")
            for i, match in enumerate(data['top_matches'], 1):
                f.write(f"### {i}. {match['title']}\n\n")
                f.write(f"- **Rule ID:** `{match['rule_id']}`\n")
                f.write(f"- **Total Similarity:** {match['weighted_similarity']:.1%}\n")
                f.write(f"- **Value Similarity:** {match['value_similarity']:.1%}\n")
                f.write(f"- **Field Similarity:** {match['field_similarity']:.1%}\n\n")
            
            # AI Analizi
            ai_analysis = data['ai_analysis']
            f.write(f"## AI Analysis\n\n")
            if ai_analysis['success']:
                f.write(f"**Status:** ✅ Successful\n\n")
                f.write(f"**Rules Analyzed by AI:** {ai_analysis['analyzed_rules_count']}\n\n")
                f.write(f"### AI Analysis Results\n\n")
                f.write(f"```\n{ai_analysis['analysis_text']}\n```\n\n")
            else:
                f.write(f"**Status:** ❌ Failed\n\n")
                f.write(f"**Error:** {ai_analysis['error']}\n\n")
    
    def _print_summary_report(self, results):
        """Özet raporu terminale yazdır"""
        
        print("\n" + "="*80)
        print("📊 ANALYSIS SUMMARY REPORT")
        print("="*80)
        
        if results["top_matches"]:
            print(f"✅ Analysis completed successfully!")
            print(f"📁 Total rules in database: {results['total_rules_analyzed']}")
            print(f"🔍 Similar rules found (>50%): {results['similar_rules_found']}")
            print(f"🏆 Highest similarity: {results['top_matches'][0]['weighted_similarity']:.1%}")
            print(f"📊 Top matches analyzed: {len(results['top_matches'])}")
            
            # En benzer kuralın detayları
            best_match = results['top_matches'][0]
            print(f"\n🥇 BEST MATCH:")
            print(f"   Title: {best_match['title']}")
            print(f"   ID: {best_match['rule_id']}")
            print(f"   Similarity: {best_match['weighted_similarity']:.1%}")
            
            # AI analizi durumu
            ai_status = "✅ Successful" if results['ai_analysis']['success'] else "❌ Failed"
            print(f"🤖 AI Analysis: {ai_status}")
            
            if results['ai_analysis']['success']:
                print(f"   AI analyzed {results['ai_analysis']['analyzed_rules_count']} rules")
                
        else:
            print("❌ No similar rules found in the database!")
        
        print("="*80)
    
    def batch_analysis(self, yaml_files_dir, pattern="*.yml"):
        """Bir dizindeki birden fazla YAML dosyasını toplu analiz et"""
        
        yaml_files = list(Path(yaml_files_dir).glob(pattern))
        
        if not yaml_files:
            print(f"❌ {yaml_files_dir} dizininde {pattern} desenine uygun dosya bulunamadı!")
            return
        
        print(f"🔄 BATCH ANALYSIS: {len(yaml_files)} dosya analiz edilecek")
        print("-" * 60)
        
        results_summary = []
        
        for i, yaml_file in enumerate(yaml_files, 1):
            print(f"\n[{i}/{len(yaml_files)}] Analyzing: {yaml_file.name}")
            
            try:
                result = self.run_analysis(str(yaml_file), save_results=True)
                if result:
                    results_summary.append({
                        "file": yaml_file.name,
                        "status": "success",
                        "similar_rules": result["similar_rules_found"],
                        "best_similarity": result["top_matches"][0]["weighted_similarity"] if result["top_matches"] else 0.0
                    })
                else:
                    results_summary.append({
                        "file": yaml_file.name,
                        "status": "failed",
                        "similar_rules": 0,
                        "best_similarity": 0.0
                    })
            except Exception as e:
                logger.error(f"Dosya {yaml_file.name} analiz edilirken hata: {e}")
                results_summary.append({
                    "file": yaml_file.name,
                    "status": "error",
                    "similar_rules": 0,
                    "best_similarity": 0.0
                })
        
        # Batch özeti
        print("\n" + "="*80)
        print("📊 BATCH ANALYSIS SUMMARY")
        print("="*80)
        
        successful = len([r for r in results_summary if r["status"] == "success"])
        print(f"✅ Successful analyses: {successful}/{len(yaml_files)}")
        
        for result in results_summary:
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {result['file']}: {result['similar_rules']} similar rules, best: {result['best_similarity']:.1%}")

def main():
    """Ana fonksiyon - örnek kullanım"""
    
    # Konfigürasyon
    MONGO_CONNECTION = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    YAML_FILE = "deneme_kural.yml"
    OLLAMA_URL = "http://localhost:11434"
    MODEL_NAME = "deepseek-r1:8b"
    
    # Runner'ı başlat
    runner = AnalysisRunner(MONGO_CONNECTION)
    
    # Tek dosya analizi
    print("🎯 Single file analysis starting...")
    results = runner.run_analysis(
        yaml_file_path=YAML_FILE,
        top_n=10,
        save_results=True,
        ollama_url=OLLAMA_URL,
        model_name=MODEL_NAME
    )
    
    if results:
        print("✅ Analysis completed successfully!")
    else:
        print("❌ Analysis failed!")

if __name__ == "__main__":
    main()