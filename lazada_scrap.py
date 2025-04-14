from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

EXCEL_FILE = "lazada_scrapping.xlsx"

keywords = [
    "Mesin EDC BCA",
    "Kertas struk thermal BCA",
    "Adaptor mesin EDC BCA",
    "Charger mesin EDC BCA",
    "Kertas struk EDC BCA",
    "Kertas struk kasir BCA",
    "Roll kertas kasir BCA",
    "Struk thermal BC4",
]

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)

def scroll_down():
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_page(results):
    time.sleep(5)
    scroll_down()
    products = driver.find_elements(By.CLASS_NAME, "Bm3ON")
    print(f"🔍 Ditemukan {len(products)} produk di halaman ini.")
    for product in products:
        try:
            product_name = product.find_element(By.CLASS_NAME, "RfADt").text
            product_price = product.find_element(By.CLASS_NAME, "ooOxS").text
            try:
                sold_count = product.find_element(By.CLASS_NAME, "_1cEkb").text
            except:
                sold_count = "N/A"
            try:
                rating = product.find_element(By.CLASS_NAME, "qzqFw").text
            except:
                rating = "N/A"
            try:
                location = product.find_element(By.CLASS_NAME, "oa6ri").text
            except:
                location = "N/A"
            product_link = product.find_element(By.TAG_NAME, "a").get_attribute("href")

            results.append({
                "Nama Produk": product_name,
                "Harga": product_price,
                "Terjual": sold_count,
                "Rating": rating,
                "Lokasi": location,
                "Link Produk": product_link
            })

        except Exception as e:
            print(f"⚠️ Gagal mengambil data dari produk: {e}")

def go_to_next_page():
    try:
        scroll_down()
        next_button = driver.find_element(By.CLASS_NAME, "ant-pagination-next")
        if "ant-pagination-disabled" in next_button.get_attribute("class"):
            print("🚫 Tidak ada halaman berikutnya.")
            return False
        driver.execute_script("arguments[0].click();", next_button)
        print("➡️ Berpindah ke halaman berikutnya...")
        time.sleep(5)
        return True
    except Exception:
        print("🚫 Tidak ada halaman berikutnya.")
        return False

try:
    all_results_by_keyword = {}

    for keyword in keywords:
        print(f"\n🔎 Mulai pencarian untuk keyword: {keyword}")
        driver.get("https://www.lazada.co.id/")
        time.sleep(5)
        search_box = driver.find_element(By.ID, "q")
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        results = []
        while True:
            scrape_page(results)
            if not go_to_next_page():
                break

        all_results_by_keyword[keyword] = results

    # Save ke Excel dengan sheet per keyword
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        for keyword, data in all_results_by_keyword.items():
            df = pd.DataFrame(data)
            sheet_name = keyword[:31]  # Batas nama sheet Excel = 31 karakter
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n✅ Semua data berhasil disimpan ke '{EXCEL_FILE}' dalam sheet per keyword!")

finally:
    driver.quit()
