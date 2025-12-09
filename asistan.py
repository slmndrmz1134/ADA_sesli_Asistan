# -*- coding: utf-8 -*-
import random
import time
import speech_recognition as sr
import pyaudio
import os
import json
import requests
from bs4 import BeautifulSoup
import cv2
import google.generativeai as genai
from datetime import datetime
import re
import threading
from queue import Queue, Empty
import ctypes
from ctypes import wintypes
import subprocess
import asyncio
import tkinter as tk
from tkinter import ttk
import webbrowser
from TTS.api import TTS
import torch
import tempfile
import pygame
import wave
import atexit
import keyboard
import sys

# Yönetici izni kontrolü ve yükseltme fonksiyonu
def is_admin():
    """Yönetici izni var mı kontrol et"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Yönetici izniyle programı yeniden başlat"""
    if is_admin():
        print("Yönetici izni ile çalışıyor")
        return True
    else:
        print("Yönetici izni gerekiyor. Program yönetici olarak yeniden başlatılıyor...")
        try:
            # Mevcut Python script'ini yönetici olarak çalıştır
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(sys.argv),
                None,
                1
            )
            
            # ShellExecuteW başarılı olursa (>32), mevcut programı kapat
            if result > 32:
                print("Yönetici programı başlatıldı, mevcut program kapatılıyor...")
                sys.exit(0)
            else:
                print(f"Yönetici izni reddedildi veya hata oluştu (kod: {result})")
                return False
    
        except Exception as e:
            print(f"Yönetici izni alınamadı: {e}")
            input("Devam etmek için Enter'a basın...")
            return False

# Konfigürasyon
GEMINI_API_KEY = ""  # API anahtarı çalışma zamanında alınacak
FOTO_KLASORU = r"C:\Users\SELMAN\OneDrive\Pictures\Camera Roll"

# Gemini modeli daha sonra yapılandırılacak
model = None

# Windows medya tuşları
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD

# Parlaklık kontrolü için varsayılan değer
DEFAULT_BRIGHTNESS = 50

class GelismisADA:

    def gemini_ile_komut_isle(self, komut):
        """Gemini 2.0 Flash-lite ile akıllı komut işleme"""
        try:
            prompt = f"""Sen ADA adında Türkçe konuşan bir sesli asistansın. Kullanıcının sorusunu veya komutunu dostça ve profesyonel bir şekilde yanıtla.'''

Kullanıcı: {komut}
ADA: """
            
            print(f"🤖 Gemini'ye gönderilen prompt: {prompt}")
            
            response = model.generate_content(prompt)
            
            if response.text:
                yanit = response.text
                print(f"🤖 Gemini yanıtı: {yanit}")
                
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                
                if "web sitesi aç" in yanit.lower():
                    site = yanit.split("web sitesi aç")[-1].strip()
                    if site:
                        webbrowser.open(f"https://{site}")
            else:
                yanit = "Üzgünüm, bir yanıt oluşturamadım. Lütfen tekrar deneyin."
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
        except Exception as e:
            print(f"❌ Gemini hatası: {e}")
            yanit = "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
    def __init__(self, api_key):
        global model, GEMINI_API_KEY
        
        # API anahtarını ayarla
        GEMINI_API_KEY = api_key
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Gerekli klasörleri oluştur
        self.klasorleri_olustur()
        
        # Ses tanıma ayarları
        self.r = sr.Recognizer()
        self.r.energy_threshold = 4000
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8
        
        # Coqui TTS motoru başlat
        self.tts_engine = None
        self.tts_baslat()
        
        # pygame ses çalma için
        pygame.mixer.init()
        
        # GUI ayarları
        self.gui_root = None
        self.gui_label = None
        self.gui_thread = None
        self.gui_aktif = False
        
        # Durum değişkenleri
        self.aktif_mod = False
        self.dinleme_aktif = False
        self.mikrofon = None
        self.aktif_mod_zamanlayici = None
        self.son_komut_zamani = 0
        self.hotkey_aktif = False
        self.aktif_mod_timeout = 5  # 5 saniye timeout
        
        # Uyanma kelimeleri
        self.uyanma_kelimeleri = [
            "hey",
            "ada",
            "hey ada",
            "ok",
            "okey",
            "baksana"
        ]
        
        # Windows ses API'si için gerekli kütüphaneler
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            self.ses_kontrol_mevcut = True
            print("✅ Windows ses kontrolü aktif")
        except ImportError:
            self.ses_kontrol_mevcut = False
            print("❌ pycaw yüklü değil. 'pip install pycaw' çalıştırın")
        
        # Global hotkey ayarları
        self.hotkey_kurulumu()
        
        print("🎤 ADA Asistan başlatılıyor...")
        print("⌨️  Ctrl+Shift tuşu ile aktif moda geçebilirsiniz")

    def klasorleri_olustur(self):
        """Gerekli klasörleri oluştur"""
        try:
            if not os.path.exists(FOTO_KLASORU):
                os.makedirs(FOTO_KLASORU)
                print(f"✅ Fotoğraf klasörü oluşturuldu: {FOTO_KLASORU}")
            
            # Temp ses dosyası klasörü
            self.temp_ses_klasoru = os.path.join(tempfile.gettempdir(), "ada_tts")
            if not os.path.exists(self.temp_ses_klasoru):
                os.makedirs(self.temp_ses_klasoru)
                
        except Exception as e:
            print(f"❌ Klasör oluşturma hatası: {e}")

    def tts_baslat(self):
        """Coqui TTS motorunu başlat"""
        try:
            print("🔊 Coqui TTS başlatılıyor...")
            
            # Coqui TTS modelini yükle (Türkçe destekli model)
            self.tts_engine = TTS(model_name="tts_models/tr/common-voice/glow-tts")
            print("✅ Coqui TTS hazır")
            
        except Exception as e:
            print(f"❌ TTS hatası: {e}")
            try:
                print("🔄 Alternatif TTS modeli deneniyor...")
                self.tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
                print("✅ İngilizce TTS hazır")
            except Exception as e2:
                print(f"❌ Alternatif TTS hatası: {e2}")
                print("🔧 Lütfen şu komutu çalıştırın: pip install TTS")
                self.tts_engine = None

    def seslendirme(self, metin):
        """Coqui TTS ile seslendirme sistemi"""
        print(f"🔊 ADA: {metin}")
        
        if not self.tts_engine:
            print("❌ TTS motoru yok, sadece metin gösteriliyor")
            return
            
        try:
            # Geçici ses dosyası oluştur
            ses_dosyasi = os.path.join(self.temp_ses_klasoru, f"ada_tts_{int(time.time())}.wav")
            
            # TTS ile ses dosyası oluştur
            print(f"🎵 TTS dosyası oluşturuluyor: {ses_dosyasi}")
            self.tts_engine.tts_to_file(text=metin, file_path=ses_dosyasi)
            
            # Dosyanın oluştuğunu kontrol et
            if os.path.exists(ses_dosyasi):
                print("✅ TTS dosyası oluşturuldu")
                
                # pygame ile ses dosyasını çal
                pygame.mixer.music.load(ses_dosyasi)
                pygame.mixer.music.play()
                print("🎵 Ses çalınıyor...")
                
                # Çalma bitene kadar bekle
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                print("✅ Ses çalma tamamlandı")
                
                # Geçici dosyayı sil
                try:
                    os.remove(ses_dosyasi)
                except:
                    pass
            else:
                print("❌ TTS dosyası oluşturulamadı")
                
        except Exception as e:
            print(f"❌ Ses çıkışı hatası: {e}")
            print(f"❌ Hata detayı: {type(e).__name__}")

    def gui_baslat(self):
        """GUI thread'ini başlat"""
        if not self.gui_aktif:
            self.gui_thread = threading.Thread(target=self.gui_olustur, daemon=True)
            self.gui_thread.start()
            self.gui_aktif = True

    def gui_olustur(self):
        """Sağ üst köşede GUI oluştur"""
        try:
            self.gui_root = tk.Tk()
            self.gui_root.title("ADA Asistan")
            
            # Pencere boyutları ve konumu
            pencere_genislik = 400
            pencere_yukseklik = 200
            ekran_genislik = self.gui_root.winfo_screenwidth()
            
            # Sağ üst köşeye yerleştir
            x = ekran_genislik - pencere_genislik - 50
            y = 50
            
            self.gui_root.geometry(f"{pencere_genislik}x{pencere_yukseklik}+{x}+{y}")
            self.gui_root.attributes("-topmost", True)  # Her zaman üstte
            self.gui_root.configure(bg='#2c3e50')
            
            # Ana frame
            main_frame = tk.Frame(self.gui_root, bg='#2c3e50', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Başlık
            baslik_label = tk.Label(
                main_frame,
                text="🎤 ADA Asistan",
                font=("Arial", 14, "bold"),
                fg='#ecf0f1',
                bg='#2c3e50'
            )
            baslik_label.pack(pady=(0, 10))
            
            # Kullanıcı girdisi label
            self.kullanici_label = tk.Label(
                main_frame,
                text="Dinleniyor...",
                font=("Arial", 11),
                fg='#3498db',  # Açık mavi
                bg='#2c3e50',
                wraplength=350,
                justify=tk.LEFT
            )
            self.kullanici_label.pack(pady=(0, 10), fill=tk.X)
            
            # ADA yanıtı label
            self.ada_label = tk.Label(
                main_frame,
                text="",
                font=("Arial", 10),
                fg='#7f8c8d',  # Koyu gri
                bg='#2c3e50',
                wraplength=350,
                justify=tk.LEFT
            )
            self.ada_label.pack(fill=tk.X)
            
            # GUI'yi başlat
            self.gui_root.mainloop()
            
        except Exception as e:
            print(f"❌ GUI hatası: {e}")

    def gui_guncelle(self, kullanici_metni="", ada_metni=""):
        """GUI'yi güncelle"""
        try:
            if self.gui_root:
                if kullanici_metni:
                    self.kullanici_label.config(text=f"👤 Sen: {kullanici_metni}")
                if ada_metni:
                    self.ada_label.config(text=f"🤖 ADA: {ada_metni}")
                self.gui_root.update()
        except:
            pass

    def onay_sesi(self):
        """Kısa onay sesi"""
        print("🔊 Hmm...")
        try:
            self.seslendirme("dinliyorum")
        except:
            print("❌ Onay sesi çıkışı hatası")

    def pasif_dinleme(self):
        """7/24 pasif dinleme - sadece uyanma kelimesini arar"""
        print("👂 Pasif dinleme modu başlatıldı...")
        print("💡 'Hey ADA' diyerek beni uyandırabilirsiniz")
        
        # GUI'yi başlat
        self.gui_baslat()
        time.sleep(2)  # GUI'nin yüklenmesi için bekle
        
        self.mikrofon = sr.Microphone()
        
        # Mikrofonu kalibre et
        with self.mikrofon as source:
            print("🔧 Mikrofon kalibre ediliyor...")
            self.r.adjust_for_ambient_noise(source, duration=2)
            print(f"📊 Enerji eşiği: {self.r.energy_threshold}")
        
       
        
        while self.dinleme_aktif:
            try:
                with self.mikrofon as source:
                    audio = self.r.listen(source, timeout=1, phrase_time_limit=3)
                
                try:
                    metin = self.r.recognize_google(audio, language="tr-TR").lower()
                    print(f"👂 Duydum: '{metin}'")
                    self.gui_guncelle(kullanici_metni=metin)
                    
                    if self.uyanma_kelimesi_kontrol(metin):
                        self.aktif_mod_baslat()
                        
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"❌ Ses tanıma servisi hatası: {e}")
                    time.sleep(5)
                    
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"❌ Dinleme hatası: {e}")
                time.sleep(1)

    def uyanma_kelimesi_kontrol(self, metin):
        """Uyanma kelimesi var mı kontrol et"""
        for kelime in self.uyanma_kelimeleri:
            if kelime in metin:
                return True
        return False

    def aktif_mod_baslat(self):
        """Aktif mod - komut dinleme"""
        print("\n🔥 AKTİF MOD BAŞLADI!")
        self.aktif_mod = True
        self.son_komut_zamani = time.time()
        
        # Mevcut zamanlayıcıyı iptal et
        if self.aktif_mod_zamanlayici:
            self.aktif_mod_zamanlayici.cancel()
        
        # Onay sesi çıkar
        self.onay_sesi()
        
        # Komut dinleme döngüsü
        self.komut_dinleme_dongusu()

    def komut_dinleme_dongusu(self):
        """Aktif mod komut dinleme döngüsü - geliştirilmiş"""
        while self.aktif_mod:
            komut = self.komut_dinle()
            
            if komut:
                print(f"📝 Komut alındı: {komut}")
                self.gui_guncelle(kullanici_metni=komut)
                self.son_komut_zamani = time.time()
                
                # Mevcut zamanlayıcıyı iptal et
                if self.aktif_mod_zamanlayici:
                    self.aktif_mod_zamanlayici.cancel()
                
                # Komut işle
                self.komut_isle(komut)
                
                # Yeni zamanlayıcı başlat
                self.zamanlayici_baslat()
                
            else:
                # Komut gelmezse zaman kontrolü yap
                if time.time() - self.son_komut_zamani > self.aktif_mod_timeout:
                    self.aktif_modu_kapat()
                    break
                    
            # Kısa bekleme
            time.sleep(0.1)

    def zamanlayici_baslat(self):
        """Timeout sonra pasif moda geçiş zamanlayıcısı"""
        def pasif_moda_gec():
            if self.aktif_mod and time.time() - self.son_komut_zamani >= self.aktif_mod_timeout:
                self.aktif_modu_kapat()
        
        self.aktif_mod_zamanlayici = threading.Timer(float(self.aktif_mod_timeout), pasif_moda_gec)
        self.aktif_mod_zamanlayici.start()

    def aktif_modu_kapat(self):
        """Aktif modu kapat"""
        self.aktif_mod = False
        if self.aktif_mod_zamanlayici:
            self.aktif_mod_zamanlayici.cancel()
        print("😴 Pasif moda dönülüyor...\n")
        self.gui_guncelle(ada_metni="Pasif moda geçiliyor...")

    def komut_dinle(self):
        """Aktif modda komut dinle"""
        try:
            with self.mikrofon as source:
                print("🎯 Komutunuzu dinliyorum...")
                audio = self.r.listen(source, timeout=2, phrase_time_limit=8)
            
            komut = self.r.recognize_google(audio, language="tr-TR").lower()
            return komut
            
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            return None

    def komut_isle(self, komut):
        """Ana komut işleme fonksiyonu - Gemini 2.0 Flash-lite ile"""
        
        # Çıkış komutları
        if any(word in komut for word in [ "çıkış", "görüşürüz", "hoşçakal"]):
            yanit = "Görüşmek üzere! Kapanıyorum."
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            self.ses_kayitci.kayit_durdur()
            self.dinleme_aktif = False
            return
        
        # Fotoğraf çekme
        if "fotoğraf" in komut and "çek" in komut:
            self.fotograf_cek()
            return
        
        # Hava durumu
        if "hava" in komut and "durumu" in komut:
            self.hava_durumu_goster()
            return
        
        # Ses seviyesi kontrol komutları
        ses_komutu = self.ses_komutu_kontrol(komut)
        if ses_komutu is not None:
            self.ses_seviyesi_ayarla(ses_komutu)
            return
        
        # Parlaklık kontrol komutları
        parlaklık_komutu = self.parlaklık_komutu_kontrol(komut)
        if parlaklık_komutu:
            self.parlaklık_kontrol(parlaklık_komutu)
            return
        
        # Wi-Fi ve Bluetooth kontrol komutları
        wifi_bt_komutu = self.wifi_bluetooth_komutu_kontrol(komut)
        if wifi_bt_komutu:
            self.wifi_bluetooth_kontrol(wifi_bt_komutu)
            return
        
        # Gece ışığı kontrol komutları
        gece_ışığı_komutu = self.gece_ışığı_komutu_kontrol(komut)
        if gece_ışığı_komutu is not None:
            self.gece_ışığı_kontrol(gece_ışığı_komutu)
            return
        
        # Oturum kontrol komutları
        oturum_komutu = self.oturum_komutu_kontrol(komut)
        if oturum_komutu:
            self.oturum_kontrol(oturum_komutu)
            return
        
        # Medya kontrol komutları
        medya_komutu = self.medya_komutu_kontrol(komut)
        if medya_komutu:
            self.medya_kontrol(medya_komutu)
            return
        
        # Birleşik komutlar (örn: "sesi 60 yap ve müziği durdur")
        if self.birlesik_komut_kontrol(komut):
            return
        
        # Web arama
        if any(word in komut for word in ["ara", "google", "arama yap"]):
            self.web_arama(komut)
            return
        
        # Eğer hiçbir komut tanınmazsa, kullanıcıya yardım mesajı göster
        if any(word in komut for word in ["yardım", "help", "neler yapabilirsin"]):
            self.yardim_mesaji()
            return
        
        # Diğer komutlar için Gemini 2.0 Flash-lite kullan
        self.gemini_ile_komut_isle(komut)

    def fotograf_cek(self):
        """Kamera ile fotoğraf çek - 3 saniye geri sayım ile"""
        try:
            yanit = "Kameranızı açıyorum"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            
            kamera = cv2.VideoCapture(0)
            
            if not kamera.isOpened():
                yanit = "Kamera açılamadı"
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                return
            
            # Kamerayı ısıt
            for i in range(5):
                kamera.read()
            
            # 3 saniye geri sayım
            for i in range(3, 0, -1):
                yanit = f"Geri sayım: {i}"
                print(f"⏰ {yanit}")
                self.gui_guncelle(ada_metni=yanit)
                self.seslendirme(str(i))
                time.sleep(1)
            
            kontrol, resim = kamera.read()
            if kontrol:
                self.seslendirme("Gülümseyin!")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dosya_adi = f"ada_foto_{timestamp}.jpg"
                dosya_yolu = os.path.join(FOTO_KLASORU, dosya_adi)
                
                cv2.imwrite(dosya_yolu, resim)
                
                yanit = f"Fotoğrafınız çekildi! {dosya_adi}"
                self.seslendirme("Fotoğrafınız çekildi!")
                self.gui_guncelle(ada_metni=yanit)
                print(f"📸 Fotoğraf kaydedildi: {dosya_yolu}")
            
            kamera.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            yanit = "Fotoğraf çekerken hata oluştu"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            print(f"❌ Fotoğraf hatası: {e}")

    def hava_durumu_goster(self):
        """Hava durumu Google araması ve TTS ile okuma"""
        try:
            yanit = "Hava durumu bilgilerini getiriyorum"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            
            # Google'da hava durumu araması aç
            arama_url = "https://www.google.com/search?q=hava+durumu"
            webbrowser.open(arama_url)
            
            # Basit hava durumu bilgisi (örnek)
            # Gerçek implementasyonda Google'dan veri çekebilirsiniz
            hava_bilgisi = "Bugün hava sıcaklığı 30 derece, güneşli. Nem oranı yüzde 34, rüzgar hızı 21 kilometre."
            
            self.seslendirme(hava_bilgisi)
            self.gui_guncelle(ada_metni=hava_bilgisi)
            
        except Exception as e:
            yanit = "Hava durumu bilgisi alınamadı"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            print(f"❌ Hava durumu hatası: {e}")

    def ses_komutu_kontrol(self, komut):
        """Ses komutlarını kontrol et ve yüzdeyi çıkar"""
        ses_patterns = [
            r"sesi?\s*%?(\d{1,3})\s*(?:yap|et|getir|çıkar|düşür)",
            r"sesi?\s*(\d{1,3})\s*(?:seviye|derece|%)?",
            r"ses\s*seviyesi\s*(\d{1,3})",
            r"volume\s*(\d{1,3})"
        ]
        
        for pattern in ses_patterns:
            match = re.search(pattern, komut)
            if match:
                seviye = int(match.group(1))
                if 0 <= seviye <= 100:
                    return seviye
        
        # Özel durumlar
        if any(word in komut for word in ["sessiz", "sesi kapat", "mute"]):
            return 0
        elif any(word in komut for word in ["sesi aç", "sesli yap"]):
            return 50
        
        return None

    def ses_seviyesi_ayarla(self, seviye):
        """Windows sistem ses seviyesini ayarla"""
        try:
            if self.ses_kontrol_mevcut:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)
                
                volume_level = seviye / 100.0
                volume.SetMasterVolumeLevelScalar(volume_level, None)
                
                yanit = f"Tamam, sesi yüzde {seviye}'e getirdim"
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                print(f"✅ Ses seviyesi %{seviye} olarak ayarlandı")
                
            else:
                yanit = "Ses ayarlanamadı, lütfen pycaw kütüphanesini yükleyin"
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                    
        except Exception as e:
            print(f"❌ Ses ayarlama hatası: {e}")
            yanit = "Ses ayarlanırken hata oluştu"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)

    def medya_komutu_kontrol(self, komut):
        """Medya kontrol komutlarını tanı"""
        medya_komutlari = {
            "play_pause": ["müziği durdur", "müzik durdur", "duraklat", "müziği başlat", "müzik başlat","şarkıyı durdur"],
            "next": ["sonraki şarkı", "sonraki şarkıya geç", "next"],
            "previous": ["önceki şarkı", "önceki şarkıya geç", "previous"]
        }
        
        for aksiyon, kelimeler in medya_komutlari.items():
            if any(kelime in komut for kelime in kelimeler):
                return aksiyon
        
        return None

    def medya_kontrol(self, aksiyon):
        """Windows medya tuşlarını simüle et"""
        try:
            if aksiyon == "play_pause":
                self.medya_tusu_gonder(VK_MEDIA_PLAY_PAUSE)
                yanit = "Müzik durduruldu veya başlatıldı"
                
            elif aksiyon == "next":
                self.medya_tusu_gonder(VK_MEDIA_NEXT_TRACK)
                yanit = "Sonraki şarkıya geçtim"
                
            elif aksiyon == "previous":
                self.medya_tusu_gonder(VK_MEDIA_PREV_TRACK)
                yanit = "Önceki şarkıya geçtim"
            
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
                
        except Exception as e:
            print(f"❌ Medya kontrol hatası: {e}")
            yanit = "Medya kontrolü çalışmadı"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)

    def medya_tusu_gonder(self, vk_code):
        """Windows medya tuşu simülasyonu"""
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
            print(f"✅ Medya tuşu gönderildi: {hex(vk_code)}")
            
        except Exception as e:
            print(f"❌ Medya tuşu hatası: {e}")

    def birlesik_komut_kontrol(self, komut):
        """Birleşik komutları işle"""
        ses_seviye = self.ses_komutu_kontrol(komut)
        medya_aksiyon = self.medya_komutu_kontrol(komut)
        
        if ses_seviye is not None and medya_aksiyon:
            self.ses_seviyesi_ayarla_sessiz(ses_seviye)
            time.sleep(0.5)
            self.medya_kontrol_sessiz(medya_aksiyon)
            
            medya_mesaj = {
                "play_pause": "müzik durduruldu",
                "next": "sonraki şarkıya geçildi", 
                "previous": "önceki şarkıya geçildi"
            }
            
            yanit = f"Ses yüzde {ses_seviye} yapıldı ve {medya_mesaj.get(medya_aksiyon, 'medya kontrolü yapıldı')}"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            return True
        
        return False

    def ses_seviyesi_ayarla_sessiz(self, seviye):
        """Ses yanıtı vermeden ses ayarla"""
        try:
            if self.ses_kontrol_mevcut:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)
                
                volume_level = seviye / 100.0
                volume.SetMasterVolumeLevelScalar(volume_level, None)
                print(f"✅ Ses seviyesi %{seviye} (sessiz)")
                
        except Exception as e:
            print(f"❌ Ses ayarlama hatası: {e}")

    def medya_kontrol_sessiz(self, aksiyon):
        """Ses yanıtı vermeden medya kontrol"""
        try:
            if aksiyon == "play_pause":
                self.medya_tusu_gonder(VK_MEDIA_PLAY_PAUSE)
            elif aksiyon == "next":
                self.medya_tusu_gonder(VK_MEDIA_NEXT_TRACK)
            elif aksiyon == "previous":
                self.medya_tusu_gonder(VK_MEDIA_PREV_TRACK)
                
            print(f"✅ Medya kontrolü: {aksiyon} (sessiz)")
                
        except Exception as e:
            print(f"❌ Medya kontrol hatası: {e}")

    def web_arama(self, komut):
        """Web arama"""
        try:
            arama_terimi = komut.replace("ara", "").replace("google", "").replace("arama yap", "").strip()
            if arama_terimi:
                url = f"https://www.google.com/search?q={arama_terimi}"
                webbrowser.open(url)
                yanit = f"{arama_terimi} aranıyor"
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
            else:
                yanit = "Ne aramamı istersiniz?"
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
        except:
            yanit = "Web araması yapılamadı"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)

    # ==================== YENİ YETENEKLER ====================
    
    def set_brightness(self, value):
        """Ekran parlaklığını ayarla (0-100)"""
        try:
            if not (0 <= value <= 100):
                return False, "Parlaklık değeri 0-100 arasında olmalı"
            
            # WMI ile parlaklık ayarlama
            cmd = f'powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{value})"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Parlaklığı {value} yaptım"
            else:
                return False, "Parlaklık ayarlanamadı"
                
        except Exception as e:
            print(f"❌ Parlaklık ayarlama hatası: {e}")
            return False, "Parlaklık ayarlanırken hata oluştu"

    def get_brightness(self):
        """Mevcut parlaklık seviyesini al"""
        try:
            cmd = 'powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                brightness = int(result.stdout.strip())
                return True, brightness
            else:
                return False, "Parlaklık okunamadı"
                
        except Exception as e:
            print(f"❌ Parlaklık okuma hatası: {e}")
            return False, "Parlaklık okunurken hata oluştu"

    def toggle_wifi(self, on):
        """Wi-Fi'ı aç/kapat - Geliştirilmiş versiyon"""
        try:
            if on:
                # Wi-Fi'ı açmak için PowerShell kullan
                cmd = 'powershell -Command "Enable-NetAdapter -Name \'Wi-Fi\' -Confirm:$false"'
                action = "açtım"
            else:
                # Wi-Fi'ı kapatmak için PowerShell kullan
                cmd = 'powershell -Command "Disable-NetAdapter -Name \'Wi-Fi\' -Confirm:$false"'
                action = "kapattım"
            
            print(f"🔧 Wi-Fi komutu çalıştırılıyor: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Wi-Fi'ı {action}"
            else:
                # Hata durumunda alternatif yöntem dene
                print(f"❌ PowerShell hatası: {result.stderr}")
                
                # Netsh ile tekrar dene
                netsh_cmd = f'netsh interface set interface "Wi-Fi" {"enabled" if on else "disabled"}'
                result2 = subprocess.run(netsh_cmd, shell=True, capture_output=True, text=True)
                
                if result2.returncode == 0:
                    return True, f"Wi-Fi'ı {action}"
                else:
                    return False, f"Wi-Fi {action.replace('tım', 'amadım')}. Yönetici izni gerekebilir"
                
        except Exception as e:
            print(f"❌ Wi-Fi kontrol hatası: {e}")
            return False, "Wi-Fi kontrolünde hata oluştu"

    def toggle_bluetooth(self, on):
        """Bluetooth'u aç/kapat - Basitleştirilmiş versiyon"""
        try:
            if on:
                action = "açtım"
                # Bluetooth ayarlarını aç
                settings_cmd = 'start ms-settings:bluetooth'
                subprocess.run(settings_cmd, shell=True)
                return True, f"Bluetooth ayarları açıldı. Manuel olarak {action.replace('tım', 'abilirsiniz')}"
            else:
                action = "kapattım"
                # Bluetooth ayarlarını aç
                settings_cmd = 'start ms-settings:bluetooth'
                subprocess.run(settings_cmd, shell=True)
                return True, f"Bluetooth ayarları açıldı. Manuel olarak {action.replace('tım', 'abilirsiniz')}"
                
        except Exception as e:
            print(f"❌ Bluetooth kontrol hatası: {e}")
            return False, "Bluetooth kontrolünde hata oluştu"

    def set_night_light(self, on):
        """Gece ışığını aç/kapat - Basit registry yaklaşımı"""
        try:
            if on:
                # Gece ışığını açmak için registry değeri
                cmd = 'powershell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\Cache\\DefaultAccount\\$$windows.data.bluelightreduction.settings\\Current\' -Name Data -Value ([byte[]](0x43,0x42,0x01,0x00,0x00,0x15,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)) -Force"'
                action = "açtım"
            else:
                # Gece ışığını kapatmak için registry değeri
                cmd = 'powershell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\Cache\\DefaultAccount\\$$windows.data.bluelightreduction.settings\\Current\' -Name Data -Value ([byte[]](0x43,0x42,0x01,0x00,0x00,0x10,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)) -Force"'
                action = "kapattım"
            
            print(f"🔧 Gece ışığı komutu çalıştırılıyor...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Ayarları yeniden yüklemek için explorer'ı yeniden başlat
                restart_cmd = 'powershell -Command "Stop-Process -Name explorer -Force; Start-Process explorer"'
                subprocess.run(restart_cmd, shell=True, capture_output=True, text=True)
                return True, f"Gece ışığını {action}. Değişiklik birkaç saniye içinde aktif olacak"
            else:
                print(f"❌ Gece ışığı registry hatası: {result.stderr}")
                # Alternatif basit yöntem - Windows ayarlarını aç
                settings_cmd = 'start ms-settings:nightlight'
                subprocess.run(settings_cmd, shell=True)
                return True, f"Gece ışığı ayarları açıldı. Manuel olarak {action.replace('tım', 'abilirsiniz')}"
                
        except Exception as e:
            print(f"❌ Gece ışığı kontrol hatası: {e}")
            return False, "Gece ışığı kontrolünde hata oluştu"

    def lock_session(self):
        """Oturumu kilitle"""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Oturumu kilitledim"
        except Exception as e:
            print(f"❌ Oturum kilitleme hatası: {e}")
            return False, f"Oturumu kilitleyemedim: {e}"

    def logoff_session(self):
        """Oturumu kapat"""
        try:
            subprocess.run("shutdown /l", shell=True)
            return True, "Oturumu kapatıyorum"
        except Exception as e:
            print(f"❌ Oturum kapatma hatası: {e}")
            return False, f"Oturumu kapatamadım: {e}"

    # ==================== KOMUT TANIMA FONKSİYONLARI ====================
    
    def parlaklık_komutu_kontrol(self, komut):
        """Parlaklık komutlarını kontrol et"""
        # Sayısal değer arama
        patterns = [
            r"parlaklığı?\s*%?(\d{1,3})\s*(?:yap|et|getir|ayarla)",
            r"parlaklık\s*(\d{1,3})\s*(?:yap|ayarla)?",
            r"brightness\s*(\d{1,3})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, komut)
            if match:
                seviye = int(match.group(1))
                if 0 <= seviye <= 100:
                    return ("set", seviye)
        
        # Özel durumlar
        if any(word in komut for word in ["parlaklığı aç", "parlaklık aç"]):
            return ("on", DEFAULT_BRIGHTNESS)
        elif any(word in komut for word in ["parlaklığı kapat", "parlaklık kapat"]):
            return ("off", 0)
        elif any(word in komut for word in ["parlaklık kaçta", "parlaklık ne kadar"]):
            return ("status", None)
        
        return None

    def wifi_bluetooth_komutu_kontrol(self, komut):
        """Wi-Fi ve Bluetooth komutlarını kontrol et"""
        # Wi-Fi komutları
        if any(word in komut for word in ["wifi aç", "wifi'ı aç", "wi-fi aç"]):
            return ("wifi", True)
        elif any(word in komut for word in ["wifi kapat", "wifi'ı kapat", "wi-fi'yi kapat"]):
            return ("wifi", False)
        
        # Bluetooth komutları
        elif any(word in komut for word in ["bluetooth aç", "bluetooth'u aç"]):
            return ("bluetooth", True)
        elif any(word in komut for word in ["bluetooth kapat", "bluetooth'u kapat"]):
            return ("bluetooth", False)
        
        return None

    def gece_ışığı_komutu_kontrol(self, komut):
        """Gece ışığı komutlarını kontrol et"""
        if any(word in komut for word in ["gece modunu aç", "gece ışığını aç", "night light aç","modunu aç"]):
            return True
        elif any(word in komut for word in ["gece modunu kapat", "gece ışığını kapat", "night light kapat"]):
            return False
        
        return None

    def oturum_komutu_kontrol(self, komut):
        """Oturum kontrol komutlarını kontrol et"""
        if any(word in komut for word in ["bilgisayarı kilitle", "oturumu kilitle", "lock"]):
            return "lock"
        elif any(word in komut for word in ["oturumu kapat", "logout"]):
            return "logout"
        
        return None

    # ==================== KONTROL FONKSİYONLARI ====================
    
    def parlaklık_kontrol(self, komut_tuple):
        """Parlaklık kontrolü ana fonksiyonu"""
        try:
            aksiyon, değer = komut_tuple
            
            if aksiyon == "set":
                başarılı, mesaj = self.set_brightness(değer)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif aksiyon == "on":
                başarılı, mesaj = self.set_brightness(DEFAULT_BRIGHTNESS)
                if başarılı:
                    mesaj = f"Parlaklığı {DEFAULT_BRIGHTNESS} yaptım"
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif aksiyon == "off":
                başarılı, mesaj = self.set_brightness(0)
                if başarılı:
                    mesaj = "Parlaklığı kapattım"
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif aksiyon == "status":
                başarılı, değer = self.get_brightness()
                if başarılı:
                    mesaj = f"Parlaklık şu anda yüzde {değer}"
                else:
                    mesaj = değer  # Hata mesajı
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
        except Exception as e:
            print(f"❌ Parlaklık kontrol hatası: {e}")
            mesaj = "Parlaklık kontrolünde hata oluştu"
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)

    def wifi_bluetooth_kontrol(self, komut_tuple):
        """Wi-Fi ve Bluetooth kontrolü ana fonksiyonu"""
        try:
            cihaz, durum = komut_tuple
            
            if cihaz == "wifi":
                başarılı, mesaj = self.toggle_wifi(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif cihaz == "bluetooth":
                başarılı, mesaj = self.toggle_bluetooth(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
        except Exception as e:
            print(f"❌ Wi-Fi/Bluetooth kontrol hatası: {e}")
            mesaj = "Ağ cihazı kontrolünde hata oluştu"
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)

    def gece_ışığı_kontrol(self, durum):
        """Gece ışığı kontrolü ana fonksiyonu"""
        try:
            başarılı, mesaj = self.set_night_light(durum)
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)
            
        except Exception as e:
            print(f"❌ Gece ışığı kontrol hatası: {e}")
            mesaj = "Gece ışığı kontrolünde hata oluştu"
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)

    def oturum_kontrol(self, aksiyon):
        """Oturum kontrolü ana fonksiyonu"""
        try:
            if aksiyon == "lock":
                başarılı, mesaj = self.lock_session()
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif aksiyon == "logout":
                başarılı, mesaj = self.logoff_session()
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
        except Exception as e:
            print(f"❌ Oturum kontrol hatası: {e}")
            mesaj = "Oturum kontrolünde hata oluştu"
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)

    def yardim_mesaji(self):
        """Kullanıcıya mevcut komutları göster"""
        mesaj = """Merhaba! Ben ADA, sesli asistanınız. İşte yapabileceklerim:

🔊 Ses Kontrolü: 'sesi 50 yap', 'sesi aç', 'sesi kapat'
🔆 Parlaklık: 'parlaklığı 70 yap', 'parlaklığı aç', 'parlaklığı kapat', 'parlaklık kaçta'
📶 Wi-Fi: 'wifi aç', 'wifi kapat'
📱 Bluetooth: 'bluetooth aç', 'bluetooth kapat'
🌙 Gece Işığı: 'gece ışığını aç', 'gece modunu kapat'
🔒 Oturum: 'bilgisayarı kilitle', 'oturumu kapat'
🎵 Müzik: 'müziği durdur', 'sonraki şarkı', 'önceki şarkı'
📸 Fotoğraf: 'fotoğraf çek'
🌤️ Hava Durumu: 'hava durumu'
🔍 Arama: 'python ara'

⌨️ Kısayol: Ctrl+Shift tuşu ile aktif moda geçebilirsiniz
🎤 Sesli: 'Hey ADA' diyerek beni uyandırabilirsiniz!"""
        
        self.seslendirme("Size yardımcı olabileceğim konuları söylüyorum")
        self.gui_guncelle(ada_metni=mesaj)
        print(f"📋 {mesaj}")

    def komut_listesi_gui_goster(self):
        """Komut listesi GUI'sini göster"""
        try:
            komut_window = tk.Toplevel()
            komut_window.title("ADA Komut Listesi")
            komut_window.configure(bg='#2c3e50')
            
            # Pencere boyutları
            pencere_genislik = 600
            pencere_yukseklik = 700
            ekran_genislik = komut_window.winfo_screenwidth()
            ekran_yukseklik = komut_window.winfo_screenheight()
            
            # Ortaya yerleştir
            x = (ekran_genislik - pencere_genislik) // 2
            y = (ekran_yukseklik - pencere_yukseklik) // 2
            
            komut_window.geometry(f"{pencere_genislik}x{pencere_yukseklik}+{x}+{y}")
            komut_window.attributes("-topmost", True)
            
            # Ana frame
            main_frame = tk.Frame(komut_window, bg='#2c3e50', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Başlık
            baslik_label = tk.Label(
                main_frame,
                text="🎤 ADA Sesli Asistan - Komut Listesi",
                font=("Arial", 16, "bold"),
                fg='#ecf0f1',
                bg='#2c3e50'
            )
            baslik_label.pack(pady=(0, 20))
            
            # Scrollable text widget
            text_frame = tk.Frame(main_frame, bg='#2c3e50')
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(
                text_frame,
                font=("Arial", 11),
                fg='#ecf0f1',
                bg='#34495e',
                wrap=tk.WORD,
                yscrollcommand=scrollbar.set,
                padx=15,
                pady=15
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Komut listesi metni
            komut_metni = """🔊 SES KONTROLÜ
• "sesi 50 yap" - Ses seviyesini %50'ye ayarla
• "sesi aç" - Sesi açar
• "sesi kapat" - Sesi kapatır
• "sessiz" - Sesi kapatır

🔆 PARLAKLIK KONTROLÜ
• "parlaklığı 70 yap" - Parlaklığı %70'e ayarla
• "parlaklığı aç" - Parlaklığı açar
• "parlaklığı kapat" - Parlaklığı kapatır
• "parlaklık kaçta" - Mevcut parlaklığı söyler

📶 WI-FI KONTROLÜ
• "wifi aç" - Wi-Fi'ı açar
• "wifi kapat" - Wi-Fi'ı kapatır

📱 BLUETOOTH KONTROLÜ
• "bluetooth aç" - Bluetooth'u açar
• "bluetooth kapat" - Bluetooth'u kapatır

🌙 GECE IŞIĞI
• "gece ışığını aç" - Gece modunu açar
• "gece modunu kapat" - Gece modunu kapatır

🔒 OTURUM KONTROLÜ
• "bilgisayarı kilitle" - Oturumu kilitler
• "oturumu kapat" - Oturumu kapatır

🎵 MÜZİK KONTROLÜ
• "müziği durdur" - Müziği durdurur/başlatır
• "sonraki şarkı" - Sonraki şarkıya geçer
• "önceki şarkı" - Önceki şarkıya geçer

📸 FOTOĞRAF
• "fotoğraf çek" - Kamera ile fotoğraf çeker

🌤️ HAVA DURUMU
• "hava durumu" - Hava durumu bilgilerini gösterir

🔍 WEB ARAMA
• "python ara" - Google'da arama yapar
• "ara [konu]" - Belirtilen konuyu arar

💬 GENEL SOHBET
• Herhangi bir soru sorabilirsiniz
• ADA, Gemini AI ile desteklenir

⌨️ KISAYOLLAR
• Ctrl+Shift - Aktif/Pasif mod geçişi
• "Hey ADA" - Sesli uyandırma

🚪 ÇIKIŞ
• "çıkış" - Programı kapatır
• "görüşürüz" - Programı kapatır
• "hoşçakal" - Programı kapatır

📋 YARDIM
• "yardım" - Bu komut listesini gösterir
• "neler yapabilirsin" - Yetenekleri listeler"""
            
            text_widget.insert(tk.END, komut_metni)
            text_widget.config(state=tk.DISABLED)
            
            # Kapat butonu
            kapat_btn = tk.Button(
                main_frame,
                text="Kapat",
                font=("Arial", 12, "bold"),
                fg='#ecf0f1',
                bg='#e74c3c',
                activebackground='#c0392b',
                activeforeground='#ecf0f1',
                command=komut_window.destroy,
                padx=20,
                pady=10
            )
            kapat_btn.pack(pady=(20, 0))
            
        except Exception as e:
            print(f"❌ Komut listesi GUI hatası: {e}")

    def hotkey_kurulumu(self):
        """Global hotkey kurulumu - Sadece Ctrl+Shift"""
        try:
            # Sadece Ctrl+Shift kombinasyonu
            keyboard.add_hotkey('ctrl+shift', self.hotkey_handler)
            self.hotkey_aktif = True
            print("✅ Global hotkey (Ctrl+Shift) kuruldu")
                
        except Exception as e:
            print(f"❌ Hotkey kurulum hatası: {e}")
            print("💡 'pip install keyboard' komutu ile keyboard kütüphanesini yükleyin")
            self.hotkey_aktif = False

    def hotkey_handler(self):
        """Hotkey basıldığında çalışacak fonksiyon - geliştirilmiş"""
        try:
            print("\n🔥 HOTKEY TETİKLENDİ! (Ctrl+Shift)")
            
            if not self.aktif_mod:
                # Pasif moddan aktif moda geç
                print("🎯 Hotkey ile aktif moda geçiliyor...")
                self.gui_guncelle(kullanici_metni="Ctrl+Shift tuşu basıldı")
                self.aktif_mod_baslat()
            else:
                # Aktif moddan pasif moda geç
                print("😴 Hotkey ile pasif moda geçiliyor...")
                self.gui_guncelle(kullanici_metni="Pasif moda geçiliyor...")
                self.aktif_modu_kapat()
                
        except Exception as e:
            print(f"❌ Hotkey handler hatası: {e}")


# Ana program
if __name__ == "__main__":
    print("ADA Gelişmiş Sesli Asistan")
    print("\nSeçenekler:")
    print("1. Normal başlatma (Yönetici izni gerekli)")
    print("2. Test modu (Yönetici izni olmadan)")
    
    secim = input("\nSeçiminizi yapın (1/2): ").strip()
    
    if secim == "2":
        print("Test modu - Yönetici izni atlanıyor")
    else:
        # Yönetici izni kontrolü
        run_as_admin()
    
    print("ADA Gelişmiş Sesli Asistan başlatılıyor...")
    print("\nEk kurulum gereksinimleri:")
    print("pip install pycaw     # Windows ses kontrolü için")
    print("pip install keyboard  # Global hotkey için")
    print("\nGemini API anahtarınızı kodda güncelleyin!")
    print("\nKısayol tuşu: Ctrl+Shift (Aktif moda geçmek için)")
    
    test_secimi = input("\nBaşlatmak için Enter'a basın (Test için 't' yazın): ")
    
    try:
        asistan = GelismisADA()
        
        # Test modu
        if test_secimi.lower() == 't':
            print("\n🧪 TEST MODU BAŞLATILIYOR...")
            
            # Parlaklık testi
            print("\n🔆 Parlaklık testi:")
            try:
                başarılı, sonuç = asistan.get_brightness()
                if başarılı:
                    print(f"✅ Mevcut parlaklık: {sonuç}")
                else:
                    print(f"❌ Parlaklık okunamadı: {sonuç}")
            except Exception as e:
                print(f"❌ Parlaklık test hatası: {e}")
            
            # Wi-Fi testi
            print("\n📶 Wi-Fi testi:")
            try:
                başarılı, sonuç = asistan.toggle_wifi(True)
                print(f"{'✅' if başarılı else '❌'} Wi-Fi açma testi: {sonuç}")
            except Exception as e:
                print(f"❌ Wi-Fi test hatası: {e}")
            
            # Bluetooth testi
            print("\n📱 Bluetooth testi:")
            try:
                başarılı, sonuç = asistan.toggle_bluetooth(True)
                print(f"{'✅' if başarılı else '❌'} Bluetooth açma testi: {sonuç}")
            except Exception as e:
                print(f"❌ Bluetooth test hatası: {e}")
            
            # Gece ışığı testi
            print("\n🌙 Gece ışığı testi:")
            try:
                başarılı, sonuç = asistan.set_night_light(True)
                print(f"{'✅' if başarılı else '❌'} Gece ışığı açma testi: {sonuç}")
            except Exception as e:
                print(f"❌ Gece ışığı test hatası: {e}")
            
            # Hotkey testi
            print("\n⌨️ Hotkey testi:")
            if asistan.hotkey_aktif:
                print("✅ Hotkey aktif")
            else:
                print("❌ Hotkey aktif değil")
            
            print("\n🧪 Test tamamlandı!")
            input("Devam etmek için Enter'a basın...")
        
        asistan.dinleme_aktif = True
        
        # Çıkış sırasında hotkey temizleme
        def cleanup():
            try:
                if asistan.hotkey_aktif:
                    keyboard.unhook_all_hotkeys()
                    print("🧹 Hotkey temizlendi")
            except:
                pass
        
        atexit.register(cleanup)
        
        asistan.pasif_dinleme()  # Pasif dinlemeyi başlat
        
    except KeyboardInterrupt:
        print("\n👋 ADA kapatılıyor...")
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
    except Exception as e:
        print(f"❌ Başlatma hatası: {e}")

