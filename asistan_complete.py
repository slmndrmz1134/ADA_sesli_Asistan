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

# Basit başlatma fonksiyonu
def start_program():
    """Programı normal kullanıcı olarak başlat"""
    print("✅ Program normal kullanıcı olarak başlatılıyor")
    return True

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
        """Gemini 2.0 Flash-lite ile akıllı komut işleme - gelişmiş hata yönetimi"""
        try:
            print(f"🤖 Gemini'ye komut gönderiliyor: '{komut}'")
            
            prompt = f"""Sen ADA adında Türkçe konuşan bir sesli asistansın. Kullanıcının sorusunu veya komutunu dostça ve profesyonel bir şekilde yanıtla.
            
Önemli: Yanıtını kısa ve öz tut, maksimum 2-3 cümle olsun. Uzun açıklamalar yapma.

Kullanıcı: {komut}
ADA: """
            
            print(f"🔄 Gemini API'ye istek gönderiliyor...")
            
            # Model kontrolü
            if model is None:
                raise Exception("Gemini model yüklenmemiş")
            
            response = model.generate_content(prompt)
            
            if response and hasattr(response, 'text') and response.text:
                yanit = response.text.strip()
                print(f"✅ Gemini yanıtı alındı: {yanit}")
                
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                
                # Web sitesi açma kontrolü
                if "web sitesi aç" in yanit.lower():
                    site = yanit.split("web sitesi aç")[-1].strip()
                    if site:
                        webbrowser.open(f"https://{site}")
                        
            else:
                error_msg = "Gemini'den yanıt alınamadı"
                if response and hasattr(response, 'prompt_feedback'):
                    error_msg += f" (Prompt feedback: {response.prompt_feedback})"
                print(f"❌ {error_msg}")
                
                yanit = "Üzgünüm, bir yanıt oluşturamadım. Lütfen tekrar deneyin."
                self.seslendirme(yanit)
                self.gui_guncelle(ada_metni=yanit)
                
        except Exception as e:
            print(f"❌ Gemini hatası: {e}")
            print(f"❌ Hata türü: {type(e).__name__}")
            
            # Hata türüne göre farklı mesajlar
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                yanit = "API kullanım limiti aşıldı. Lütfen daha sonra tekrar deneyin."
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                yanit = "İnternet bağlantısı sorunu. Lütfen bağlantınızı kontrol edin."
            elif "model" in str(e).lower():
                yanit = "AI model sorunu yaşanıyor. Lütfen tekrar deneyin."
            else:
                yanit = "Bir teknik sorun yaşandı. Lütfen tekrar deneyin."
                
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
        
        # Gelişmiş ses tanıma ayarları
        self.r = sr.Recognizer()
        self.r.energy_threshold = 1000  # Başlangıç değeri, dinamik olarak ayarlanacak
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.6  # Daha hızlı yanıt için azaltıldı
        self.r.phrase_threshold = 0.3  # Kelime başlangıcı için eşik
        self.r.non_speaking_duration = 0.5  # Konuşma bitişi algısı
        
        # Coqui TTS motoru başlat
        self.tts_engine = None
        self.tts_baslat()
        
        # pygame ses çalma için - optimize edilmiş ayarlar
        try:
            pygame.mixer.pre_init(
                frequency=22050,  # Daha düşük frekansta daha hızlı yükleme
                size=-16,         # 16-bit audio
                channels=2,       # Stereo
                buffer=1024       # Daha küçük buffer daha hızlı başlatma
            )
            pygame.mixer.init()
            print("✅ Pygame ses sistemi optimize edildi")
        except Exception as e:
            pygame.mixer.init()  # Varsayılan ayarlarla
            print(f"⚠️ Pygame varsayılan ayarlarla başlatıldı: {e}")
        
        # GUI ayarları
        self.gui_root = None
        self.gui_label = None
        self.gui_thread = None
        self.gui_aktif = False
        self.animasyon_aktif = False
        
        # Durum değişkenleri
        self.aktif_mod = False
        self.dinleme_aktif = False
        self.mikrofon = None
        self.aktif_mod_zamanlayici = None
        self.son_komut_zamani = 0
        self.hotkey_aktif = False
        self.aktif_mod_timeout = 5  # 5 saniye timeout
        self.ses_caliniyor = False  # Ses çalma durumu kontrolü
        
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
        
        # Performans izleme değişkenleri
        self.ses_tanima_istatistikleri = {
            'toplam_deneme': 0,
            'basarili_tanima': 0,
            'basarisiz_tanima': 0,
            'timeout_sayisi': 0,
            'hata_sayisi': 0,
            'ortalama_yanit_suresi': 0.0
        }
        
        # Bekleyen komut sistemi
        self._bekleyen_komut = None
        self._bekleyen_komut_zamani = 0
        
        # Silinecek dosyalar listesi
        self._silinecek_dosyalar = []
        
        # Periyodik temizlik başlat
        self.temizlik_baslat()
        
        # Global hotkey ayarları
        self.hotkey_kurulumu()
        
        # Global hotkey ayarları
        self.hotkey_kurulumu()
        
        # Global hotkey ayarları
        self.hotkey_kurulumu()
        
        print("🎤 ADA Asistan başlatılıyor...")
        print("⌨️  Ctrl+Shift tuşu ile aktif/pasif mod geçişi")

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
        """Gelişmiş Coqui TTS ile seslendirme sistemi - non-blocking"""
        print(f"🔊 ADA: {metin}")
        
        if not self.tts_engine:
            print("❌ TTS motoru yok, sadece metin gösteriliyor")
            return
            
        try:
            # Ses çalma durumunu işaretle
            self.ses_caliniyor = True
            
            # Geçici ses dosyası oluştur - daha benzersiz isim
            timestamp = int(time.time() * 1000)  # Milisaniye hassasiyeti
            thread_id = threading.get_ident()
            ses_dosyasi = os.path.join(self.temp_ses_klasoru, f"ada_tts_{timestamp}_{thread_id}.wav")
            
            # TTS ile ses dosyası oluştur
            print(f"🎵 TTS dosyası oluşturuluyor...")
            self.tts_engine.tts_to_file(text=metin, file_path=ses_dosyasi)
            
            # Dosyanın oluştuğunu kontrol et
            if os.path.exists(ses_dosyasi) and os.path.getsize(ses_dosyasi) > 0:
                print("✅ TTS dosyası oluşturuldu")
                
                # Threaded ses çalma için ayrı fonksiyon
                ses_thread = threading.Thread(
                    target=self._ses_cal_threaded, 
                    args=(ses_dosyasi,),
                    daemon=True
                )
                ses_thread.start()
                
            else:
                print("❌ TTS dosyası oluşturulamadı veya boş")
                self.ses_caliniyor = False
                
        except Exception as e:
            print(f"❌ Ses çıkışı hatası: {e}")
            print(f"❌ Hata detayı: {type(e).__name__}")
            self.ses_caliniyor = False
    
    def _ses_cal_threaded(self, ses_dosyasi):
        """Threaded ses çalma fonksiyonu - gelişmiş dosya yönetimi"""
        try:
            # pygame ile ses dosyasını çal
            pygame.mixer.music.load(ses_dosyasi)
            pygame.mixer.music.play()
            print("🎵 Ses çalınıyor...")
            
            # Çalma bitene kadar bekle - non-blocking kontrolü
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print("✅ Ses çalma tamamlandı")
            
        except Exception as e:
            print(f"❌ Threaded ses çalma hatası: {e}")
        finally:
            # Ses çalma durumunu temizle
            self.ses_caliniyor = False
            
            # Bekleyen komutları kontrol et
            self.bekleyen_komut_kontrol()
            
            # Geçici dosyayı güvenli şekilde sil
            self._guvenli_dosya_sil(ses_dosyasi)
    
    def _guvenli_dosya_sil(self, dosya_yolu):
        """Geçici dosyayı güvenli şekilde sil"""
        max_deneme = 5
        bekleme_suresi = 0.2
        
        for deneme in range(max_deneme):
            try:
                if os.path.exists(dosya_yolu):
                    # Dosyanın kilitli olmaması için bekleme
                    time.sleep(bekleme_suresi)
                    
                    # pygame'den dosyayı serbest bırak
                    try:
                        pygame.mixer.music.unload()
                    except:
                        pass
                    
                    # Dosyayı sil
                    os.remove(dosya_yolu)
                    print(f"✅ Geçici dosya silindi: {os.path.basename(dosya_yolu)}")
                    return
                else:
                    return  # Dosya zaten yok
                    
            except PermissionError:
                # Dosya hala kilitli, daha uzun bekle
                bekleme_suresi *= 2
                print(f"⚠️ Dosya kilitli, {deneme+1}/{max_deneme} deneme, {bekleme_suresi}s bekleniyor...")
                time.sleep(bekleme_suresi)
                continue
            except Exception as cleanup_error:
                print(f"⚠️ Dosya silme denemsesi {deneme+1}/{max_deneme} hatası: {cleanup_error}")
                time.sleep(bekleme_suresi)
                continue
        
        # Tüm denemeler başarısız olduysa, dosyayı daha sonra silinmek üzere işaretle
        print(f"⚠️ Geçici dosya silinemiyor, daha sonra temizlenecek: {os.path.basename(dosya_yolu)}")
        
        # Dosyayı silinecekler listesine ekle
        if not hasattr(self, '_silinecek_dosyalar'):
            self._silinecek_dosyalar = []
        self._silinecek_dosyalar.append(dosya_yolu)

    def gui_baslat(self):
        """GUI thread'ini başlat"""
        if not self.gui_aktif:
            self.gui_thread = threading.Thread(target=self.gui_olustur, daemon=True)
            self.gui_thread.start()
            self.gui_aktif = True

    def gui_olustur(self):
        """Modern Siri benzeri GUI oluştur"""
        try:
            self.gui_root = tk.Tk()
            self.gui_root.title("ADA AI Assistant")
            
            # Pencere boyutları ve konumu (başlangıçta küçük)
            self.pasif_genislik = 300
            self.pasif_yukseklik = 180
            self.aktif_genislik = 450
            self.aktif_yukseklik = 280
            
            ekran_genislik = self.gui_root.winfo_screenwidth()
            
            # Sağ üst köşeye yerleştir (başlangıçta küçük boyut)
            x = ekran_genislik - self.pasif_genislik - 30
            y = 30
            
            self.gui_root.geometry(f"{self.pasif_genislik}x{self.pasif_yukseklik}+{x}+{y}")
            self.gui_root.attributes("-topmost", True)  # Her zaman üstte
            self.gui_root.overrideredirect(True)  # Pencere çerçevesini kaldır
            self.gui_root.configure(bg='#000000')  # Siyah arka plan
            
            # Şeffaf arka plan efekti
            self.gui_root.attributes("-alpha", 0.95)  # %95 şeffaflık
            
            # Sürüklenebilir yapmak için mouse event'leri
            self.gui_root.bind("<Button-1>", self.on_mouse_down)
            self.gui_root.bind("<B1-Motion>", self.on_mouse_drag)
            self.gui_root.bind("<ButtonRelease-1>", self.on_mouse_up)
            
            # Sürükleme değişkenleri
            self.drag_x = 0
            self.drag_y = 0
            self.dragging = False
            
            # Ana frame - gradient efekti için
            main_frame = tk.Frame(self.gui_root, bg='#1a1a1a', padx=25, pady=25)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Üst kısım - ADA logo ve durum
            top_frame = tk.Frame(main_frame, bg='#1a1a1a')
            top_frame.pack(fill=tk.X, pady=(0, 15))
            
            # ADA logo ve başlık
            logo_frame = tk.Frame(top_frame, bg='#1a1a1a')
            logo_frame.pack(side=tk.LEFT)
            
            # Animasyonlu ADA ikonu
            self.ada_icon = tk.Label(
                logo_frame,
                text="🤖",
                font=("Arial", 24),
                fg='#00ff88',  # Neon yeşil
                bg='#1a1a1a'
            )
            self.ada_icon.pack(side=tk.LEFT, padx=(0, 10))
            
            # ADA başlık
            baslik_label = tk.Label(
                logo_frame,
                text="ADA AI",
                font=("Arial", 18, "bold"),
                fg='#ffffff',
                bg='#1a1a1a'
            )
            baslik_label.pack(side=tk.LEFT)
            
            # Durum göstergesi
            self.durum_label = tk.Label(
                top_frame,
                text="●",
                font=("Arial", 16),
                fg='#00ff88',  # Yeşil - aktif
                bg='#1a1a1a'
            )
            self.durum_label.pack(side=tk.RIGHT)
            
            # Orta kısım - Kullanıcı mesajı
            self.kullanici_frame = tk.Frame(main_frame, bg='#2a2a2a', relief=tk.FLAT, bd=0)
            self.kullanici_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.kullanici_label = tk.Label(
                self.kullanici_frame,
                text="👤 Dinleniyor...",
                font=("Arial", 12),
                fg='#ffffff',
                bg='#2a2a2a',
                wraplength=250,  # Pasif mod için daha küçük
                justify=tk.LEFT,
                anchor=tk.W
            )
            self.kullanici_label.pack(padx=15, pady=10, fill=tk.X)
            
            # Alt kısım - ADA yanıtı
            self.ada_frame = tk.Frame(main_frame, bg='#1a1a1a', relief=tk.FLAT, bd=0)
            self.ada_frame.pack(fill=tk.BOTH, expand=True)
            
            self.ada_label = tk.Label(
                self.ada_frame,
                text="",
                font=("Arial", 11),
                fg='#00ff88',  # Neon yeşil
                bg='#1a1a1a',
                wraplength=250,  # Pasif mod için daha küçük
                justify=tk.LEFT,
                anchor=tk.W
            )
            self.ada_label.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
            
            # Animasyon başlat
            self.animasyon_baslat()
            
            # GUI'yi başlat
            self.gui_root.mainloop()
            
        except Exception as e:
            print(f"❌ GUI hatası: {e}")

    def on_mouse_down(self, event):
        """Mouse basıldığında sürükleme başlat"""
        self.drag_x = event.x
        self.drag_y = event.y
        self.dragging = True

    def on_mouse_drag(self, event):
        """Mouse sürüklendiğinde pencereyi taşı"""
        if self.dragging:
            x = self.gui_root.winfo_x() + (event.x - self.drag_x)
            y = self.gui_root.winfo_y() + (event.y - self.drag_y)
            self.gui_root.geometry(f"+{x}+{y}")

    def on_mouse_up(self, event):
        """Mouse bırakıldığında sürükleme bitir"""
        self.dragging = False

    def gui_boyut_degistir(self, aktif_mod):
        """GUI boyutunu aktif/pasif moda göre değiştir"""
        try:
            if self.gui_root:
                if aktif_mod:
                    # Aktif modda büyük boyut
                    self.gui_root.geometry(f"{self.aktif_genislik}x{self.aktif_yukseklik}")
                    print("🔍 GUI aktif mod boyutuna geçti")
                else:
                    # Pasif modda küçük boyut
                    self.gui_root.geometry(f"{self.pasif_genislik}x{self.pasif_yukseklik}")
                    print("🔍 GUI pasif mod boyutuna geçti")
        except Exception as e:
            print(f"❌ GUI boyut değiştirme hatası: {e}")
            
        except Exception as e:
            print(f"❌ GUI hatası: {e}")

    def animasyon_baslat(self):
        """Animasyonları başlat"""
        self.animasyon_aktif = True
        self.yanip_sonme_animasyonu()
        self.durum_animasyonu()

    def yanip_sonme_animasyonu(self):
        """ADA ikonunu yanıp söndür"""
        if hasattr(self, 'ada_icon') and self.animasyon_aktif:
            current_color = self.ada_icon.cget('fg')
            new_color = '#00ff88' if current_color == '#1a1a1a' else '#1a1a1a'
            self.ada_icon.configure(fg=new_color)
            self.gui_root.after(800, self.yanip_sonme_animasyonu)

    def durum_animasyonu(self):
        """Durum göstergesini animasyonlu yap"""
        if hasattr(self, 'durum_label') and self.animasyon_aktif:
            if self.aktif_mod:
                # Aktif modda hızlı yanıp sönme
                current_color = self.durum_label.cget('fg')
                new_color = '#ff4444' if current_color == '#00ff88' else '#00ff88'
                self.durum_label.configure(fg=new_color)
                self.gui_root.after(300, self.durum_animasyonu)
            else:
                # Pasif modda yavaş yanıp sönme
                current_color = self.durum_label.cget('fg')
                new_color = '#00ff88' if current_color == '#1a1a1a' else '#1a1a1a'
                self.durum_label.configure(fg=new_color)
                self.gui_root.after(1000, self.durum_animasyonu)

    def gui_guncelle(self, kullanici_metni="", ada_metni=""):
        """Modern GUI'yi güncelle"""
        try:
            if self.gui_root:
                if kullanici_metni:
                    # Kullanıcı mesajını animasyonlu göster
                    self.kullanici_label.config(
                        text=f"👤 {kullanici_metni}",
                        fg='#ffffff'
                    )
                    # Kullanıcı frame'ini vurgula
                    self.kullanici_frame.configure(bg='#3a3a3a')
                    self.gui_root.after(2000, lambda: self.kullanici_frame.configure(bg='#2a2a2a'))
                
                if ada_metni:
                    # ADA yanıtını animasyonlu göster
                    self.ada_label.config(
                        text=f"🤖 {ada_metni}",
                        fg='#00ff88'
                    )
                    # ADA frame'ini vurgula
                    self.ada_frame.configure(bg='#2a2a2a')
                    self.gui_root.after(2000, lambda: self.ada_frame.configure(bg='#1a1a1a'))
                
                # Durum göstergesini güncelle
                if self.aktif_mod:
                    self.durum_label.config(text="●", fg='#ff4444')  # Kırmızı - aktif
                else:
                    self.durum_label.config(text="●", fg='#00ff88')  # Yeşil - pasif
                
                # Label boyutlarını aktif/pasif moda göre ayarla
                if self.aktif_mod:
                    self.kullanici_label.config(wraplength=380)
                    self.ada_label.config(wraplength=380)
                else:
                    self.kullanici_label.config(wraplength=250)
                    self.ada_label.config(wraplength=250)
                
                self.gui_root.update()
        except Exception as e:
            print(f"❌ GUI güncelleme hatası: {e}")

    def onay_sesi(self):
        """Kısa onay sesi"""
        print("🔊 Hmm...")
        try:
            self.seslendirme("dinliyorum")
        except Exception as e:
            print(f"❌ Onay sesi çıkışı hatası: {e}")

    def pasif_dinleme(self):
        """Gelişmiş 7/24 pasif dinleme - optimize edilmiş mikrofon yönetimi"""
        print("👂 Gelişmiş pasif dinleme modu başlatıldı...")
        print("💡 'Hey ADA' diyerek beni uyandırabilirsiniz")
        
        # GUI'yi başlat
        self.gui_baslat()
        time.sleep(2)  # GUI'nin yüklenmesi için bekle
        
        # Mikrofon ayarları
        self.mikrofon = sr.Microphone()
        
        # Gelişmiş mikrofon kalibrasyonu
        self.mikrofon_kalibre_et()
        
        # Sürekli dinleme döngüsü
        basarisiz_denemeler = 0
        max_basarisiz = 5
        
        while self.dinleme_aktif:
            try:
                # Mikrofon durumunu kontrol et
                if basarisiz_denemeler >= max_basarisiz:
                    print("🔄 Mikrofon yeniden kalibre ediliyor...")
                    self.mikrofon_kalibre_et()
                    basarisiz_denemeler = 0
                
                # Ses dinleme - optimize edilmiş parametreler
                audio_data = self.ses_dinle()
                
                if audio_data:
                    # Ses tanıma işlemi
                    metin = self.ses_tanima_isle(audio_data)
                    
                    if metin:
                        print(f"👂 Duydum: '{metin}'")
                        self.gui_guncelle(kullanici_metni=metin)
                        
                        # Komut işleme
                        self.komut_yonlendir(metin)
                        
                        basarisiz_denemeler = 0  # Başarılı işlem sonrası reset
                    else:
                        basarisiz_denemeler += 1
                else:
                    # Sessizlik döneminde CPU'yu rahatlatmak için kısa bekleme
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"❌ Dinleme döngüsü hatası: {e}")
                basarisiz_denemeler += 1
                time.sleep(0.5)  # Hata durumunda kısa bekleme
                
        print("👋 Dinleme modu sonlandırıldı")
    
    def mikrofon_kalibre_et(self):
        """Gelişmiş mikrofon kalibrasyonu"""
        try:
            print("🔧 Mikrofon kalibre ediliyor...")
            
            with self.mikrofon as source:
                # Dinamik gürültü ayarlaması
                self.r.adjust_for_ambient_noise(source, duration=2)  # int olarak
                
                # Optimize edilmiş eşik değerleri
                self.r.energy_threshold = max(300, min(4000, self.r.energy_threshold))
                self.r.dynamic_energy_threshold = True
                self.r.pause_threshold = 0.6  # Daha hızlı yanıt için
                self.r.phrase_threshold = 0.3
                self.r.non_speaking_duration = 0.5
                
                print(f"📊 Enerji eşiği: {self.r.energy_threshold}")
                print(f"📊 Duraklatma eşiği: {self.r.pause_threshold}")
                
        except Exception as e:
            print(f"❌ Mikrofon kalibrasyon hatası: {e}")
            # Varsayılan değerleri kullan
            self.r.energy_threshold = 1000
            self.r.pause_threshold = 0.8
    
    def ses_dinle(self):
        """Optimize edilmiş ses dinleme fonksiyonu"""
        try:
            with self.mikrofon as source:
                # Aktif/pasif moda göre farklı timeout değerleri
                if self.aktif_mod:
                    timeout = 0.5  # Aktif modda daha hızlı yanıt
                    phrase_time_limit = 4  # Daha uzun komutlar için
                else:
                    timeout = 1  # Pasif modda enerji tasarrufu
                    phrase_time_limit = 3
                
                # Ses dinle
                audio = self.r.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                return audio
                
        except sr.WaitTimeoutError:
            # Timeout normal bir durum, sessizce devam et
            self.performans_guncelle('timeout')
            return None
        except Exception as e:
            if "blocking" not in str(e).lower():
                print(f"❌ Ses dinleme hatası: {e}")
            return None
    
    def ses_tanima_isle(self, audio_data):
        """Gelişmiş ses tanıma işlemi - performans izlemeli"""
        baslangic_zamani = time.time()
        
        try:
            # Google ses tanıma - optimize edilmiş ayarlar
            metin = self.r.recognize_google(
                audio_data, 
                language="tr-TR",
                show_all=False  # Sadece en iyi sonucu al
            ).lower().strip()
            
            # Boş veya çok kısa metinleri filtrele
            if len(metin) < 2:
                self.performans_guncelle('basarisiz')
                return None
            
            # Başarılı tanıma
            yanit_suresi = time.time() - baslangic_zamani
            self.performans_guncelle('basarili', yanit_suresi)
            return metin
            
        except sr.UnknownValueError:
            # Tanınamayan ses - normal durum
            self.performans_guncelle('basarisiz')
            return None
        except sr.RequestError as e:
            print(f"❌ Google ses tanıma servisi hatası: {e}")
            self.performans_guncelle('hata')
            # Internet bağlantı sorunu durumunda kısa bekleme
            time.sleep(2)
            return None
        except Exception as e:
            print(f"❌ Ses tanıma işlem hatası: {e}")
            self.performans_guncelle('hata')
            return None
    
    def performans_guncelle(self, durum, yanit_suresi=0.0):
        """Ses tanıma performansını izle"""
        try:
            self.ses_tanima_istatistikleri['toplam_deneme'] += 1
            
            if durum == 'basarili':
                self.ses_tanima_istatistikleri['basarili_tanima'] += 1
                if yanit_suresi > 0:
                    # Ortalama yanıt süresini güncelle
                    toplam = self.ses_tanima_istatistikleri['basarili_tanima']
                    eski_ortalama = self.ses_tanima_istatistikleri['ortalama_yanit_suresi']
                    yeni_ortalama = ((eski_ortalama * (toplam - 1)) + yanit_suresi) / toplam
                    self.ses_tanima_istatistikleri['ortalama_yanit_suresi'] = yeni_ortalama
                    
            elif durum == 'basarisiz':
                self.ses_tanima_istatistikleri['basarisiz_tanima'] += 1
            elif durum == 'timeout':
                self.ses_tanima_istatistikleri['timeout_sayisi'] += 1
            elif durum == 'hata':
                self.ses_tanima_istatistikleri['hata_sayisi'] += 1
            
            # Her 50 denemede bir istatistikleri göster
            if self.ses_tanima_istatistikleri['toplam_deneme'] % 50 == 0:
                self.performans_raporu()
                
        except Exception as e:
            print(f"❌ Performans güncelleme hatası: {e}")
    
    def performans_raporu(self):
        """Performans raporunu göster"""
        try:
            stats = self.ses_tanima_istatistikleri
            toplam = stats['toplam_deneme']
            
            if toplam == 0:
                return
            
            basari_orani = (stats['basarili_tanima'] / toplam) * 100
            
            print(f"\n📊 === PERFORMANS RAPORU ===")
            print(f"📊 Toplam deneme: {toplam}")
            print(f"✅ Başarılı: {stats['basarili_tanima']} ({basari_orani:.1f}%)")
            print(f"❌ Başarısız: {stats['basarisiz_tanima']}")
            print(f"⏱️ Timeout: {stats['timeout_sayisi']}")
            print(f"⚠️ Hata: {stats['hata_sayisi']}")
            print(f"🚀 Ortalama yanıt: {stats['ortalama_yanit_suresi']:.2f}s")
            print(f"📊 ========================\n")
            
        except Exception as e:
            print(f"❌ Performans raporu hatası: {e}")
            
    def komut_yonlendir(self, metin):
        """Komutları duruma göre yönlendir - gelişmiş komut işleme"""
        try:
            # Uyanma kelimesi kontrolü (pasif modda)
            if not self.aktif_mod:
                if self.uyanma_kelimesi_kontrol(metin):
                    print("🔥 Uyanma kelimesi algılandı!")
                    self.aktif_mod_baslat()
                return
            
            # Aktif modda komut işleme
            if self.aktif_mod:
                # Ses çalma sırasında önemli komutları beklet
                if self.ses_caliniyor:
                    print(f"🔇 Ses çalma sırasında komut bekleniyor: '{metin}'")
                    # Komutları kuyruğa al
                    self._bekleyen_komut = metin
                    self._bekleyen_komut_zamani = time.time()
                    return
                
                print(f"📝 Aktif modda komut işleniyor: {metin}")
                self.gui_guncelle(kullanici_metni=metin)
                self.son_komut_zamani = time.time()
                
                # Komut işle
                self.komut_isle(metin)
                
                # Yeni zamanlayıcı başlat (ses çalma bittikten sonra)
                self.zamanlayici_gecikme_ile_baslat()
                
        except Exception as e:
            print(f"❌ Komut yönlendirme hatası: {e}")
    
    def temizlik_baslat(self):
        """Periyodik geçici dosya temizliği başlat"""
        def temizlik_gorevi():
            while self.dinleme_aktif:
                try:
                    # 30 saniyede bir temizlik yap
                    time.sleep(30)
                    self.gecici_dosya_temizligi()
                except Exception as e:
                    print(f"❌ Temizlik görevi hatası: {e}")
        
        temizlik_thread = threading.Thread(target=temizlik_gorevi, daemon=True)
        temizlik_thread.start()
    
    def gecici_dosya_temizligi(self):
        """Geçici dosyaları temizle"""
        try:
            # Silinecek dosyalar listesini kontrol et
            if hasattr(self, '_silinecek_dosyalar') and self._silinecek_dosyalar:
                silinen_count = 0
                kalan_dosyalar = []
                
                for dosya_yolu in self._silinecek_dosyalar:
                    try:
                        if os.path.exists(dosya_yolu):
                            os.remove(dosya_yolu)
                            silinen_count += 1
                    except:
                        # Hala silinemiyor, listede kalsın
                        kalan_dosyalar.append(dosya_yolu)
                
                self._silinecek_dosyalar = kalan_dosyalar
                
                if silinen_count > 0:
                    print(f"🧹 Periyodik temizlik: {silinen_count} dosya silindi")
            
            # Eski geçici dosyaları temizle (1 saatten eski)
            if os.path.exists(self.temp_ses_klasoru):
                su_an = time.time()
                eski_dosya_count = 0
                
                for dosya_adi in os.listdir(self.temp_ses_klasoru):
                    dosya_yolu = os.path.join(self.temp_ses_klasoru, dosya_adi)
                    try:
                        if os.path.isfile(dosya_yolu):
                            dosya_yaratilma = os.path.getctime(dosya_yolu)
                            if su_an - dosya_yaratilma > 3600:  # 1 saat
                                os.remove(dosya_yolu)
                                eski_dosya_count += 1
                    except:
                        continue
                
                if eski_dosya_count > 0:
                    print(f"🧹 Eski dosya temizliği: {eski_dosya_count} dosya silindi")
                    
        except Exception as e:
            print(f"❌ Geçici dosya temizlik hatası: {e}")
            
    def bekleyen_komut_kontrol(self):
        """Ses çalma bittikten sonra bekleyen komutları işle"""
        try:
            if hasattr(self, '_bekleyen_komut') and self._bekleyen_komut:
                # Komutun çok eski olmamasını kontrol et (5 saniye)
                if time.time() - self._bekleyen_komut_zamani < 5:
                    print(f"📋 Bekleyen komut işleniyor: '{self._bekleyen_komut}'")
                    
                    # Komut işle
                    self.gui_guncelle(kullanici_metni=self._bekleyen_komut)
                    self.son_komut_zamani = time.time()
                    self.komut_isle(self._bekleyen_komut)
                    
                    # Yeni zamanlayıcı başlat
                    self.zamanlayici_gecikme_ile_baslat()
                else:
                    print("⏰ Bekleyen komut çok eski, iptal ediliyor")
                
                # Bekleyen komutu temizle
                self._bekleyen_komut = None
                self._bekleyen_komut_zamani = 0
                
        except Exception as e:
            print(f"❌ Bekleyen komut kontrol hatası: {e}")

    def uyanma_kelimesi_kontrol(self, metin):
        """Gelişmiş uyanma kelimesi kontrolü - fuzzy matching ile"""
        if not metin:
            return False
            
        # Metni temizle
        metin = metin.lower().strip()
        
        # Direkt eşleşme kontrolü
        for kelime in self.uyanma_kelimeleri:
            if kelime in metin:
                print(f"✅ Uyanma kelimesi bulundu: '{kelime}' -> '{metin}'")
                return True
        
        # Fuzzy matching - benzer sesli kelimeler
        benzer_kelimeler = {
            "ada": ["eda", "ada", "ata", "ade", "adağ"],
            "hey": ["hay", "hey", "he", "ay"],
            "ok": ["ok", "oke", "okay"],
            "okey": ["okey", "oke", "ok", "okay"],
            "baksana": ["baksana", "bak sana", "baksan", "baksa"]
        }
        
        for ana_kelime, varyasyonlar in benzer_kelimeler.items():
            for varyasyon in varyasyonlar:
                if varyasyon in metin:
                    print(f"✅ Benzer uyanma kelimesi bulundu: '{varyasyon}' -> '{ana_kelime}' -> '{metin}'")
                    return True
        
        # Sesli harf değişimi kontrolü
        import re
        for kelime in ["ada", "hey"]:
            # Sesli harfleri wildcard ile değiştir
            pattern = re.sub(r'[aeiouçğııöşü]', '[aeiouçğııöşü]', kelime)
            if re.search(pattern, metin):
                print(f"✅ Sesli harf varyasyonu bulundu: '{kelime}' pattern -> '{metin}'")
                return True
        
        return False

    def aktif_mod_baslat(self):
        """Gelişmiş aktif mod - daha iyi zaman yönetimi"""
        print("\n🔥 AKTİF MOD BAŞLADI!")
        self.aktif_mod = True
        self.son_komut_zamani = time.time()
        
        # Mevcut zamanlayıcıyı iptal et
        if self.aktif_mod_zamanlayici:
            self.aktif_mod_zamanlayici.cancel()
        
        # GUI boyutunu büyüt
        self.gui_boyut_degistir(True)
        
        # "Dinliyorum" sesi çıkar - non-blocking
        self.seslendirme("Dinliyorum")
        self.gui_guncelle(ada_metni="Dinliyorum...")
        
        # Zamanlayıcı başlat (ses çalma bittikten sonra)
        self.zamanlayici_gecikme_ile_baslat()
    
    def zamanlayici_gecikme_ile_baslat(self):
        """Ses çalma bittikten sonra zamanlayıcı başlat - gelişmiş versiyon"""
        def gecikme_ile_baslat():
            try:
                # Ses çalma bitene kadar bekle
                bekleme_sayaci = 0
                max_bekleme = 50  # 5 saniye maksimum bekleme
                
                while self.ses_caliniyor and bekleme_sayaci < max_bekleme:
                    time.sleep(0.1)
                    bekleme_sayaci += 1
                
                if bekleme_sayaci >= max_bekleme:
                    print("⚠️ Ses çalma çok uzun sürüyor, zamanlayıcı başlatılıyor")
                
                # 0.5 saniye ek bekleme
                time.sleep(0.5)
                
                # Aktif mod hala devam ediyorsa zamanlayıcıyı başlat
                if self.aktif_mod:
                    print("⏰ Zamanlayıcı başlatılıyor (ses sonrası)...")
                    self.zamanlayici_baslat()
                
            except Exception as e:
                print(f"❌ Gecikme ile başlatma hatası: {e}")
                # Hata durumunda normal zamanlayıcıyı başlat
                if self.aktif_mod:
                    self.zamanlayici_baslat()
        
        # Thread olarak çalıştır
        gecikme_thread = threading.Thread(target=gecikme_ile_baslat, daemon=True)
        gecikme_thread.start()
    
    def zamanlayici_baslat(self):
        """Gelişmiş timeout zamanlayıcısı - çoklu kontrol"""
        # Mevcut zamanlayıcıyı iptal et
        if self.aktif_mod_zamanlayici:
            self.aktif_mod_zamanlayici.cancel()
        
        def pasif_moda_gec():
            try:
                # Son komut zamanını kontrol et
                gecen_sure = time.time() - self.son_komut_zamani
                
                if self.aktif_mod and gecen_sure >= self.aktif_mod_timeout:
                    print(f"\n⏰ {self.aktif_mod_timeout} saniye timeout - pasif moda geçiliyor...")
                    self.aktif_modu_kapat()
                elif self.aktif_mod:
                    # Henüz timeout olmamış, kalan süre için yeni zamanlayıcı
                    kalan_sure = self.aktif_mod_timeout - gecen_sure
                    if kalan_sure > 0:
                        self.aktif_mod_zamanlayici = threading.Timer(kalan_sure, pasif_moda_gec)
                        self.aktif_mod_zamanlayici.start()
                        print(f"⏱️ Yeniden zamanlayıcı: {kalan_sure:.1f} saniye kaldı")
                    else:
                        self.aktif_modu_kapat()
            except Exception as e:
                print(f"❌ Zamanlayıcı hatası: {e}")
        
        # Yeni zamanlayıcı başlat
        self.aktif_mod_zamanlayici = threading.Timer(float(self.aktif_mod_timeout), pasif_moda_gec)
        self.aktif_mod_zamanlayici.start()
        print(f"⏰ Aktif mod zamanlayıcısı başlatıldı: {self.aktif_mod_timeout} saniye")
    
    def aktif_modu_kapat(self):
        """Gelişmiş aktif mod kapatışı"""
        if not self.aktif_mod:
            return
            
        self.aktif_mod = False
        
        if self.aktif_mod_zamanlayici:
            self.aktif_mod_zamanlayici.cancel()
            self.aktif_mod_zamanlayici = None
        
        # GUI boyutunu küçült
        self.gui_boyut_degistir(False)
        
        print("😴 Pasif moda dönülüyor...\n")
        self.gui_guncelle(ada_metni="Pasif moda geçiliyor...")

    def komut_isle(self, komut):
        """Ana komut işleme fonksiyonu - Gemini 2.0 Flash-lite ile - debug li"""
        
        print(f"🔍 DEBUG: Komut işleme başlıyor: '{komut}'")
        
        # Çıkış komutları
        if any(word in komut for word in [ "çıkış", "görüşürüz", "hoşçakal"]):
            print("🔍 DEBUG: Çıkış komutu tespit edildi")
            yanit = "Görüşmek üzere! Kapanıyorum."
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            self.dinleme_aktif = False
            return
        
        # Fotoğraf çekme
        if "fotoğraf" in komut and "çek" in komut:
            print("🔍 DEBUG: Fotoğraf çekme komutu tespit edildi")
            self.fotograf_cek()
            return
        
        # Hava durumu
        if "hava" in komut and "durumu" in komut:
            print("🔍 DEBUG: Hava durumu komutu tespit edildi")
            self.hava_durumu_goster()
            return
        
        # Ses seviyesi kontrol komutları
        ses_komutu = self.ses_komutu_kontrol(komut)
        if ses_komutu is not None:
            print(f"🔍 DEBUG: Ses komutu tespit edildi: {ses_komutu}")
            self.ses_seviyesi_ayarla(ses_komutu)
            return
        
        # Parlaklık kontrol komutları
        parlaklık_komutu = self.parlaklık_komutu_kontrol(komut)
        if parlaklık_komutu:
            print(f"🔍 DEBUG: Parlaklık komutu tespit edildi: {parlaklık_komutu}")
            self.parlaklık_kontrol(parlaklık_komutu)
            return
        
        # Wi-Fi ve Bluetooth kontrol komutları
        wifi_bt_komutu = self.wifi_bluetooth_komutu_kontrol(komut)
        if wifi_bt_komutu:
            print(f"🔍 DEBUG: Wi-Fi/Bluetooth komutu tespit edildi: {wifi_bt_komutu}")
            self.wifi_bluetooth_kontrol(wifi_bt_komutu)
            return
        
        # Gece ışığı kontrol komutları
        gece_ışığı_komutu = self.gece_ışığı_komutu_kontrol(komut)
        if gece_ışığı_komutu is not None:
            print(f"🔍 DEBUG: Gece ışığı komutu tespit edildi: {gece_ışığı_komutu}")
            self.gece_ışığı_kontrol(gece_ışığı_komutu)
            return
        
        # Oturum kontrol komutları
        oturum_komutu = self.oturum_komutu_kontrol(komut)
        if oturum_komutu:
            print(f"🔍 DEBUG: Oturum komutu tespit edildi: {oturum_komutu}")
            self.oturum_kontrol(oturum_komutu)
            return
        
        # Medya kontrol komutları
        medya_komutu = self.medya_komutu_kontrol(komut)
        if medya_komutu:
            print(f"🔍 DEBUG: Medya komutu tespit edildi: {medya_komutu}")
            self.medya_kontrol(medya_komutu)
            return
        
        # Birleşik komutlar (örn: "sesi 60 yap ve müziği durdur")
        if self.birlesik_komut_kontrol(komut):
            print("🔍 DEBUG: Birleşik komut tespit edildi")
            return
        
        # Web arama
        if any(word in komut for word in ["ara", "google", "arama yap"]):
            print("🔍 DEBUG: Web arama komutu tespit edildi")
            self.web_arama(komut)
            return
        
        # Eğer hiçbir komut tanınmazsa, kullanıcıya yardım mesajı göster
        if any(word in komut for word in ["yardım", "help", "neler yapabilirsin"]):
            print("🔍 DEBUG: Yardım komutu tespit edildi")
            self.yardim_mesaji()
            return
        
        # Diğer komutlar için Gemini 2.0 Flash-lite kullan
        print(f"🔍 DEBUG: Gemini'ye yönlendiriliyor: '{komut}'")
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
        """Google'da hava durumu araması yap"""
        try:
            yanit = "Hava durumu bilgilerini getiriyorum"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            
            # Google'da hava durumu araması yap
            url = "https://www.google.com/search?q=hava+durumu"
            webbrowser.open(url)
            
            yanit = "Hava durumu bilgileri Google'da açıldı"
            self.seslendirme(yanit)
            self.gui_guncelle(ada_metni=yanit)
            
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
            else:
                yanit = "Bilinmeyen medya komutu"
            
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
                
            else:
                print("⚠️ Ses ayarlanamadı - pycaw kütüphanesi gerekli")
                
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
        """Wi-Fi'ı aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # Enter tuşu ile Wi-Fi'ı seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Wi-Fi'ı {action}"
                
        except Exception as e:
            print(f"❌ Wi-Fi kontrol hatası: {e}")
            return False, "Wi-Fi kontrolünde hata oluştu"

    def toggle_bluetooth(self, on):
        """Bluetooth'u aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # Sağ ok tuşu ile Bluetooth'a geç
            ctypes.windll.user32.keybd_event(0x27, 0, 0, 0)  # Sağ ok tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x27, 0, 2, 0)  # Sağ ok tuşu bırak
            time.sleep(0.2)
            
            # Enter tuşu ile Bluetooth'u seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Bluetooth'u {action}"
                
        except Exception as e:
            print(f"❌ Bluetooth kontrol hatası: {e}")
            return False, "Bluetooth kontrolünde hata oluştu"

    def toggle_airplane_mode(self, on):
        """Uçak modunu aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # 2x sağ ok tuşu ile uçak moduna geç
            for i in range(2):
                ctypes.windll.user32.keybd_event(0x27, 0, 0, 0)  # Sağ ok tuşu bas
                time.sleep(0.1)
                ctypes.windll.user32.keybd_event(0x27, 0, 2, 0)  # Sağ ok tuşu bırak
                time.sleep(0.2)
            
            # Enter tuşu ile uçak modunu seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Uçak modunu {action}"
                
        except Exception as e:
            print(f"❌ Uçak modu kontrol hatası: {e}")
            return False, "Uçak modu kontrolünde hata oluştu"

    def toggle_energy_saver(self, on):
        """Enerji tasarrufu modunu aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # 5x sağ ok tuşu ile enerji tasarrufuna geç
            for i in range(5):
                ctypes.windll.user32.keybd_event(0x27, 0, 0, 0)  # Sağ ok tuşu bas
                time.sleep(0.1)
                ctypes.windll.user32.keybd_event(0x27, 0, 2, 0)  # Sağ ok tuşu bırak
                time.sleep(0.2)
            
            # Enter tuşu ile enerji tasarrufunu seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Enerji tasarrufu modunu {action}"
                
        except Exception as e:
            print(f"❌ Enerji tasarrufu kontrol hatası: {e}")
            return False, "Enerji tasarrufu kontrolünde hata oluştu"

    def set_night_light(self, on):
        """Gece ışığını aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # 7x sağ ok tuşu ile gece ışığına geç
            for i in range(7):
                ctypes.windll.user32.keybd_event(0x27, 0, 0, 0)  # Sağ ok tuşu bas
                time.sleep(0.1)
                ctypes.windll.user32.keybd_event(0x27, 0, 2, 0)  # Sağ ok tuşu bırak
                time.sleep(0.2)
            
            # Enter tuşu ile gece ışığını seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Gece ışığını {action}"
                
        except Exception as e:
            print(f"❌ Gece ışığı kontrol hatası: {e}")
            return False, "Gece ışığı kontrolünde hata oluştu"

    def toggle_mobile_hotspot(self, on):
        """Mobil etkin noktayı aç/kapat - Quick Settings ile klavye kontrolü"""
        try:
            # Windows Quick Settings panelini aç (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            time.sleep(0.5)  # Panel açılması için bekle
            
            # 8x sağ ok tuşu ile mobil etkin noktaya geç
            for i in range(8):
                ctypes.windll.user32.keybd_event(0x27, 0, 0, 0)  # Sağ ok tuşu bas
                time.sleep(0.1)
                ctypes.windll.user32.keybd_event(0x27, 0, 2, 0)  # Sağ ok tuşu bırak
                time.sleep(0.2)
            
            # Enter tuşu ile mobil etkin noktayı seç ve aç/kapat
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter tuşu bırak
            time.sleep(0.3)  # İşlem için bekle
            
            # Quick Settings panelini kapat (Win+A)
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A tuşu bas
            time.sleep(0.2)
            ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            
            action = "açtım" if on else "kapattım"
            return True, f"Mobil etkin noktayı {action}"
                
        except Exception as e:
            print(f"❌ Mobil etkin nokta kontrol hatası: {e}")
            return False, "Mobil etkin nokta kontrolünde hata oluştu"

    def lock_session(self):
        """Oturumu kilitle"""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Oturumu kilitledim"
        except Exception as e:
            print(f"❌ Oturum kilitleme hatası: {e}")
            return False, f"Oturumu kilitleyemedim: {e}"

    def logoff_session(self):
        """Oturumu kapat - Win+L kısayolu ile"""
        try:
            # Win+L kısayolunu simüle et
            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x4C, 0, 0, 0)  # L tuşu bas
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x4C, 0, 2, 0)  # L tuşu bırak
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win tuşu bırak
            return True, "Oturumu kilitledim"
        except Exception as e:
            print(f"❌ Oturum kilitleme hatası: {e}")
            return False, f"Oturumu kilitleyemedim: {e}"

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
        """Wi-Fi, Bluetooth, Uçak modu, Enerji tasarrufu, Gece ışığı ve Mobil etkin nokta komutlarını kontrol et"""
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
        
        # Uçak modu komutları
        elif any(word in komut for word in ["uçak modu aç", "uçak modunu aç", "airplane mode aç"]):
            return ("airplane", True)
        elif any(word in komut for word in ["uçak modu kapat", "uçak modunu kapat", "airplane mode kapat"]):
            return ("airplane", False)
        
        # Enerji tasarrufu komutları
        elif any(word in komut for word in ["enerji tasarrufu aç", "enerji tasarrufunu aç", "battery saver aç"]):
            return ("energy", True)
        elif any(word in komut for word in ["enerji tasarrufu kapat", "enerji tasarrufunu kapat", "battery saver kapat"]):
            return ("energy", False)
        
        # Gece ışığı komutları
        elif any(word in komut for word in ["gece ışığını aç", "gece modunu aç", "night light aç"]):
            return ("nightlight", True)
        elif any(word in komut for word in ["gece ışığını kapat", "gece modunu kapat", "night light kapat"]):
            return ("nightlight", False)
        
        # Mobil etkin nokta komutları
        elif any(word in komut for word in ["mobil etkin nokta aç", "hotspot aç", "mobil nokta aç"]):
            return ("hotspot", True)
        elif any(word in komut for word in ["mobil etkin nokta kapat", "hotspot kapat", "mobil nokta kapat"]):
            return ("hotspot", False)
        
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
                    mesaj = str(değer)  # Hata mesajı
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
        except Exception as e:
            print(f"❌ Parlaklık kontrol hatası: {e}")
            mesaj = "Parlaklık kontrolünde hata oluştu"
            self.seslendirme(mesaj)
            self.gui_guncelle(ada_metni=mesaj)

    def wifi_bluetooth_kontrol(self, komut_tuple):
        """Wi-Fi, Bluetooth, Uçak modu, Enerji tasarrufu, Gece ışığı ve Mobil etkin nokta kontrolü ana fonksiyonu"""
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
                
            elif cihaz == "airplane":
                başarılı, mesaj = self.toggle_airplane_mode(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif cihaz == "energy":
                başarılı, mesaj = self.toggle_energy_saver(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif cihaz == "nightlight":
                başarılı, mesaj = self.set_night_light(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
            elif cihaz == "hotspot":
                başarılı, mesaj = self.toggle_mobile_hotspot(durum)
                self.seslendirme(mesaj)
                self.gui_guncelle(ada_metni=mesaj)
                
        except Exception as e:
            print(f"❌ Sistem kontrol hatası: {e}")
            mesaj = "Sistem kontrolünde hata oluştu"
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
        admin_notice = ""
        if not self.admin_izni:
            admin_notice = "\n⚠️ Not: Bazı özellikler yönetici izni gerektirir (ses, parlaklık, Wi-Fi kontrolü)"
        
        mesaj = f"""Merhaba! Ben ADA, sesli asistanınız. İşte yapabileceklerim:

🔊 Ses Kontrolü: 'sesi 50 yap', 'sesi aç', 'sesi kapat'
🔆 Parlaklık: 'parlaklığı 70 yap', 'parlaklığı aç', 'parlaklığı kapat', 'parlaklık kaçta'
📶 Wi-Fi: 'wifi aç', 'wifi kapat'
📱 Bluetooth: 'bluetooth aç', 'bluetooth kapat'
✈️ Uçak Modu: 'uçak modu aç', 'uçak modu kapat'
🔋 Enerji Tasarrufu: 'enerji tasarrufu aç', 'enerji tasarrufu kapat'
🌙 Gece Işığı: 'gece ışığını aç', 'gece modunu kapat'
📱 Mobil Etkin Nokta: 'mobil etkin nokta aç', 'hotspot aç'
🔒 Oturum: 'bilgisayarı kilitle', 'oturumu kapat' (Win+L ile kilitleme)
🎵 Müzik: 'müziği durdur', 'sonraki şarkı', 'önceki şarkı'
📸 Fotoğraf: 'fotoğraf çek'
🌤️ Hava Durumu: 'hava durumu' (Google'da arama)
🔍 Arama: 'python ara'

⌨️ Kısayol: Ctrl+Shift tuşu ile aktif/pasif mod geçişi
🎤 Sesli: 'Hey ADA' diyerek beni uyandırabilirsiniz!{admin_notice}"""
        
        self.seslendirme("Size yardımcı olabileceğim konuları söylüyorum")
        self.gui_guncelle(ada_metni=mesaj)
        print(f"📋 {mesaj}")

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
        """Gelişmiş hotkey handler - daha hızlı yanıt"""
        try:
            print("\n🔥 HOTKEY TETİKLENDİ! (Ctrl+Shift)")
            
            # Aynı anda birden fazla hotkey tetiklenmesini önle
            current_time = time.time()
            if hasattr(self, '_last_hotkey_time') and current_time - self._last_hotkey_time < 0.5:
                print("⚠️ Hotkey çok hızlı tetiklendi, göz ardı ediliyor")
                return
            
            self._last_hotkey_time = current_time
            
            if not self.aktif_mod:
                # Pasif moddan aktif moda geç
                print("🎯 Hotkey ile aktif moda geçiliyor...")
                self.gui_guncelle(kullanici_metni="Ctrl+Shift tuşu basıldı")
                
                # Aktif modu başlat
                self.aktif_mod_baslat()
                
            else:
                # Aktif moddan pasif moda geç
                print("😴 Hotkey ile pasif moda geçiliyor...")
                self.gui_guncelle(kullanici_metni="Pasif moda geçiliyor...")
                self.aktif_modu_kapat()
                
        except Exception as e:
            print(f"❌ Hotkey handler hatası: {e}")
            # Hata durumunda hotkey'i yeniden kur
            try:
                keyboard.unhook_all_hotkeys()
                time.sleep(0.1)
                keyboard.add_hotkey('ctrl+shift', self.hotkey_handler)
                print("🔄 Hotkey yeniden kuruldu")
            except Exception as e2:
                print(f"❌ Hotkey yeniden kurulamadı: {e2}")


def api_key_gui():
    """API anahtarı giriş GUI'si"""
    api_key = None
    
    def api_key_al():
        nonlocal api_key
        api_key = entry.get().strip()
        if api_key:
            root.quit()
        else:
            error_label.config(text="Lütfen geçerli bir API anahtarı girin!")
    
    def komut_listesi_goster():
        """Komut listesi penceresini göster"""
        try:
            komut_window = tk.Toplevel(root)
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

✈️ UÇAK MODU KONTROLÜ
• "uçak modu aç" - Uçak modunu açar
• "uçak modu kapat" - Uçak modunu kapatır

🔋 ENERJİ TASARRUFU KONTROLÜ
• "enerji tasarrufu aç" - Enerji tasarrufu modunu açar
• "enerji tasarrufu kapat" - Enerji tasarrufu modunu kapatır

🌙 GECE IŞIĞI KONTROLÜ
• "gece ışığını aç" - Gece ışığını açar
• "gece modunu kapat" - Gece ışığını kapatır

📱 MOBİL ETKİN NOKTA KONTROLÜ
• "mobil etkin nokta aç" - Mobil etkin noktayı açar
• "hotspot aç" - Mobil etkin noktayı açar
• "mobil etkin nokta kapat" - Mobil etkin noktayı kapatır

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
• "hava durumu" - Google'da hava durumu araması yapar

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
•
    def medya_kontrol(self,
"hoşçakal" - Programı kapatır

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
    
    root = tk.Tk()
    root.title("ADA Sesli Asistan - API Anahtarı")
    root.configure(bg='#2c3e50')
    
    # Pencere boyutları ve konumu
    pencere_genislik = 500
    pencere_yukseklik = 400
    ekran_genislik = root.winfo_screenwidth()
    ekran_yukseklik = root.winfo_screenheight()
    
    # Ortaya yerleştir
    x = (ekran_genislik - pencere_genislik) // 2
    y = (ekran_yukseklik - pencere_yukseklik) // 2
    
    root.geometry(f"{pencere_genislik}x{pencere_yukseklik}+{x}+{y}")
    root.resizable(False, False)
    
    # Ana frame
    main_frame = tk.Frame(root, bg='#2c3e50', padx=30, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Başlık
    baslik_label = tk.Label(
        main_frame,
        text="🎤 ADA Sesli Asistan",
        font=("Arial", 18, "bold"),
        fg='#ecf0f1',
        bg='#2c3e50'
    )
    baslik_label.pack(pady=(0, 20))
    
    # Açıklama
    aciklama_label = tk.Label(
        main_frame,
        text="Başlamak için Gemini API anahtarınızı girin:",
        font=("Arial", 12),
        fg='#bdc3c7',
        bg='#2c3e50'
    )
    aciklama_label.pack(pady=(0, 20))
    
    # API key entry
    entry = tk.Entry(
        main_frame,
        font=("Arial", 11),
        width=50,
        show="*"
    )
    entry.pack(pady=(0, 10))
    entry.focus()
    
    # Hata mesajı
    error_label = tk.Label(
        main_frame,
        text="",
        font=("Arial", 10),
        fg='#e74c3c',
        bg='#2c3e50'
    )
    error_label.pack(pady=(0, 20))
    
    # Butonlar frame
    button_frame = tk.Frame(main_frame, bg='#2c3e50')
    button_frame.pack(pady=(0, 20))
    
    # Başlat butonu
    baslat_btn = tk.Button(
        button_frame,
        text="Başlat",
        font=("Arial", 12, "bold"),
        fg='#ecf0f1',
        bg='#27ae60',
        activebackground='#2ecc71',
        activeforeground='#ecf0f1',
        command=api_key_al,
        padx=20,
        pady=10
    )
    baslat_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # Komut listesi butonu
    komut_btn = tk.Button(
        button_frame,
        text="Komut Listesi",
        font=("Arial", 12, "bold"),
        fg='#ecf0f1',
        bg='#3498db',
        activebackground='#5dade2',
        activeforeground='#ecf0f1',
        command=komut_listesi_goster,
        padx=20,
        pady=10
    )
    komut_btn.pack(side=tk.LEFT)
    
    # Enter tuşu ile başlatma
    def enter_pressed(event):
        api_key_al()
    
    entry.bind('<Return>', enter_pressed)
    
    # Bilgi metni
    bilgi_label = tk.Label(
        main_frame,
        text="API anahtarınızı https://makersuite.google.com/app/apikey adresinden alabilirsiniz.",
        font=("Arial", 9),
        fg='#7f8c8d',
        bg='#2c3e50',
        wraplength=450,
        justify=tk.CENTER
    )
    bilgi_label.pack()
    
    root.mainloop()
    root.destroy()
    
    return api_key

# Ana program
if __name__ == "__main__":
    print("🎤 ADA Gelişmiş Sesli Asistan")
    print("=" * 50)
    
    # Programı normal kullanıcı olarak başlat
    start_ok = start_program()
    
    if start_ok:
        print("✅ Program başlatılıyor...")
    else:
        print("❌ Program başlatılamadı.")
        sys.exit(1)
    
    print("\n📋 Gereksinimler kontrol ediliyor...")
    print("pip install pycaw     # Windows ses kontrolü için")
    print("pip install keyboard  # Global hotkey için")
    print("pip install TTS       # Ses sentezi için")
    
    try:
        # API anahtarı al
        print("\n🔑 API anahtarı alınıyor...")
        api_key = api_key_gui()
        
        if not api_key:
            print("❌ API anahtarı girilmedi. Program sonlandırılıyor.")
            sys.exit(1)
        
        print("✅ API anahtarı alındı")
        print("\n🚀 ADA başlatılıyor...")
        
        # Asistanı başlat
        asistan = GelismisADA(api_key)
        asistan.dinleme_aktif = True
        
        # Çıkış sırasında temizlik
        def cleanup():
            try:
                if asistan.hotkey_aktif:
                    keyboard.unhook_all_hotkeys()
                    print("🧹 Hotkey temizlendi")
                if hasattr(asistan, 'animasyon_aktif'):
                    asistan.animasyon_aktif = False
                    print("🎬 Animasyonlar durduruldu")
            except:
                pass
        
        atexit.register(cleanup)
        
        print("✅ ADA hazır!")
        print("⌨️  Ctrl+Shift tuşu ile aktif/pasif mod geçişi")
        print("🎤 'Hey ADA' diyerek beni uyandırabilirsiniz")
        
        # Sürekli dinlemeyi başlat
        asistan.pasif_dinleme()
        
    except KeyboardInterrupt:
        print("\n👋 ADA kapatılıyor...")
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
    except Exception as e:
        print(f"❌ Başlatma hatası: {e}")
        input("Devam etmek için Enter'a basın...")