import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

COOKIES_FILE = "shopee_cookies.json"
EXCEL_FILE = "shopee_scraping.xlsx"

def load_cookies(driver, cookies_file):
    """Load cookies dari file JSON ke browser Selenium"""
    with open(cookies_file, "r") as f:
        cookies = json.load(f)
        for cookie in cookies:
            cookie.pop("sameSite", None)  # Hapus sameSite jika ada
            driver.add_cookie(cookie)

def save_to_excel(results, file_name):
    """Simpan data ke Excel dengan header jika belum ada"""
    df = pd.DataFrame(results)
    
    if not os.path.exists(file_name):
        # Jika file tidak ada, simpan dengan header
        df.to_excel(file_name, index=False)
    else:
        # Jika file sudah ada, tambahkan data tanpa header
        with pd.ExcelWriter(file_name, mode="a", if_sheet_exists="overlay") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1", header=False, startrow=writer.sheets['Sheet1'].max_row)

    print(f"✅ Data halaman ini berhasil disimpan ke {file_name}")

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
    wait = WebDriverWait(driver, 20)  # Perpanjang waktu tunggu

    try:
        # 1. Buka Shopee
        driver.get("https://shopee.co.id/")
        time.sleep(5)  # Tunggu agar halaman termuat

        # 2. Load cookie dari file
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

        # 5. Cari produk
        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.shopee-searchbar-input__input"))
        )
        keyword_search = input("Masukkan kata kunci pencarian: ")
        search_box.send_keys(keyword_search)
        search_box.send_keys(Keys.ENTER)
        time.sleep(10)  # Tunggu Shopee memuat hasil pencarian

        # Inisialisasi file Excel dengan header jika belum ada
        if not os.path.exists(EXCEL_FILE):
            df_init = pd.DataFrame(columns=["Link Produk", "Nama Produk", "Harga", "Lokasi", "Rating", "Terjual"])
            df_init.to_excel(EXCEL_FILE, index=False)
            print(f"📄 File Excel baru dibuat: {EXCEL_FILE}")

        while True:  # Loop untuk scraping setiap halaman
            # 6. Tunggu hasil pencarian muncul
            print("🔍 Mencoba menemukan elemen hasil pencarian...")
            try:
                product_items = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'relative group border border-solid')]"))
                )
            except:
                print("⚠️ Terjadi error saat mengambil data produk. Mungkin halaman Shopee meminta verifikasi bot.")
                break  # Hentikan program jika bot verification muncul

            print(f"✅ Ditemukan {len(product_items)} produk di halaman ini.")

            # 7. Ambil data produk
            results = []
            for item in product_items:
                try:
                    # Mengambil link produk
                    product_link = item.find_element(By.XPATH, ".//a[@class='contents']").get_attribute("href")

                    # Mengambil nama produk
                    product_name = item.find_element(By.XPATH, ".//div[contains(@class, 'text-sm')]").text

                    # Mengambil harga produk
                    product_price = item.find_element(By.XPATH, ".//div[contains(@class, 'text-shopee-primary')]").text

                    # Mengambil lokasi toko
                    try:
                        store_location = item.find_element(By.XPATH, ".//div[contains(@class, 'text-shopee-black54')]").text
                    except:
                        store_location = "Unknown"

                    # Mengambil rating produk
                    try:
                        product_rating = item.find_element(By.XPATH, ".//div[contains(@class, 'text-shopee-black87')]/div").text
                    except:
                        product_rating = "No Rating"

                    # Mengambil jumlah produk terjual
                    try:
                        sold_count = item.find_element(By.XPATH, ".//div[contains(text(),'Terjual')]").text
                    except:
                        sold_count = "0 Terjual"

                    # Print hasil scraping ke terminal
                    print("=" * 60)
                    print(f"Nama Produk : {product_name}")
                    print(f"Harga       : {product_price}")
                    print(f"Lokasi      : {store_location}")
                    print(f"Rating      : {product_rating}")
                    print(f"Terjual     : {sold_count}")
                    print(f"Link Produk : {product_link}")
                    print("=" * 60)

                    results.append({
                        "Link Produk": product_link,
                        "Nama Produk": product_name,
                        "Harga": product_price,
                        "Lokasi": store_location,
                        "Rating": product_rating,
                        "Terjual": sold_count
                    })

                except Exception as e:
                    print("❌ Gagal mengambil data satu produk:", e)

            # 8. Simpan data ke Excel setiap selesai satu halaman
            if results:
                save_to_excel(results, EXCEL_FILE)

            # 9. Cek apakah masih ada halaman berikutnya
            try:
                current_page = int(wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.shopee-mini-page-controller__current"))
                ).text)
                
                total_pages = int(wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.shopee-mini-page-controller__total"))
                ).text)

                print(f"📄 Halaman {current_page} dari {total_pages}")

                if current_page >= total_pages:
                    print("✅ Scraping selesai! Semua halaman telah diproses.")
                    break  # Keluar dari loop jika sudah di halaman terakhir

                # 10. Klik tombol "Next Page"
                next_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopee-mini-page-controller__next-btn"))
                )
                driver.execute_script("arguments[0].click();", next_button)  # Klik tombol berikutnya dengan JS

                print("⏳ Beralih ke halaman berikutnya...")
                time.sleep(5)  # Tunggu halaman berikutnya termuat

            except Exception as e:
                print(f"❌ Gagal menemukan atau menekan tombol next page: {e}")
                break  # Keluar dari loop jika tombol tidak ditemukan

    finally:
        # 11. Tutup browser
        driver.quit()

if __name__ == "__main__":
    main()
