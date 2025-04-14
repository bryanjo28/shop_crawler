from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

EXCEL_FILE = "tokped_scrapping.xlsx"

# 🔍 Daftar kata kunci pencarian
keywords = [
    "Mesin EDC BCA",
    "Kertas struk thermal BCA",
    "Adaptor mesin EDC BCA",
    "Charger mesin EDC BCA",
    "Kertas thermal 57x40mm logo BCA",
    "Kertas struk EDC BCA",
    "Kertas struk kasir BCA",
    "Roll kertas kasir BCA",
    "Struk thermal BC4",
    "Mesin kasir BCA"
]

def scroll_down(driver):
    """Fungsi untuk scroll ke bawah secara bertahap."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(3):  # Scroll sebanyak 3 kali untuk memastikan elemen termuat
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Tunggu agar elemen termuat

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Jika tidak ada perubahan tinggi halaman, hentikan scroll
        last_height = new_height

def scrape_page(driver, results, keyword):
    """Fungsi untuk scrape produk di halaman saat ini."""
    try:
        time.sleep(5)
        
        # Scroll ke bawah agar semua produk termuat
        scroll_down(driver)

        # Cari container utama hasil pencarian
        container = driver.find_element(By.CSS_SELECTOR, "div[data-testid='divSRPContentProducts']")
        
        # Ambil semua elemen produk
        product_anchors = container.find_elements(
            By.XPATH, ".//a[contains(@class, 'oQ94Awb6LlTiGByQZo8Lyw')]"
        )

        print(f"🔍 Ditemukan {len(product_anchors)} produk di halaman ini.")

        # Loop untuk ambil detail setiap produk
        for anchor in product_anchors:
            try:
                product_link = anchor.get_attribute("href")
                
                product_name_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, '_0T8-iGxMpV6NEsYEhwkqEg==')]"
                )
                product_name = product_name_el.text

                store_name_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, 'T0rpy-LEwYNQifsgB-3SQw==')]"
                )
                store_name = store_name_el.text
                
                location_el = anchor.find_element(
                    By.XPATH, ".//span[contains(@class, 'pC8DMVkBZGW7-egObcWMFQ==')]"
                )
                store_location = location_el.text
                
                try:
                    rating_el = anchor.find_element(
                        By.XPATH, ".//span[contains(@class, '_9jWGz3C-GX7Myq-32zWG9w==')]"
                    )
                    product_rating = rating_el.text
                except:
                    product_rating = "N/A"
                
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

        return True

    except Exception as e:
        print(f"❌ Gagal mengambil data halaman: {e}")
        return False

def save_to_excel(all_results_by_keyword):
    """Simpan data ke satu Excel file dengan setiap keyword di sheet terpisah."""
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        for keyword, data in all_results_by_keyword.items():
            df = pd.DataFrame(data)
            sheet_name = keyword[:31]  # Nama sheet max 31 karakter
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"✅ Semua data berhasil disimpan ke file '{EXCEL_FILE}' dalam sheet terpisah.")


def go_to_next_page(driver):
    """Fungsi untuk berpindah ke halaman berikutnya jika tersedia."""
    try:
        time.sleep(3)
        
        # Scroll ke bawah untuk memastikan pagination terlihat
        scroll_down(driver)

        next_button = driver.find_element(By.XPATH, "//button[@aria-label='Laman berikutnya']")
        
        if next_button.is_enabled():
            driver.execute_script("arguments[0].click();", next_button)
            print("➡️ Berpindah ke halaman berikutnya...")
            return True
        
    except Exception:
        print("🚫 Tidak ada halaman berikutnya.")
    
    return False

def main():
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=chrome_options)

    all_results_by_keyword = {}  # Dictionary {keyword: list of results}

    try:
        for keyword in keywords:
            print(f"\n🔎 Memulai pencarian untuk: {keyword}")
            driver.get("https://www.tokopedia.com/")
            time.sleep(3)

            search_box = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Cari di Tokopedia']")
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)

            results = []

            while True:
                success = scrape_page(driver, results, keyword)
                if not go_to_next_page(driver):
                    break

            all_results_by_keyword[keyword] = results

        save_to_excel(all_results_by_keyword)
        print("🎉 Semua data berhasil dikumpulkan dan disimpan!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
