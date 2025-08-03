import os
import sys
import subprocess
import platform

def sistem_bilgisi():
    print("\n" + "="*50)
    print("Sistem Bilgisi")
    print("="*50)
    print(f"İşletim Sistemi: {platform.system()}")
    print(f"Sürüm: {platform.release()}")
    print(f"Python Sürümü: {platform.python_version()}")
    print("="*50 + "\n")

def pip_kontrol():
    try:
        import pip
        print("✅ pip zaten yüklü")
        return True
    except ImportError:
        print("❌ pip yüklü değil, yükleniyor...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            print("✅ pip başarıyla yüklendi")
            return True
        except Exception as e:
            print(f"❌ pip yükleme hatası: {e}")
            return False

def kutuphane_yukle(paketler):
    for paket in paketler:
        try:
            __import__(paket.split('==')[0])
            print(f"✅ {paket} zaten yüklü")
        except ImportError:
            print(f"❌ {paket} yüklü değil, yükleniyor...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", paket])
                print(f"✅ {paket} başarıyla yüklendi")
            except Exception as e:
                print(f"❌ {paket} yükleme hatası: {e}")

def windows_ozel_yuklemeler():
    if platform.system() == "Windows":
        print("\nWindows özel yüklemeleri:")
        try:
            # PyAudio için ön koşullar
            os.system('pip install pipwin')
            os.system('pipwin install pyaudio')
            print("✅ PyAudio başarıyla yüklendi (pipwin ile)")
            
            # PyCaw için gerekli
            kutuphane_yukle(['comtypes'])
        except Exception as e:
            print(f"❌ Windows özel yüklemelerinde hata: {e}")

def gerekli_kutuphaneler():
    return [
        'speechrecognition',
        'pyaudio',
        'google-generativeai',
        'pillow',
        'opencv-python',
        'pyautogui',
        'pycaw',
        'pygame',
        'tts',
        'requests',
        'beautifulsoup4',
        'python-dotenv'
    ]

def asistan_kontrol():
    try:
        # Temel kütüphaneleri test et
        import speech_recognition as sr
        import google.generativeai as genai
        import cv2
        import pygame
        from TTS.api import TTS
        
        print("\n" + "="*50)
        print("✅ Tüm kütüphaneler başarıyla yüklendi!")
        print("="*50)
        return True
    except Exception as e:
        print("\n" + "="*50)
        print(f"❌ Kütüphane testinde hata: {e}")
        print("="*50)
        return False

def main():
    print("""
    #############################################
    #          ADA ASİSTAN KURULUMU             #
    #  Tüm gerekli kütüphaneler yüklenecek      #
    #############################################
    """)
    
    sistem_bilgisi()
    
    if not pip_kontrol():
        input("pip yüklenemedi. Lütfen manuel olarak pip yükleyin ve tekrar deneyin. Çıkmak için Enter'a basın...")
        return
    
    # Temel kütüphaneleri yükle
    kutuphane_yukle(gerekli_kutuphaneler())
    
    # Windows'a özel yüklemeler
    windows_ozel_yuklemeler()
    
    # Kurulumu doğrula
    if asistan_kontrol():
        print("\nKurulum tamamlandı! Artık ADA Asistan'ı kullanabilirsiniz.")
        print("Ana programı çalıştırmak için 'python ada_asistan.py' komutunu kullanın.")
    else:
        print("\nKurulum sırasında hatalar oluştu. Lütfen hataları düzeltip tekrar deneyin.")
    
    input("\nKapatmak için Enter'a basın...")

if __name__ == "__main__":
    main()