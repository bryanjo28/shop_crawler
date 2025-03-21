from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

# Nama file Excel untuk menyimpan data
EXCEL_FILE = "lazada_products.xlsx"

# Setup ChromeDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")  # Kurangi log yang tidak perlu
driver = webdriver.Chrome(options=chrome_options)

# List untuk menyimpan hasil scraping
results = []

def scroll_down():
    """Fungsi untuk melakukan scroll ke bawah agar pagination terlihat"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(3):  # Scroll beberapa kali untuk memastikan elemen termuat
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_page():
    """Fungsi untuk scrape semua produk di halaman saat ini"""
    time.sleep(5)
    scroll_down()  # Scroll ke bawah sebelum mengambil data

    products = driver.find_elements(By.CLASS_NAME, "Bm3ON")
    print(f"🔍 Ditemukan {len(products)} produk di halaman ini.")

    for product in products:
        try:
            # Nama produk
            product_name = product.find_element(By.CLASS_NAME, "RfADt").text

            # Harga produk
            product_price = product.find_element(By.CLASS_NAME, "ooOxS").text

            # Jumlah terjual
            try:
                sold_count = product.find_element(By.CLASS_NAME, "_1cEkb").text
            except:
                sold_count = "N/A"

            # Rating
            try:
                rating = product.find_element(By.CLASS_NAME, "qzqFw").text
            except:
                rating = "N/A"

            # Lokasi penjual
            try:
                location = product.find_element(By.CLASS_NAME, "oa6ri").text
            except:
                location = "N/A"

            # Link produk
            product_link = product.find_element(By.TAG_NAME, "a").get_attribute("href")

           

            # Simpan ke list results
            results.append({
                "Nama Produk": product_name,
                "Harga": product_price,
                "Terjual": sold_count,
                "Rating": rating,
                "Lokasi": location,
                "Link Produk": product_link,
            })

        except Exception as e:
            print(f"⚠️ Gagal mengambil data dari produk: {e}")

def go_to_next_page():
    """Fungsi untuk pindah ke halaman berikutnya jika tombol Next tersedia"""
    try:
        scroll_down()  # Pastikan tombol pagination terlihat
        next_button = driver.find_element(By.CLASS_NAME, "ant-pagination-next")

        if "ant-pagination-disabled" in next_button.get_attribute("class"):
            print("🚫 Tidak ada halaman berikutnya.")
            return False

        driver.execute_script("arguments[0].click();", next_button)
        print("➡️ Berpindah ke halaman berikutnya...")
        time.sleep(5)  # Tunggu halaman baru termuat
        return True
    
    except Exception:
        print("🚫 Tidak ada halaman berikutnya.")
        return False

try:
    # 1️⃣ Buka Lazada
    driver.get("https://www.lazada.co.id/")
    time.sleep(5)

    # 2️⃣ Cari search box
    search_box = driver.find_element(By.ID, "q")
    keyword = input("Masukkan kata kunci pencarian: ")
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)  # Tunggu hasil pencarian

    # 3️⃣ Looping scraping hingga tidak ada pagination
    while True:
        scrape_page()  # Ambil data dari halaman saat ini

        # 4️⃣ Simpan ke Excel setiap halaman
        df = pd.DataFrame(results)
        df.to_excel(EXCEL_FILE, index=False)
        print(f"✅ Data berhasil disimpan ke '{EXCEL_FILE}'.")

        # 5️⃣ Cek apakah ada halaman berikutnya
        if not go_to_next_page():
            break  # Jika tidak ada pagination, hentikan loop

    print("🎉 Semua data berhasil dikumpulkan dan disimpan!")

finally:
    driver.quit()  # Tutup browser setelah selesai
