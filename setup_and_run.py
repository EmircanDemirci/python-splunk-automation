#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML Karşılaştırma Uygulaması Kurulum ve Çalıştırma Scripti
"""

import subprocess
import sys
import time
import signal
import os
from threading import Thread

def run_command(command, description):
    """Komut çalıştırır ve sonucu gösterir"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} tamamlandı")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} başarısız: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def check_service(service_name, port=None):
    """Servis durumunu kontrol eder"""
    if service_name == "mongodb":
        try:
            result = subprocess.run("systemctl is-active mongodb", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {service_name} çalışıyor")
                return True
            else:
                print(f"⚠️  {service_name} çalışmıyor, başlatılıyor...")
                return run_command("sudo systemctl start mongodb", f"{service_name} başlatma")
        except:
            print(f"⚠️  {service_name} durumu kontrol edilemedi")
            return False
    
    elif service_name == "ollama":
        try:
            result = subprocess.run("pgrep -f ollama", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {service_name} çalışıyor")
                return True
            else:
                print(f"⚠️  {service_name} çalışmıyor")
                return False
        except:
            return False

def install_system_dependencies():
    """Sistem bağımlılıklarını yükler"""
    print("\n📦 Sistem bağımlılıkları kontrol ediliyor...")
    
    # MongoDB kurulumu kontrol et
    mongodb_check = subprocess.run("which mongod", shell=True, capture_output=True)
    if mongodb_check.returncode != 0:
        print("📥 MongoDB kuruluyor...")
        commands = [
            "sudo apt update",
            "sudo apt install -y mongodb",
            "sudo systemctl enable mongodb",
            "sudo systemctl start mongodb"
        ]
        for cmd in commands:
            if not run_command(cmd, f"MongoDB kurulum: {cmd}"):
                return False
    
    # Ollama kurulumu kontrol et
    ollama_check = subprocess.run("which ollama", shell=True, capture_output=True)
    if ollama_check.returncode != 0:
        print("📥 Ollama kuruluyor...")
        if not run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Ollama kurulumu"):
            return False
    
    return True

def install_python_dependencies():
    """Python bağımlılıklarını yükler"""
    print("\n🐍 Python bağımlılıkları yükleniyor...")
    return run_command("pip install -r requirements.txt", "Python paketleri kurulumu")

def setup_ollama():
    """Ollama modelini kurar"""
    print("\n🤖 Ollama modeli kuruluyor...")
    
    # Ollama servisini başlat
    run_command("ollama serve &", "Ollama servis başlatma")
    time.sleep(5)
    
    # Llama2 modelini indir
    if run_command("ollama pull llama2", "Llama2 model indirme"):
        print("✅ Ollama modeli hazır")
        return True
    else:
        print("⚠️  Ollama modeli indirilemedi, manuel olarak 'ollama pull llama2' çalıştırın")
        return False

def test_connections():
    """Bağlantıları test eder"""
    print("\n🔍 Bağlantılar test ediliyor...")
    
    # MongoDB test
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command('ping')
        print("✅ MongoDB bağlantısı başarılı")
        mongodb_ok = True
    except Exception as e:
        print(f"❌ MongoDB bağlantısı başarısız: {e}")
        mongodb_ok = False
    
    # Ollama test
    try:
        import ollama
        models = ollama.list()
        print("✅ Ollama bağlantısı başarılı")
        ollama_ok = True
    except Exception as e:
        print(f"❌ Ollama bağlantısı başarısız: {e}")
        ollama_ok = False
    
    return mongodb_ok and ollama_ok

def run_web_app():
    """Web uygulamasını çalıştırır"""
    print("\n🚀 Web uygulaması başlatılıyor...")
    print("🌐 Uygulama http://localhost:8000 adresinde çalışacak")
    print("⏹️  Durdurmak için Ctrl+C kullanın")
    
    try:
        subprocess.run([sys.executable, "web_interface.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Uygulama durduruldu")
    except Exception as e:
        print(f"❌ Uygulama hatası: {e}")

def run_console_app():
    """Konsol uygulamasını çalıştırır"""
    print("\n💻 Konsol uygulaması başlatılıyor...")
    try:
        subprocess.run([sys.executable, "yaml_comparator.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Uygulama durduruldu")
    except Exception as e:
        print(f"❌ Uygulama hatası: {e}")

def main():
    print("🔍 YAML Karşılaştırma Uygulaması Kurulum Scripti")
    print("=" * 60)
    
    # Kurulum menüsü
    print("\nNe yapmak istiyorsunuz?")
    print("1. Tam kurulum (sistem bağımlılıkları + Python paketleri)")
    print("2. Sadece Python paketleri kur")
    print("3. Servisleri kontrol et ve test et")
    print("4. Web uygulamasını çalıştır")
    print("5. Konsol uygulamasını çalıştır")
    print("6. Çıkış")
    
    choice = input("\nSeçiminizi yapın (1-6): ").strip()
    
    if choice == "1":
        print("\n🚀 Tam kurulum başlatılıyor...")
        
        if not install_system_dependencies():
            print("❌ Sistem bağımlılıkları kurulamadı")
            return
        
        if not install_python_dependencies():
            print("❌ Python bağımlılıkları kurulamadı")
            return
        
        if not setup_ollama():
            print("⚠️  Ollama kurulumu tamamlanamadı")
        
        if test_connections():
            print("\n✅ Kurulum başarıyla tamamlandı!")
            print("🌐 Web uygulamasını çalıştırmak için: python web_interface.py")
            print("💻 Konsol uygulamasını çalıştırmak için: python yaml_comparator.py")
        else:
            print("\n⚠️  Kurulum tamamlandı ama bazı servisler çalışmıyor")
    
    elif choice == "2":
        install_python_dependencies()
    
    elif choice == "3":
        print("\n🔍 Servisler kontrol ediliyor...")
        check_service("mongodb")
        check_service("ollama")
        test_connections()
    
    elif choice == "4":
        if test_connections():
            run_web_app()
        else:
            print("❌ Servisler hazır değil, önce kurulum yapın")
    
    elif choice == "5":
        if test_connections():
            run_console_app()
        else:
            print("❌ Servisler hazır değil, önce kurulum yapın")
    
    elif choice == "6":
        print("👋 Görüşmek üzere!")
    
    else:
        print("❌ Geçersiz seçim!")

if __name__ == "__main__":
    main()