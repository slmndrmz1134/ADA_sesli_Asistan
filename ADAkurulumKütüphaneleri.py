import os
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
    """Check and setup pip with proper error handling"""
    try:
        import pip
        print("✅ pip already installed")
        return True
    except ImportError:
        print("❌ pip not installed, installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            print("✅ pip successfully installed")
            return True
        except Exception as e:
            print(f"❌ pip installation error: {e}")
            print("💡 Please run as administrator or use: python -m pip install --user")
            return True  # Continue anyway, pip might still work

def kutuphane_yukle(paketler):
    """Install packages with better error handling"""
    for paket in paketler:
        try:
            __import__(paket.split('==')[0])
            print(f"✅ {paket} already installed")
        except ImportError:
            print(f"❌ {paket} not installed, installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", paket])
                print(f"✅ {paket} successfully installed")
            except Exception as e:
                print(f"❌ {paket} installation error: {e}")
                # Try with --user flag for permission issues
                try:
                    print(f"🔄 Trying with --user flag for {paket}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", paket])
                    print(f"✅ {paket} installed with --user flag")
                except Exception as e2:
                    print(f"❌ {paket} failed with --user: {e2}")

def windows_ozel_yuklemeler():
    """Windows özel yüklemeleri - iyileştirilmiş sürüm"""
    if platform.system() == "Windows":
        print("\n💻 Windows özel yüklemeleri:")
        try:
            # PyAudio için ön koşullar
            print("🔊 PyAudio kurulumu kontrol ediliyor...")
            try:
                import pyaudio
                print("✅ PyAudio zaten yüklü")
            except ImportError:
                print("❌ PyAudio yüklü değil, yükleme denemeleri başlıyor...")
                
                # Önce pip ile dene
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
                    print("✅ PyAudio pip ile yüklendi")
                except:
                    print("⚠️ pip ile başarısız, pipwin deneniyor...")
                    try:
                        # pipwin yükle ve kullan
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
                        os.system('pipwin install pyaudio')
                        print("✅ PyAudio pipwin ile yüklendi")
                    except Exception as e:
                        print(f"❌ PyAudio yükleme hatası: {e}")
                        print("💡 Manuel kurulum gerekebilir: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
            
            # PyCaw için gerekli comtypes
            print("🔊 comtypes (PyCaw için) kurulumu...")
            kutuphane_yukle(['comtypes'])
            
            # pycaw kurulumu
            print("🔊 pycaw (Windows ses kontrolü) kurulumu...")
            kutuphane_yukle(['pycaw'])
            
        except Exception as e:
            print(f"❌ Windows özel yüklemelerinde hata: {e}")
    else:
        print("💻 Windows dışı sistem tespit edildi, Windows özel yüklemeler atlanıyor.")

def gerekli_kutuphaneler():
    """asistan_complete.py dosyasındaki tüm kütüphaneleri döndürür"""
    return [
        # Temel Python kütüphaneleri (built-in, yükleme gerekmez)
        # 'random', 'time', 'os', 'json', 'datetime', 're', 'threading', 
        # 'queue', 'ctypes', 'subprocess', 'asyncio', 'tempfile', 'wave', 
        # 'atexit', 'sys', 'platform'
        
        # Ses tanıma ve işleme
        'speechrecognition',
        'pyaudio',
        
        # Google AI/Gemini
        'google-generativeai',
        
        # Web scraping ve HTTP istekleri
        'requests',
        'beautifulsoup4',
        
        # Görüntü işleme
        'opencv-python',
        'pillow',
        
        # Ses çıkışı ve TTS
        'TTS',  # Coqui TTS
        'pygame',
        
        # Windows sistem kontrolü
        'pycaw',  # Windows ses kontrolü
        
        # GUI
        'tkinter',  # Built-in olabilir ama bazı sistemlerde ayrı
        
        # Global hotkey kontrolü
        'keyboard',
        
        # PyTorch (TTS için gerekli)
        'torch',
        'torchaudio',
        
        # Ek yardımcı kütüphaneler
        'python-dotenv',
        'comtypes',  # Windows COM işlemleri için
        'pipwin'     # Windows binary paketleri için
    ]

def asistan_complete_kutuphaneleri_yukle():
    """Install all libraries from asistan_complete.py automatically"""
    print("\n" + "="*60)
    print("🤖 ADA ASSISTANT COMPLETE - LIBRARY INSTALLATION")
    print("="*60)
    print("📦 Installing all libraries from asistan_complete.py...")
    print("="*60 + "\n")
    
    # Update pip first
    print("🔄 Updating pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip successfully updated")
    except Exception as e:
        print(f"⚠️ Error updating pip: {e}")
        try:
            print("🔄 Trying pip update with --user flag...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "pip"])
            print("✅ pip updated with --user flag")
        except Exception as e2:
            print(f"⚠️ pip update failed: {e2} - continuing anyway...")
    
    # Install PyTorch first (required for TTS)
    print("\n🔥 Installing PyTorch (required for TTS)...")
    pytorch_yukle()
    
    # Install basic libraries
    print("\n📚 Installing basic libraries...")
    kutuphane_yukle(gerekli_kutuphaneler())
    
    # Windows-specific installations
    windows_ozel_yuklemeler()
    
    # Special installations
    ozel_kurulumlar()
    
    # Verify installation
    print("\n🔍 Verifying installation...")
    if asistan_complete_kontrol():
        print("\n" + "="*60)
        print("✅ ALL LIBRARIES SUCCESSFULLY INSTALLED!")
        print("🤖 ADA Assistant Complete is ready to run.")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print("❌ SOME LIBRARIES COULD NOT BE INSTALLED!")
        print("🔧 Please fix the errors and try again.")
        print("="*60)
        return False

def pytorch_yukle():
    """Install PyTorch CPU version"""
    try:
        import torch
        print("✅ PyTorch already installed")
    except ImportError:
        print("❌ PyTorch not installed, installing...")
        try:
            # For CPU version
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torch", "torchaudio", "--index-url", 
                "https://download.pytorch.org/whl/cpu"
            ])
            print("✅ PyTorch successfully installed")
        except Exception as e:
            print(f"❌ PyTorch installation error: {e}")
            print("🔄 Trying alternative method...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
                print("✅ PyTorch installed with alternative method")
            except Exception as e2:
                print(f"❌ PyTorch alternative installation error: {e2}")

def ozel_kurulumlar():
    """Özel kurulum gerektiren kütüphaneler"""
    print("\n🔧 Özel kurulumlar yapılıyor...")
    
    # pipwin ile Windows binary paketleri
    if platform.system() == "Windows":
        try:
            print("📦 pipwin ile Windows paketleri yükleniyor...")
            
            # pipwin'i yükle
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
            
            # PyAudio'yu pipwin ile yükle
            try:
                import pyaudio
                print("✅ PyAudio zaten yüklü")
            except ImportError:
                print("❌ PyAudio yüklü değil, pipwin ile yükleniyor...")
                try:
                    os.system('pipwin install pyaudio')
                    print("✅ PyAudio pipwin ile yüklendi")
                except:
                    print("⚠️ pipwin ile PyAudio yüklenemedi, pip ile deneniyor...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
                    
        except Exception as e:
            print(f"❌ Özel kurulum hatası: {e}")
    
    # TTS modellerini kontrol et
    tts_modelleri_kontrol()

def tts_modelleri_kontrol():
    """TTS modellerinin indirilip indirilmediğini kontrol et"""
    try:
        print("🔊 TTS modelleri kontrol ediliyor...")
        from TTS.api import TTS
        
        # Türkçe model dene
        try:
            print("🇹🇷 Türkçe TTS modeli kontrol ediliyor...")
            tts = TTS(model_name="tts_models/tr/common-voice/glow-tts")
            print("✅ Türkçe TTS modeli hazır")
        except:
            print("⚠️ Türkçe TTS modeli yüklenemedi")
            try:
                print("🇺🇸 İngilizce TTS modeli kontrol ediliyor...")
                tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
                print("✅ İngilizce TTS modeli hazır")
            except Exception as e:
                print(f"❌ TTS model hatası: {e}")
                
    except Exception as e:
        print(f"❌ TTS kontrol hatası: {e}")

def asistan_complete_kontrol():
    """asistan_complete.py dosyasındaki tüm kütüphaneleri test et"""
    try:
        print("📋 Kütüphane testi başlıyor...")
        
        # Temel kütüphaneleri test et
        test_kutuphaneleri = [
            ('speech_recognition', 'Ses tanıma'),
            ('google.generativeai', 'Google Gemini AI'),
            ('cv2', 'OpenCV'),
            ('pygame', 'Pygame'),
            ('requests', 'HTTP istekleri'),
            ('bs4', 'BeautifulSoup'),
            ('keyboard', 'Global hotkey'),
            ('tkinter', 'GUI'),
        ]
        
        for kutuphane, aciklama in test_kutuphaneleri:
            try:
                __import__(kutuphane)
                print(f"✅ {aciklama} - OK")
            except ImportError as e:
                print(f"❌ {aciklama} - HATA: {e}")
                return False
        
        # TTS testi
        try:
            from TTS.api import TTS
            print("✅ Coqui TTS - OK")
        except ImportError as e:
            print(f"❌ Coqui TTS - HATA: {e}")
            return False
        
        # Windows özel kütüphaneleri (sadece Windows'ta)
        if platform.system() == "Windows":
            try:
                from pycaw.pycaw import AudioUtilities
                print("✅ Windows ses kontrolü (pycaw) - OK")
            except ImportError as e:
                print(f"⚠️ Windows ses kontrolü (pycaw) - HATA: {e}")
                print("💡 Bu kütüphane olmadan da çalışır, ancak ses kontrolü çalışmaz")
        
        # PyTorch testi
        try:
            import torch
            print(f"✅ PyTorch {torch.__version__} - OK")
        except ImportError as e:
            print(f"❌ PyTorch - HATA: {e}")
            return False
        
        print("\n🎉 Tüm temel kütüphaneler başarıyla test edildi!")
        return True
        
    except Exception as e:
        print(f"❌ Kütüphane testinde genel hata: {e}")
        return False

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
    #          ADA ASSISTANT SETUP             #
    #   Installing ALL required libraries      #
    #############################################
    """)
    
    sistem_bilgisi()
    
    if not pip_kontrol():
        input("pip could not be installed. Please install pip manually and try again. Press Enter to exit...")
        return
    
    print("\n🚀 Starting complete ADA Assistant library installation...")
    print("📦 This will install ALL libraries needed for full functionality")
    print("⏳ Please wait, this may take several minutes...\n")
    
    # Install everything automatically
    print("🔧 Installing basic libraries...")
    kutuphane_yukle([
        'speechrecognition',
        'pyaudio', 
        'google-generativeai',
        'pillow',
        'opencv-python',
        'pygame',
        'requests',
        'beautifulsoup4'
    ])
    
    print("\n🚀 Installing complete ADA Assistant libraries...")
    # Install complete version libraries
    asistan_complete_kutuphaneleri_yukle()
    
    print("\n📖 Usage Information:")
    print("• For basic version: python asistan.py")
    print("• For complete version: python asistan_complete.py")
    print("• Get your API key from: https://makersuite.google.com/app/apikey")
    print("\n✅ Installation completed! You can now run ADA Assistant.")
    
    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()