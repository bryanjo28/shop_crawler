import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EXCEL_FILE = "shopee_scraping_detail.xlsx"
COOKIES_FILE = "shopee_cookies.json"

def load_cookies(driver, cookies_file):
    """Load cookie dari file JSON ke browser Selenium"""
    try:
        with open(cookies_file, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                # Hapus "sameSite" jika ada untuk kompatibilitas
                cookie.pop("sameSite", None)
                driver.add_cookie(cookie)
        print("✅ Cookies berhasil dimuat.")
    except FileNotFoundError:
        print("❌ File cookies tidak ditemukan! Pastikan sudah login dan menyimpan cookies.")
    except Exception as e:
        print(f"⚠️ Gagal memuat cookies: {e}")

def main():
    # Setup ChromeDriver dengan mode Incognito
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Gunakan User-Agent agar lebih mirip pengguna asli
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)  # Atur waktu tunggu maksimal

    try:
        # 1. Buka halaman utama Shopee terlebih dahulu
        driver.get("https://shopee.co.id/")
        time.sleep(5)  # Tunggu halaman termuat

        # 2. Load cookie dari file untuk melewati login
        load_cookies(driver, COOKIES_FILE)
        time.sleep(3)

        # 3. Refresh halaman agar cookie diterapkan
        driver.refresh()
        time.sleep(5)

        # 4. Pastikan halaman tidak redirect ke login
        if "/login" in driver.current_url:
            print("❌ Masih diarahkan ke halaman login! Cek kembali cookie yang digunakan.")
            driver.quit()
            return

        print("✅ Berhasil melewati login Shopee!")

        # 5. Membaca file Excel dan mendapatkan semua link produk
        df = pd.read_excel(EXCEL_FILE)

        if "Link Produk" not in df.columns:
            print("❌ Kolom 'Link Produk' tidak ditemukan di file Excel.")
            return

        product_links = df["Link Produk"].dropna().tolist()
        print(f"🔍 Ditemukan {len(product_links)} link produk untuk diproses.")

        for index, link in enumerate(product_links):
            try:
                print(f"📌 Memproses produk {index + 1} dari {len(product_links)}")
                driver.get(link)
                time.sleep(5)  # Tunggu halaman produk termuat

                # 6. Tekan tombol "Laporkan"
                try:
                    report_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'YysGiT') and text()='Laporkan']"))
                    )
                    driver.execute_script("arguments[0].click();", report_button)
                    print("✅ Tombol 'Laporkan' diklik.")
                    time.sleep(3)  # Tunggu popup muncul
                except:
                    print("⚠️ Tombol 'Laporkan' tidak ditemukan, lanjut ke produk berikutnya.")
                    continue  # Skip ke produk berikutnya

                # 7. Pilih alasan pelanggaran "Produk melanggar hak cipta atau distribusi"
                try:
                    reason_option = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//li[contains(text(), 'Produk melanggar hak cipta atau distribusi')]"))
                    )
                    driver.execute_script("arguments[0].click();", reason_option)
                    print("✅ Alasan 'Produk melanggar hak cipta atau distribusi' dipilih.")
                except:
                    print("❌ Gagal memilih alasan laporan.")
                    continue  # Skip ke produk berikutnya

                # 8. Isi textarea dengan deskripsi laporan
                try:
                    report_textarea = wait.until(
                        EC.presence_of_element_located((By.XPATH, "//textarea"))
                    )
                    report_textarea.send_keys("Kertas edc berlogo bank tidak boleh dijualbelikan")
                    print("✅ Deskripsi laporan berhasil diisi.")
                except:
                    print("❌ Gagal mengisi deskripsi laporan.")
                    continue  # Skip ke produk berikutnya

                # 9. Tekan tombol "Kirim Laporan"
                try:
                    submit_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-solid-primary') and text()='Kirim Laporan']"))
                    )
                    driver.execute_script("arguments[0].click();", submit_button)
                    print("✅ Laporan berhasil dikirim.")
                except:
                    print("❌ Gagal menekan tombol 'Kirim Laporan'.")

                time.sleep(5)  # Tunggu sebelum pindah ke produk berikutnya

            except Exception as e:
                print(f"⚠️ Terjadi kesalahan saat memproses produk {index + 1}: {e}")

    finally:
        # 10. Tutup browser setelah selesai
        driver.quit()
        print("🚀 Selesai! Semua produk telah diproses.")

if __name__ == "__main__":
    main()
