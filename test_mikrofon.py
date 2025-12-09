# -*- coding: utf-8 -*-
"""
Gelişmiş mikrofon test scripti
ADA asistanının mikrofon dinleme fonksiyonunu test eder
"""

import speech_recognition as sr
import time
import threading

def mikrofon_test():
    """Mikrofon fonksiyonunu test et"""
    print("🎤 Mikrofon test başlatılıyor...")
    
    # Recognizer oluştur
    r = sr.Recognizer()
    
    # Optimize edilmiş ayarlar
    r.energy_threshold = 1000
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.6
    r.phrase_threshold = 0.3
    r.non_speaking_duration = 0.5
    
    # Mikrofon oluştur
    mikrofon = sr.Microphone()
    
    print("🔧 Mikrofon kalibre ediliyor...")
    
    # Kalibrasyon
    try:
        with mikrofon as source:
            r.adjust_for_ambient_noise(source, duration=2)
            print(f"📊 Enerji eşiği: {r.energy_threshold}")
    except Exception as e:
        print(f"❌ Kalibrasyon hatası: {e}")
        return
    
    print("✅ Kalibrasyon tamamlandı")
    print("🎤 Şimdi konuşun... (10 saniye test)")
    print("💡 Test kelimeler: 'hey', 'ada', 'merhaba'")
    
    # 10 saniye boyunca dinle
    baslangic = time.time()
    basarili_tanima = 0
    toplam_deneme = 0
    
    while time.time() - baslangic < 10:
        try:
            with mikrofon as source:
                print("👂 Dinleniyor...")
                audio = r.listen(source, timeout=1, phrase_time_limit=3)
                
            try:
                toplam_deneme += 1
                metin = r.recognize_google(audio, language="tr-TR").lower()
                basarili_tanima += 1
                print(f"✅ Tanındı: '{metin}'")
                
                # Wake word kontrolü
                wake_words = ["hey", "ada", "merhaba"]
                for wake_word in wake_words:
                    if wake_word in metin:
                        print(f"🔥 Wake word bulundu: '{wake_word}'")
                        
            except sr.UnknownValueError:
                print("❓ Ses tanınamadı")
            except sr.RequestError as e:
                print(f"❌ Google API hatası: {e}")
                
        except sr.WaitTimeoutError:
            print("⏰ Timeout - devam ediliyor...")
            continue
        except Exception as e:
            print(f"❌ Genel hata: {e}")
            break
    
    # Sonuçlar
    print(f"\n📊 === TEST SONUÇLARI ===")
    print(f"🎯 Toplam deneme: {toplam_deneme}")
    print(f"✅ Başarılı tanıma: {basarili_tanima}")
    if toplam_deneme > 0:
        basari_orani = (basarili_tanima / toplam_deneme) * 100
        print(f"📈 Başarı oranı: {basari_orani:.1f}%")
    print(f"📊 ===================")

def ses_kalitesi_test():
    """Ses kalitesini test et"""
    print("\n🔊 Ses kalitesi test başlatılıyor...")
    
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        
        print("🎤 Mevcut ses giriş cihazları:")
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"  [{i}] {device_info['name']} - {device_info['maxInputChannels']} kanal")
        
        # Varsayılan giriş cihazını göster
        try:
            default_input = p.get_default_input_device_info()
            print(f"\n🎯 Varsayılan giriş: {default_input['name']}")
            print(f"📊 Örnekleme hızı: {default_input['defaultSampleRate']} Hz")
        except:
            print("❌ Varsayılan giriş cihazı bulunamadı")
        
        p.terminate()
        
    except ImportError:
        print("❌ pyaudio yüklü değil - 'pip install pyaudio' çalıştırın")
    except Exception as e:
        print(f"❌ Ses kalitesi test hatası: {e}")

if __name__ == "__main__":
    print("🧪 ADA Mikrofon Test Sistemi")
    print("=" * 40)
    
    # Ses kalitesi testi
    ses_kalitesi_test()
    
    # Ana mikrofon testi
    try:
        mikrofon_test()
    except KeyboardInterrupt:
        print("\n👋 Test kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
    
    print("\n✅ Test tamamlandı")
    input("Devam etmek için Enter'a basın...")