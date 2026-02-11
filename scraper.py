import time
import os
import pandas as pd
import requests
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 30 KATEGORİLİK DEV LİSTE ---
CATEGORIES = {
    # --- KADIN ---
    "Kadin_Elbise": "https://www.trendyol.com/kadin-elbise-x-g1-c56",
    "Kadin_Tisort": "https://www.trendyol.com/kadin-tisort-x-g1-c73",
    "Kadin_Gomlek": "https://www.trendyol.com/kadin-gomlek-x-g1-c75",
    "Kadin_Pantolon": "https://www.trendyol.com/kadin-pantolon-x-g1-c70",
    "Kadin_Jean": "https://www.trendyol.com/kadin-jeans-x-g1-c120",
    "Kadin_Ceket": "https://www.trendyol.com/kadin-ceket-x-g1-c1030",
    "Kadin_Mont": "https://www.trendyol.com/kadin-mont-x-g1-c118",
    "Kadin_Kazak": "https://www.trendyol.com/kadin-kazak-x-g1-c1092",
    "Kadin_Etek": "https://www.trendyol.com/kadin-etek-x-g1-c69",
    "Kadin_Sort": "https://www.trendyol.com/kadin-sort-x-g1-c119",
    "Kadin_Topuklu": "https://www.trendyol.com/topuklu-ayakkabi-x-c107",
    "Kadin_SporAyakkabi": "https://www.trendyol.com/kadin-spor-ayakkabi-x-g1-c109",
    "Kadin_Canta": "https://www.trendyol.com/kadin-canta-x-g1-c117",
    "Kadin_Taki": "https://www.trendyol.com/kadin-taki-mucevher-x-g1-c27",
    "Kadin_Bluz": "https://www.trendyol.com/kadin-bluz-x-g1-c1019",

    # --- ERKEK ---
    "Erkek_Tisort": "https://www.trendyol.com/erkek-t-shirt-x-g2-c73",
    "Erkek_Gomlek": "https://www.trendyol.com/erkek-gomlek-x-g2-c75",
    "Erkek_Pantolon": "https://www.trendyol.com/erkek-pantolon-x-g2-c70",
    "Erkek_Jean": "https://www.trendyol.com/erkek-jeans-x-g2-c120",
    "Erkek_Ceket": "https://www.trendyol.com/erkek-ceket-x-g2-c1030",
    "Erkek_Mont": "https://www.trendyol.com/erkek-mont-x-g2-c118",
    "Erkek_Sweatshirt": "https://www.trendyol.com/erkek-sweatshirt-x-g2-c1179",
    "Erkek_Kazak": "https://www.trendyol.com/erkek-kazak-x-g2-c1092",
    "Erkek_TakimElbise": "https://www.trendyol.com/erkek-takim-elbise-x-g2-c67",
    "Erkek_SporAyakkabi": "https://www.trendyol.com/erkek-spor-ayakkabi-x-g2-c109",
    "Erkek_Bot": "https://www.trendyol.com/erkek-bot-x-g2-c1025",
    "Erkek_Saat": "https://www.trendyol.com/erkek-saat-x-g2-c34",
    "Erkek_Sort": "https://www.trendyol.com/erkek-sort-x-g2-c119",
    "Erkek_IcGiyim": "https://www.trendyol.com/erkek-ic-giyim-x-g2-c63",
    "Erkek_Aksesuar": "https://www.trendyol.com/erkek-aksesuar-x-g2-c27"
}

# --- AYARLAR ---
SCROLL_COUNT_PER_CAT = 4  # Her kategori için kaç kez aşağı kaydırsın? (Yaklaşık 100 ürün/kategori)
IMAGE_SAVE_FOLDER = "dataset/images"
OUTPUT_CSV = "dataset/trendyol_full_data.csv"

# --- CONFIG (Değişmez) ---
SITE_CONFIG = {
    "card_selector": "product-card",
    "brand_selector": "product-brand",
    "name_selector": "product-name",
    "price_selector": "price-value",
    "image_selector": "image"
}

if not os.path.exists(IMAGE_SAVE_FOLDER):
    os.makedirs(IMAGE_SAVE_FOLDER)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def download_image(img_url, product_id):
    if not img_url: return None
    # Dosya zaten varsa tekrar indirme (Hız kazandırır)
    file_path = os.path.join(IMAGE_SAVE_FOLDER, f"{product_id}.jpg")
    if os.path.exists(file_path):
        return file_path
        
    try:
        response = requests.get(img_url, timeout=10)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path
    except:
        return None

def main():
    driver = setup_driver()
    all_data = []
    
    print(f"🚀 Dev Tarama Başlıyor! Hedef: {len(CATEGORIES)} Kategori")
    
    # KATEGORİLERİ DÖNGÜYE ALIYORUZ
    for cat_name, cat_url in CATEGORIES.items():
        print(f"\n📂 Kategoriye Gidiliyor: {cat_name}...")
        try:
            driver.get(cat_url)
            
            # Sayfa yüklenmesini bekle
            try:
                WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                print("⚠️ Sayfa geç yüklendi, devam ediliyor...")

            # Scroll işlemi
            for i in range(SCROLL_COUNT_PER_CAT):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(1.0, 2.0)) # Biraz daha hızlı scroll

            # Kartları bul
            cards = driver.find_elements(By.CLASS_NAME, SITE_CONFIG["card_selector"])
            print(f"   -> {len(cards)} ürün bulundu. Veriler alınıyor...")

            cat_count = 0
            for card in cards:
                try:
                    product_link = card.get_attribute("href")
                    
                    # ID Çıkarma
                    if "p-" in product_link:
                        product_id = product_link.split("p-")[-1].split("?")[0]
                    else:
                        product_id = product_link.split("/")[-1].split("?")[0][-10:]

                    # Marka ve İsim
                    try:
                        brand = card.find_element(By.CLASS_NAME, SITE_CONFIG["brand_selector"]).text
                        name = card.find_element(By.CLASS_NAME, SITE_CONFIG["name_selector"]).text
                    except:
                        brand = "Unknown"
                        name = "Unknown Product"

                    # Fiyat
                    try:
                        price = card.find_element(By.CLASS_NAME, SITE_CONFIG["price_selector"]).text
                    except:
                        price = "0 TL"

                    # Resim
                    try:
                        img_element = card.find_element(By.CLASS_NAME, SITE_CONFIG["image_selector"])
                        img_url = img_element.get_attribute("src")
                        if not img_url: img_url = img_element.get_attribute("data-src")
                    except:
                        img_url = None

                    if img_url and product_link:
                        all_data.append({
                            "category": cat_name, # KATEGORİ BİLGİSİNİ EKLİYORUZ
                            "product_id": product_id,
                            "brand": brand,
                            "name": name,
                            "price": price,
                            "image_url": img_url,
                            "product_url": product_link
                        })
                        cat_count += 1
                except:
                    continue
            
            print(f"   ✅ {cat_name}: {cat_count} ürün havuza eklendi.")
            
        except Exception as e:
            print(f"❌ {cat_name} hatası: {e}")
            continue

    driver.quit()
    
    # --- KAYDETME VE İNDİRME ---
    print(f"\n📊 TOPLAM {len(all_data)} ÜRÜN TOPLANDI. İNDİRME BAŞLIYOR...")
    
    if len(all_data) > 0:
        df = pd.DataFrame(all_data)
        
        # Resimleri indir (Progress bar gibi çalışır)
        print("📸 Resimler indiriliyor (Bu işlem biraz sürebilir)...")
        # Basit bir sayacı print edelim
        total_imgs = len(df)
        for index, row in df.iterrows():
            if index % 50 == 0: print(f"   İlerleme: {index}/{total_imgs}")
            df.at[index, 'local_path'] = download_image(row['image_url'], row['product_id'])
        
        df = df.dropna(subset=['local_path'])
        
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"🎉 BÜYÜK BAŞARI! Tüm veri seti hazır: {OUTPUT_CSV}")
        print("➡️ Şimdi 'feature_extractor.py' dosyasını çalıştır (Dosya ismini güncellemeyi unutma!)")
    else:
        print("❌ Hiç veri toplanamadı.")

if __name__ == "__main__":
    main()