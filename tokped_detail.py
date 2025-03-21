import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_FILE = "tokped_cookies.json"
EXCEL_FILE = "tokped_scrapping.xlsx"

def load_cookies(driver, cookies_file):
    """Memuat cookies dari file JSON ke browser untuk login."""
    with open(cookies_file, "r") as f:
        cookies = json.load(f)
        for cookie in cookies:
            cookie.pop("sameSite", None)  # Hapus atribut sameSite jika ada
            driver.add_cookie(cookie)

def report_product(driver, product_link):
    """Melakukan pelaporan produk di halaman Tokopedia."""
    driver.get(product_link)
    time.sleep(5)  # Tunggu halaman termuat
    
    wait = WebDriverWait(driver, 10)

    try:
        # 1. Klik tombol "Laporkan"
        report_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='btnReportProduct']"))
        )
        driver.execute_script("arguments[0].click();", report_button)
        print("✅ Tombol 'Laporkan' diklik.")
        time.sleep(3)  # Tunggu modal muncul

        # 2. Tunggu modal pelaporan muncul
        report_modal = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "css-1sehla9-unf-modal"))
        )
        print("✅ Modal pelaporan muncul.")

        # 3. Scroll ke radio button alasan "Duplikasi Produk"
        reason_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//li[@id='Report-radio-4']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", reason_button)
        time.sleep(1)

        # 4. Coba klik radio button dengan JavaScript jika tidak bisa diklik langsung
        driver.execute_script("arguments[0].click();", reason_button)
        print("✅ Alasan 'Duplikasi Produk' dipilih.")

        # 5. Isi textarea dengan laporan
        report_textarea = wait.until(
            EC.presence_of_element_located((By.XPATH, "//textarea[@name='report_content']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", report_textarea)
        report_textarea.send_keys("Produk dari bank tidak boleh diperjualbelikan")
        print("✅ Deskripsi laporan diisi.")

        # 6. Centang checkbox persetujuan
        checkbox = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
        )
        driver.execute_script("arguments[0].click();", checkbox)
        print("✅ Checkbox persetujuan dicentang.")

        # 7. Klik tombol "Report"
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='btnSubmitReport']"))
        )
        driver.execute_script("arguments[0].click();", submit_button)
        print("✅ Laporan berhasil dikirim.")

        time.sleep(3)  # Tunggu sebelum pindah ke produk berikutnya
        return True  # Berhasil melaporkan produk

    except Exception as e:
        print(f"❌ Gagal melaporkan produk: {product_link} - {e}")
        return False  # Gagal melaporkan produk

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
    
    wait = WebDriverWait(driver, 15)

    try:
        # 1. Buka Tokopedia
        driver.get("https://www.tokopedia.com/")
        time.sleep(3)  # Tunggu agar halaman termuat

        # 2. Load cookie dari file
        load_cookies(driver, COOKIES_FILE)
        time.sleep(3)

        # 3. Refresh halaman agar cookie diterapkan
        driver.refresh()
        time.sleep(5)

        # 4. Pastikan halaman tidak redirect ke login
        if "login" in driver.current_url:
            print("❌ Masih diarahkan ke halaman login! Cek kembali cookie yang digunakan.")
            driver.quit()
            return

        print("✅ Berhasil login ke Tokopedia!")

        # 5. Membaca file Excel dan mendapatkan semua link produk
        df = pd.read_excel(EXCEL_FILE)

        if "Link Produk" not in df.columns:
            print("❌ Kolom 'Link Produk' tidak ditemukan di file Excel.")
            return

        product_links = df["Link Produk"].dropna().tolist()
        print(f"🔍 Ditemukan {len(product_links)} link produk untuk diproses.")

        for index, link in enumerate(product_links):
            print(f"📌 Memproses produk {index + 1} dari {len(product_links)}")
            success = report_product(driver, link)

            if success:
                print(f"✅ Produk {index + 1} berhasil dilaporkan!")
            else:
                print(f"❌ Gagal melaporkan produk {index + 1}.")

    finally:
        # 6. Tutup browser setelah selesai
        driver.quit()
        print("🚀 Selesai! Semua produk telah diproses.")

if __name__ == "__main__":
    main()
