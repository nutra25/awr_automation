import pyawr.mwoffice as mwoffice
import time
import pyautogui  # Klavye simülasyonu için
import ctypes  # Windows API'sine erişip aktif pencereyi bulmak için


def run_load_pull_template_script():
    app = mwoffice.CMWOffice()

    # AWR'nin ana pencere kimliğini (Handle - hWnd) alıyoruz [Kaynak: 205]
    main_hwnd = app.hWnd

    for module in app.GlobalScripts:
        for routine in module.Routines:
            isim = routine.Name.lower()

            if "load" in isim and "pull" in isim and "template" in isim:
                print(f"Modül: {module.Name} | Rutin: {routine.Name} çalıştırılıyor...")

                # 1. Scripti çalıştır (Kod bloklanmadan devam edecek)
                routine.Run()

                # 2. DİNAMİK BEKLEME: Mesaj kutusunun açılmasını bekle
                print("Mesaj kutusunun açılması bekleniyor...")
                timeout = 10.0  # Maksimum bekleme süresi (Sonsuz döngüyü önlemek için)
                start_time = time.time()

                while time.time() - start_time < timeout:
                    # Windows'ta o an en önde/aktif olan pencerenin kimliğini al
                    active_hwnd = ctypes.windll.user32.GetForegroundWindow()

                    # Eğer aktif pencere AWR'nin ana penceresi değilse (yani bir pop-up açıldıysa)
                    if active_hwnd != 0 and active_hwnd != main_hwnd:

                        # Emin olmak için açılan pencerenin başlığını okuyalım
                        length = ctypes.windll.user32.GetWindowTextLengthW(active_hwnd)
                        buf = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(active_hwnd, buf, length + 1)
                        window_title = buf.value

                        # Pencere başlığı "Script Info", "AWR Design Environment" vb. ise
                        if "Script" in window_title or "Info" in window_title or "AWR" in window_title:
                            # Pencerenin tam olarak çizilmesi için çok ufak bir süre tanı (100 milisaniye)
                            time.sleep(0.1)

                            # Otomatik olarak 'Enter' tuşuna bas
                            pyautogui.press('enter')
                            print(f"[BAŞARILI] '{window_title}' penceresi algılandı ve otomatik geçildi.")
                            return

                    # İşlemciyi yormamak için döngüde çok kısa bekle
                    time.sleep(0.1)

                print("[BİLGİ] İşlem tamamlandı, ancak zaman aşımı süresince bir mesaj kutusu algılanmadı.")
                return


if __name__ == "__main__":
    run_load_pull_template_script()