import google.generativeai as genai

# Senin paylaştığın anahtarı buraya ekledim
MY_KEY = "AIzaSyBNi7xiU6yVUoMOSltQ0FosvxgOROjq3Q0"

try:
    genai.configure(api_key=MY_KEY)
    
    print("\n🔍 Google Sunucularında Senin İçin Açık Olan Modeller Aranıyor...\n")
    print("-" * 40)
    
    found_any = False
    for m in genai.list_models():
        # Bize sadece metin/içerik üretebilen modeller lazım
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ BULUNDU: {m.name}")
            found_any = True
            
    print("-" * 40)
    
    if not found_any:
        print("❌ Hata: Anahtar çalışıyor ama hiçbir modele erişim yok.")
    else:
        print("🎉 Süper! Yukarıdaki 'models/...' ile başlayan isimlerden birini seçip kullanacağız.")

except Exception as e:
    print(f"\n🚨 BAĞLANTI HATASI: {e}")
    print("İnternet bağlantını veya VPN durumunu kontrol et.")