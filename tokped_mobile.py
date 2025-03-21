from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

EXCEL_FILE = "tokped_scrapping.xlsx"

def scrape_page(driver, results):
    """Fungsi untuk scrape produk di halaman saat ini."""
    try:
        # 1. Tunggu hingga hasil pencarian muncul
        time.sleep(5)
        
        # 2. Cari container utama hasil pencarian
        container = driver.find_element(By.CSS_SELECTOR, "div[data-testid='divSRPContentProducts']")
        
        # 3. Ambil semua elemen produk
        product_anchors = container.find_elements(
            By.XPATH, ".//a[contains(@class, 'oQ94Awb6LlTiGByQZo8Lyw')]"
        )

        print(f"🔍 Ditemukan {len(product_anchors)} produk di halaman ini.")

        # 4. Loop untuk ambil detail setiap produk
        for anchor in product_anchors:
            try:
                # Link produk
                product_link = anchor.get_attribute("href")
                
                # Nama produk
                product_name_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, '_0T8-iGxMpV6NEsYEhwkqEg==')]"
                )
                product_name = product_name_el.text

                # Nama toko
                store_name_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, 'T0rpy-LEwYNQifsgB-3SQw==')]"
                )
                store_name = store_name_el.text
                
                # Lokasi toko
                location_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, 'pC8DMVkBZGW7-egObcWMFQ==')]"
                )
                store_location = location_el.text
                
                # Rating produk
                try:
                    rating_el = anchor.find_element(
                        By.XPATH, ".//span[contains(@class, '_9jWGz3C-GX7Myq-32zWG9w==')]"
                    )
                    product_rating = rating_el.text
                except:
                    product_rating = "N/A"
                
                # Jumlah terjual
                try:
                    sold_count_el = anchor.find_element(
                        By.XPATH, ".//span[contains(@class, 'se8WAnkjbVXZNA8mT+Veuw==')]"
                    )
                    sold_count = sold_count_el.text
                except:
                    sold_count = "N/A"

                print("=" * 60)
                print(f"Nama Produk  : {product_name}")
                print(f"Nama Toko    : {store_name}")
                print(f"Lokasi Toko  : {store_location}")
                print(f"Rating       : {product_rating}")
                print(f"Terjual      : {sold_count}")
                print(f"Link Produk  : {product_link}")
                print("=" * 60)

                # Simpan hasil scraping
                results.append({
                    "Link Produk": product_link,
                    "Nama Produk": product_name,
                    "Nama Toko": store_name,
                    "Lokasi Toko": store_location,
                    "Rating": product_rating,
                    "Jumlah Terjual": sold_count
                })
            
            except Exception as e:
                print(f"⚠️ Gagal ambil data dari satu produk: {e}")

        return True  # Berhasil scrape halaman ini

    except Exception as e:
        print(f"❌ Gagal mengambil data halaman: {e}")
        return False  # Gagal scrape halaman ini

def save_to_excel(results):
    """Fungsi untuk menyimpan data ke Excel."""
    df = pd.DataFrame(results)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Data berhasil disimpan ke '{EXCEL_FILE}'.")

def go_to_next_page(driver):
    """Fungsi untuk berpindah ke halaman berikutnya jika tersedia."""
    try:
        time.sleep(3)  # Tunggu pagination muncul
        next_button = driver.find_element(By.XPATH, "//button[@aria-label='Laman berikutnya']")
        
        if next_button.is_enabled():
            driver.execute_script("arguments[0].click();", next_button)
            print("➡️ Berpindah ke halaman berikutnya...")
            return True  # Berhasil klik pagination
        
    except Exception:
        print("🚫 Tidak ada halaman berikutnya.")
    
    return False  # Tidak ada pagination lanjut


def main():
    # Konfigurasi Mobile Emulation
    mobile_emulation = {
        "deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"
    }
    # Setup Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Tambahkan Mobile Emulation ke Chrome Options
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(390, 844) 
    # List untuk menyimpan hasil scraping
    results = []

    try:
        # 1. Buka halaman utama Tokopedia
        driver.get("https://www.tokopedia.com/")
        time.sleep(3)  # Tunggu agar halaman termuat
        
        # 2. Cari box pencarian
        search_box = driver.find_element(By.CSS_SELECTOR, "input.css-3017qm.exxxdg63")
        
        # Masukkan kata kunci dan tekan ENTER
        keyword_search = input("Enter keyword: ")
        search_box.send_keys(keyword_search)
        search_box.send_keys(Keys.RETURN)
        
        while True:
            # 3. Scrape halaman saat ini
            success = scrape_page(driver, results)
            
            # 4. Simpan data ke Excel setiap halaman
            if success:
                save_to_excel(results)
            
            # 5. Cek apakah ada pagination untuk ke halaman berikutnya
            if not go_to_next_page(driver):
                break  # Jika tidak ada pagination, hentikan loop

        print("🎉 Semua data berhasil dikumpulkan dan disimpan!")

    finally:
        # 6. Tutup browser setelah scraping selesai
        driver.quit()

if __name__ == "__main__":
    main()
