# ADA Gelişmiş Sesli Asistan

ADA (Advanced Digital Assistant), Python tabanlı, Türkçe dil desteğine sahip gelişmiş bir sesli asistandır. Google Gemini yapay zeka modeli ile güçlendirilmiş olup, bilgisayar kontrolü, medya yönetimi, internet araması ve doğal dil işleme yeteneklerine sahiptir.

## 🚀 Özellikler

*   **Yapay Zeka Destekli Sohbet:** Google Gemini 2.0 Flash-lite modeli ile akıllı ve doğal sohbet.
*   **Sesli Kontrol:** "Hey ADA" gibi uyanma kelimeleri ile sesli aktivasyon.
*   **Sistem Kontrolü:**
    *   Ses seviyesi ayarlama
    *   Parlaklık kontrolü
    *   Wi-Fi, Bluetooth, Uçak Modu, Enerji Tasarrufu açma/kapama
    *   Gece ışığı kontrolü
    *   Mobil Hotspot kontrolü
    *   Bilgisayarı kilitleme ve oturum kapatma
*   **Medya Yönetimi:** Müzik durdurma/başlatma, önceki/sonraki şarkıya geçiş.
*   **Araçlar:**
    *   Fotoğraf çekme (geri sayımlı)
    *   Hava durumu sorgulama
    *   Web araması yapma
*   **Modern Arayüz (GUI):**
    *   Siri benzeri animasyonlu arayüz
    *   Sürüklenip bırakılabilir pencere
    *   Dinleme ve konuşma durumlarına göre görsel geri bildirim
*   **Klavye Kısayolu:** `Ctrl+Shift` ile hızlı aktivasyon.
*   **Gelişmiş Ses Sentezi:** Coqui TTS ile doğal Türkçe seslendirme.

## 📋 Gereksinimler

Projenin çalışması için aşağıdaki Python kütüphanelerine ihtiyacı vardır:

```bash
pip install -r requirements.txt
```

**Temel Kütüphaneler:**
*   `google-generativeai`: Gemini API iletişimi için
*   `speech_recognition`: Ses tanıma için
*   `pyaudio`: Mikrofon girişi için
*   `pygame`: Ses çalma için
*   `gTTS` veya `TTS`: Ses sentezi için (Projedi Coqui TTS kullanmaktadır)
*   `opencv-python` (cv2): Kamera ve fotoğraf çekimi için
*   `pycaw`: Windows ses kontrolü için
*   `keyboard`: Global kısayol tuşları için
*   `beautifulsoup4`: Web ayrıştırma için
*   `Pillow`: Görüntü işleme için

## 🎮 Kullanım

1.  Programı başlatın:
    ```bash
    python asistan_complete.py
    ```
2.  İlk açılışta sizden **Google Gemini API Anahtarı** isteyecektir. (https://makersuite.google.com/app/apikey adresinden alabilirsiniz).
3.  **Kullanım Yöntemleri:**
    *   **Sesli:** "Hey ADA", "ADA", "Baksana" diyerek asistanı uyandırın.
    *   **Klavye:** `Ctrl+Shift` tuşlarına basarak dinleme modunu başlatın.

## 🗣️ Sesli Komut Listesi

### Ses ve Parlaklık
*   "Sesi 50 yap", "Sesi aç", "Sessiz"
*   "Parlaklığı 70 yap", "Parlaklığı aç/kapat"

### Bağlantı ve Sistem
*   "Wifi aç/kapat"
*   "Bluetooth aç/kapat"
*   "Uçak modunu aç/kapat"
*   "Gece ışığını aç/kapat"
*   "Bilgisayarı kilitle", "Oturumu kapat"

### Medya
*   "Müziği durdur", "Devam ettir"
*   "Sonraki şarkı", "Önceki şarkı"

### Diğer
*   "Fotoğraf çek"
*   "Hava durumu"
*   "Python nedir ara" (Web araması)
*   "Çıkış", "Görüşürüz"

---

## 🔧 Kod ve Fonksiyon Dokümantasyonu

Dosya: `asistan_complete.py`

### Sınıf: `GelismisADA`

Bu sınıf asistanın tüm temel fonksiyonlarını barındırır.

#### Başlangıç ve Ayarlar
*   `__init__(self, api_key)`: Asistanı başlatır. Gemini, TTS, Mikrofon, GUI ve Ses sistemi ayarlarını yapar.
*   `klasorleri_olustur(self)`: Fotoğraflar ve geçici ses dosyaları için gerekli klasörleri oluşturur.
*   `api_key_gui()` (Global Fonksiyon): Kullanıcıdan API anahtarını almak için bir arayüz gösterir.

#### Ses Tanıma ve İşleme (STT)
*   `pasif_dinleme(self)`: Arka planda sürekli çalışarak uyanma kelimesini (Keyword Spotting) dinler.
*   `ses_dinle(self)`: Mikrofondan sesi dinler ve veriyi yakalar.
*   `ses_tanima_isle(self, audio_data)`: Yakalanan sesi Google Speech Recognition servisi ile metne çevirir.
*   `uyanma_kelimesi_kontrol(self, metin)`: "Hey ADA" gibi kelimelerin söylenip söylenmediğini kontrol eder.
*   `komut_isle(self, komut)`: Algılanan metni analiz eder ve uygun fonksiyona yönlendirir.
*   `gemini_ile_komut_isle(self, komut)`: Tanımlı komutlar dışındaki istekleri Gemini yapay zekasına gönderir ve yanıtı seslendirir.

#### Ses Sentezi (TTS)
*   `tts_baslat(self)`: Coqui TTS (Metin Okuma) motorunu başlatır.
*   `seslendirme(self, metin)`: Verilen metni sese çevirir ve çalar.
*   `_ses_cal_threaded(self, ses_dosyasi)`: Sesi arayüzü dondurmadan arka planda çalar.

#### Grafik Arayüz (GUI)
*   `gui_baslat(self)`: Arayüzü ayrı bir thread (iş parçacığı) olarak başlatır.
*   `gui_olustur(self)`: Tkinter kullanarak modern, şeffaf ve sürüklenebilir pencereyi oluşturur.
*   `gui_guncelle(self, kullanici_metni, ada_metni)`: Konuşulanları ve cevapları ekrana yazar.
*   `animasyon_baslat(self)`: Dinleme simgesi ve durum ışığı animasyonlarını yönetir.

#### Sistem Kontrolü
*   `ses_seviyesi_ayarla(self, seviye)`: Bilgisayarın ana ses seviyesini değiştirir.
*   `set_brightness(self, value)`: Ekran parlaklığını WMI üzerinden ayarlar.
*   `wifi_bluetooth_kontrol(...)`: Wi-Fi, Bluetooth, Uçak Modu vb. ayarları Windows arayüz simülasyonu ile değiştirir.
*   `oturum_kontrol(self, aksiyon)`: Bilgisayarı kilitleme veya oturumu kapatma işlemlerini yapar.

#### Medya ve Araçlar
*   `medya_kontrol(self, aksiyon)`: Medya tuşlarını (Oynat/Durdur, İleri, Geri) simüle eder.
*   `fotograf_cek(self)`: Web kamerasını açar, 3 saniye geri sayar ve fotoğrafı `Resimler` klasörüne kaydeder.
*   `web_arama(self, komut)`: Varsayılan tarayıcıda Google araması başlatır.

#### Performans ve Yardımcılar
*   `temizlik_baslat(self)`: Geçici ses dosyalarını periyodik olarak temizler.
*   `hotkey_kurulumu(self)`: `Ctrl+Shift` kısayolunu dinler.
*   `performans_raporu(self)`: Ses tanıma başarısını ve hızını konsola raporlar.
