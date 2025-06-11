import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

EXCEL_FILE = "fb_marketplace_scraping.xlsx"
COOKIES_FILE = "facebook_cookies.json"

# 🔍 Kata-kunci pencarian
KEYWORDS = [
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

def load_cookies(driver, file_path):
    """Muat cookies Facebook ke dalam sesi Selenium."""
    with open(file_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for ck in cookies:
        # Hapus properti 'sameSite' (tidak dikenali oleh Selenium)
        ck.pop("sameSite", None)
        driver.add_cookie(ck)

def scroll_once(driver, pause=2):
    """Scroll sekali ke dasar halaman untuk memancing lazy-loading."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause)

def scrape_current_page(driver):
    results = []
    scroll_once(driver)

    anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'/marketplace/item/')]")
    print(f"[INFO] Ditemukan {len(anchors)} listing.")

    for a in anchors:
        try:
            link = a.get_attribute("href")

            # Nama produk berdasarkan style khas Facebook untuk judul
            try:
                title = a.find_element(By.XPATH, ".//span[contains(@style,'-webkit-line-clamp')]").text
            except:
                title = "N/A"

            # Harga (berisi Rp atau IDR)
            try:
                price = a.find_element(By.XPATH, ".//span[contains(text(),'IDR') or contains(text(),'Rp')]").text
            except:
                price = "N/A"

            # Lokasi (mengandung koma)
            try:
                location = a.find_element(By.XPATH, ".//span[contains(text(),',')]").text
            except:
                location = "N/A"

            results.append({
                "Nama Produk": title,
                "Harga": price,
                "Lokasi": location,
                "Link": link
            })

        except Exception as e:
            print(f"[WARN] Gagal parsing listing: {e}")

    return results


def save_to_excel(data_per_keyword):
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        for kw, rows in data_per_keyword.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=kw[:31], index=False)
    print(f"[DONE] Data tersimpan di '{EXCEL_FILE}'.")

def main():
    chrome_opt = Options()
    chrome_opt.add_argument("--log-level=3")
    # ➜ Jika ingin headless, aktifkan baris di bawah:
    # chrome_opt.add_argument("--headless=new")

    driver = webdriver.Chrome(options=chrome_opt)

    try:
        # 1) Buka facebook.com agar domain sesuai sebelum memasukkan cookie
        driver.get("https://www.facebook.com/")
        time.sleep(2)
        load_cookies(driver, COOKIES_FILE)
        driver.refresh()
        time.sleep(5)   # beri waktu memuat ulang dengan cookie

        # 2) Pastikan sudah login
        if "login" in driver.current_url:
            raise RuntimeError("Cookie tidak valid atau sudah kedaluwarsa – silakan perbarui.")

        all_results = {}

        for kw in KEYWORDS:
            print(f"\n🔎 Mencari: {kw}")
            # Buka halaman Marketplace utama
            driver.get("https://www.facebook.com/marketplace/")
            time.sleep(4)

            # Cari kotak pencarian Marketplace
            search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search Marketplace']")
            search_box.clear()
            search_box.send_keys(kw)
            search_box.send_keys(Keys.RETURN)
            time.sleep(5)  # tunggu hasil

            # Scrape hanya halaman pertama
            page_rows = scrape_current_page(driver)
            all_results[kw] = page_rows

        # 3) Simpan
        save_to_excel(all_results)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
