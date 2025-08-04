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

# Konfigürasyon
GEMINI_API_KEY = "AIzaSyBtxHw82u-Y3uEK2Uh-kvk7gwEVRTbFtuI"  # Gemini API anahtarınızı buraya girin
FOTO_KLASORU = r"C:\Users\SELMAN\OneDrive\Pictures\Camera Roll"

# Gemini 2.0 Flash-lite modeli yapılandır
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Windows medya tuşları
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD



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
    def __init__(self):
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
        
   
        
        print("🎤 ADA Asistan başlatılıyor...")

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
        """5 saniye boyunca komut dinleme döngüsü"""
        while self.aktif_mod:
            komut = self.komut_dinle()
            
            if komut:
                print(f"📝 Komut alındı: {komut}")
                self.gui_guncelle(kullanici_metni=komut)
                self.son_komut_zamani = time.time()
                
                # Komut iptal et zamanlayıcıyı
                if self.aktif_mod_zamanlayici:
                    self.aktif_mod_zamanlayici.cancel()
                
                # Komut işle
                self.komut_isle(komut)
                
                # Yeni 5 saniye zamanlayıcı başlat
                self.zamanlayici_baslat()
                
            else:
                # Komut gelmezse zaman kontrolü yap
                if time.time() - self.son_komut_zamani > 5:
                    self.aktif_modu_kapat()
                    break

    def zamanlayici_baslat(self):
        """5 saniye sonra pasif moda geçiş zamanlayıcısı"""
        def pasif_moda_gec():
            if self.aktif_mod and time.time() - self.son_komut_zamani >= 5:
                self.aktif_modu_kapat()
        
        self.aktif_mod_zamanlayici = threading.Timer(5.0, pasif_moda_gec)
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
        if any(word in komut for word in ["kapat", "çıkış", "görüşürüz", "hoşçakal"]):
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


# Ana program
if __name__ == "__main__":
    print("🚀 ADA Gelişmiş Sesli Asistan başlatılıyor...")
    print("\n⚙️  Ek kurulum gereksinimleri:")
    print("pip install pycaw  # Windows ses kontrolü için")
    print("\n🔑 Gemini API anahtarınızı kodda güncelleyin!")
    
    input("\n▶️  Başlatmak için Enter'a basın...")
    
    asistan = GelismisADA()
    asistan.dinleme_aktif = True
    asistan.pasif_dinleme()  # Pasif dinlemeyi başlat
