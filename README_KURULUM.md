# ADA Asistan Kütüphane Kurulum Rehberi

ADA Asistan projesi, bir dizi güçlü Python kütüphanesi kullanarak sesli etkileşim, yapay zeka ve sistem kontrolü sağlar. Bu belge, gerekli kütüphanelerin nasıl kurulacağını ve projedeki görevlerini açıklar.

## 🚀 1. Otomatik Kurulum

Proje dosyalarında bulunan `ADAkurulumKütüphaneleri.py` dosyası, tüm gerekli kütüphaneleri sizin için otomatik olarak yükleyen bir kurulum sihirbazıdır.

### Nasıl Kullanılır?

1.  Komut satırını (Terminal veya CMD) açın.
2.  Aşağıdaki komutu yazın ve Enter'a basın:
    ```bash
    python ADAkurulumKütüphaneleri.py
    ```
3.  Sihirbaz, eksik kütüphaneleri tarayacak ve otomatik olarak yükleyecektir.
4.  Kurulum tamamlandığında size bir özet rapor sunacaktır.

---

## 📚 2. Kullanılan Kütüphaneler ve Görevleri

Aşağıdaki liste, kurulum dosyasının yüklediği kütüphaneleri ve bu kütüphanelerin ADA Asistan projesindeki işlevlerini detaylandırır.

| Kütüphane Adı | Ne İşe Yarar? (Görev Tanımı) |
| :--- | :--- |
| **`google-generativeai`** | **Yapay Zeka Beyni:** Asistanın zekasını oluşturur. Google'ın Gemini modelini kullanarak kullanıcı ile sohbet eder, soruları yanıtlar ve metin üretir. |
| **`SpeechRecognition`** | **Kulak:** Mikrofondan gelen ses verilerini dinler ve bu sesleri metne (yazıya) çevirir (Speech-to-Text). |
| **`TTS` (Coqui TTS)** | **Dil/Ses:** Asistanın konuşmasını sağlar. Metinleri doğal ve akıcı bir insan sesine dönüştürür (Text-to-Speech). |
| **`pyaudio`** | **Ses Girişi:** Bilgisayarın mikrofonuna erişimi sağlar. `SpeechRecognition` kütüphanesinin sesi duyabilmesi için gereklidir. |
| **`pygame`** | **Ses Çıkışı:** Asistanın ürettiği yanıt seslerini (MP3/WAV) hoparlörden çalmak için kullanılır. |
| **`opencv-python`** | **Göz:** Bilgisayarın kamerasını kontrol eder. "Fotoğraf çek" komutu verildiğinde kamerayı açar, görüntüyü işler ve kaydeder. |
| **`pycaw`** | **Ses Kontrolü:** Windows'un ana ses seviyesini (Volume) programatik olarak değiştirmeyi sağlar (Örn: "Sesi 50 yap"). |
| **`comtypes`** | **Sistem Bağlantısı:** `pycaw` gibi Windows API'lerini kullanan kütüphanelerin sistemle haberleşmesi için gerekli bir yardımcı araçtır. |
| **`keyboard`** | **Kısayollar:** Klavyedeki tuşları dinler. `Ctrl+Shift` gibi kısayol tuşlarıyla asistanın uyandırılmasını sağlar. |
| **`beautifulsoup4`** | **İnternet Tarayıcısı:** Web sayfalarından veri çekmek için kullanılır. Asistanın internetten bilgi toplamasına yardımcı olur. |
| **`requests`** | **İnternet Erişimi:** Web sitelerine bağlanmak ve veri alışverişi yapmak (API istekleri göndermek) için kullanılır. |
| **`Pillow`** | **Görsel İşleme:** Resim dosyalarını açmak, işlemek ve kaydetmek için kullanılır. |

## ⚠️ Olası Kurulum Sorunları ve Çözümleri

*   **`pyaudio` Hatası:** Eğer otomatik kurulumda `pyaudio` hata verirse, sisteminize uygun `.whl` dosyasını [buradan](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) indirip manuel kurmanız gerekebilir.
*   **`TTS` Hatası:** Ses sentezi kütüphanesi bazen C++ derleyicisi gerektirebilir. Hata alırsanız "Visual Studio C++ Build Tools" yüklemeniz gerekebilir.
*   **Yönetici İzni:** Bazı kütüphaneler yüklenirken yönetici izni isteyebilir. Hata durumunda komut satırını "Yönetici olarak çalıştır" seçeneği ile açıp tekrar deneyin.
