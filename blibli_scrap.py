from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

# Nama file Excel untuk menyimpan data
EXCEL_FILE = "blibli_products.xlsx"

# Setup ChromeDriver
def setup_driver():
    """Fungsi untuk mengonfigurasi driver"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")  # Minimalkan log ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Scroll ke bawah agar elemen termuat
def scroll_down(driver):
    """Fungsi untuk melakukan scroll ke bawah agar pagination terlihat"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(3):  # Scroll beberapa kali untuk memastikan elemen termuat
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Fungsi untuk mengambil data produk
def scrape_page(driver):
    """Fungsi untuk scrape semua produk di halaman saat ini"""
    time.sleep(5)
    scroll_down(driver)  # Scroll ke bawah sebelum mengambil data

    products = driver.find_elements(By.CSS_SELECTOR, '.product-item')
    print(f"🔍 Ditemukan {len(products)} produk di halaman ini.")

    results = []
    for product in products:
        try:
            # Nama produk
            product_name = product.find_element(By.CSS_SELECTOR, '.product-title').text

            # Harga produk
            product_price = product.find_element(By.CSS_SELECTOR, '.price').text

            # Link produk
            product_link = product.find_element(By.TAG_NAME, "a").get_attribute("href")

            # Simpan ke list results
            results.append({
                "Nama Produk": product_name,
                "Harga": product_price,
                "Link Produk": product_link,
            })

        except Exception as e:
            print(f"⚠️ Gagal mengambil data dari produk: {e}")
    return results

# Fungsi untuk pindah ke halaman berikutnya
def go_to_next_page(driver):
    """Fungsi untuk pindah ke halaman berikutnya jika tombol Next tersedia"""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
        if "disabled" in next_button.get_attribute("class"):
            print("🚫 Tidak ada halaman berikutnya.")
            return False

        driver.execute_script("arguments[0].click();", next_button)
        print("➡️ Berpindah ke halaman berikutnya...")
        time.sleep(5)  # Tunggu halaman baru termuat
        return True
    
    except Exception:
        print("🚫 Tidak ada halaman berikutnya.")
        return False

# Utama script
def main():
    """Fungsi utama untuk scraping"""
    # Setup WebDriver
    driver = setup_driver()

    try:
        # 1️⃣ Buka Blibli
        driver.get("https://www.blibli.com")
        time.sleep(5)

        # 2️⃣ Cari search box dan masukkan kata kunci
        search_box = driver.find_element(By.CSS_SELECTOR, 'input[name="search"]')
        keyword = input("Masukkan kata kunci pencarian: ")
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)  # Tunggu hasil pencarian

        # 3️⃣ Looping scraping hingga tidak ada pagination
        results = []
        while True:
            # 4️⃣ Ambil data produk dari halaman
            page_results = scrape_page(driver)
            results.extend(page_results)

            # 5️⃣ Simpan ke Excel setiap halaman
            df = pd.DataFrame(results)
            df.to_excel(EXCEL_FILE, index=False)
            print(f"✅ Data berhasil disimpan ke '{EXCEL_FILE}'.")

            # 6️⃣ Cek apakah ada halaman berikutnya
            if not go_to_next_page(driver):
                break  # Jika tidak ada pagination, hentikan loop

        print("🎉 Semua data berhasil dikumpulkan dan disimpan!")

    finally:
        driver.quit()  # Tutup browser setelah selesai

# Jalankan program utama
if __name__ == "__main__":
    main()
