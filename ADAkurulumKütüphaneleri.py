
import subprocess
import sys
import importlib.util
import os
import platform

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_python_version():
    print(f"🐍 Python Sürümü: {sys.version.split()[0]}")
    if sys.version_info < (3, 9):
        print("⚠️ UYARI: Bu proje Python 3.9 veya üstü ile daha stabil çalışır.")
    print("-" * 50)

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def install(package, import_name=None):
    if import_name is None:
        import_name = package

    # Paket adını temizle (versiyon bilgisini kaldır)
    clean_package_name = package.split('==')[0].split('>=')[0].split('<=')[0]
    
    # Bazı paketlerin import adı farklı olabilir
    special_imports = {
        "SpeechRecognition": "speech_recognition",
        "opencv-python": "cv2",
        "beautifulsoup4": "bs4",
        "google-generativeai": "google.generativeai",
        "Pillow": "PIL",
        "pycaw": "pycaw",
        "comtypes": "comtypes",
        "gTTS": "gtts"
    }
    
    check_name = special_imports.get(clean_package_name, import_name)
    
    try:
        spec = importlib.util.find_spec(check_name)
        if spec is not None:
            print(f"✅ {clean_package_name} zaten yüklü.")
            return True
    except ImportError:
        pass
    except ModuleNotFoundError:
        pass

    print(f"⏳ {package} yükleniyor...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} başarıyla yüklendi.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} yüklenirken hata oluştu!")
        print(f"   Hata kodu: {e.returncode}")
        return False

def main():
    clear_screen()
    print("🚀 ADA Asistan Kurulum Sihirbazı")
    print("================================")
    
    check_python_version()
    
    # Gerekli kütüphaneler listesi
    libraries = [
        "requests",           # HTTP istekleri
        "SpeechRecognition",  # Ses tanıma
        "pyaudio",           # Mikrofon erişimi
        "pygame",            # Ses çalma
        "google-generativeai",# Gemini AI
        "opencv-python",     # Kamera/Görüntü
        "keyboard",          # Klavye kısayolları
        "beautifulsoup4",    # Web scraping
        "Pillow",            # Resim işleme
        "pycaw",             # Windows ses kontrolü
        "comtypes",          # Windows COM arayüzü
        "TTS",               # Coqui TTS (Ses sentezi)
    ]
    
    success_count = 0
    fail_count = 0
    
    print("📦 Kütüphaneler kontrol ediliyor ve eksikler yükleniyor...\n")
    
    for lib in libraries:
        if install(lib):
            success_count += 1
        else:
            fail_count += 1
            
    print("\n" + "=" * 50)
    print("📊 Kurulum Özeti:")
    print(f"✅ Başarılı: {success_count}")
    
    if fail_count > 0:
        print(f"❌ Başarısız: {fail_count}")
        print("\n⚠️ Olası Çözümler:")
        print("1. 'pyaudio' hatasında: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio adresinden uygun .whl dosyasını indirip kurun.")
        print("2. 'TTS' hatasında: C++ Build Tools'un yüklü olduğundan emin olun.")
        print("3. Yönetici olarak çalıştırmayı deneyin.")
    else:
        print("🎉 Tüm kütüphaneler başarıyla kuruldu!")
        print("🚀 Artık 'python asistan_complete.py' komutu ile asistanı başlatabilirsiniz.")

    input("\nÇıkmak için Enter'a basın...")

if __name__ == "__main__":
    # Eğer pip güncel değilse uyarı verebilir, önce pip'i güncelleyelim
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except:
        pass
        
    main()