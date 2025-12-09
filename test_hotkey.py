# -*- coding: utf-8 -*-
import keyboard
import time

def test_hotkey():
    print("Hotkey test başlatılıyor...")
    print("Ctrl+Shift tuşuna basın (Çıkmak için ESC)")
    
    def hotkey_handler():
        print("Ctrl+Shift tusu algilandi!")
        print("Dinliyorum...")
    
    try:
        keyboard.add_hotkey('ctrl+shift', hotkey_handler)
        print("Hotkey kuruldu. Ctrl+Shift'e basın...")
        
        # ESC tuşuna basılana kadar bekle
        keyboard.wait('esc')
        print("Test sonlandırıldı.")
        
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        keyboard.unhook_all_hotkeys()

if __name__ == "__main__":
    test_hotkey()