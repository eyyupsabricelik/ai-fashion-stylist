import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def xray_scan():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print("🚀 Trendyol'a gidiliyor...")
    driver.get("https://www.trendyol.com/erkek-t-shirt-x-g2-c73")
    time.sleep(5) 
    
    print("👀 'product-card' aranıyor...")
    cards = driver.find_elements(By.CLASS_NAME, "product-card")
    
    if len(cards) > 0:
        print(f"✅ {len(cards)} adet kart bulundu. İşte ilkinin röntgeni:")
        print("-" * 50)
        # Kartın HTML kodunu alıp ekrana basıyoruz
        print(cards[0].get_attribute('outerHTML'))
        print("-" * 50)
        print("Lütfen yukarıdaki HTML kodunu kopyalayıp bana at!")
    else:
        print("❌ Kart bulunamadı! Trendyol yine sınıf ismini değiştirmiş olabilir.")

    driver.quit()

if __name__ == "__main__":
    xray_scan()