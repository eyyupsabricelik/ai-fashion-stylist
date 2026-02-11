import pandas as pd
import numpy as np
import os
from PIL import Image
from sentence_transformers import SentenceTransformer
import pickle

# --- AYARLAR ---
DATASET_CSV = "dataset/trendyol_full_data.csv"
OUTPUT_PKL = "dataset/fashion_features.pkl" 

print("🚀 Feature Engineering Başlıyor...")

# 1. VERİYİ YÜKLE VE TEMİZLE
if not os.path.exists(DATASET_CSV):
    print(f"❌ HATA: {DATASET_CSV} bulunamadı! Lütfen önce scraper.py'yi çalıştır.")
    exit()

df = pd.read_csv(DATASET_CSV)
print(f"📥 Toplam {len(df)} satır veri yüklendi.")

def check_file(path):
    if pd.isna(path): return False
    return os.path.exists(path)

df['file_exists'] = df['local_path'].apply(check_file)
df = df[df['file_exists'] == True].reset_index(drop=True)
print(f"✅ Dosyalar kontrol edildi. İşlenecek: {len(df)}")

# 2. RENK ANALİZİ (Basitleştirilmiş - Çökme Yapmaz)
def get_average_color(image_path):
    """Resimdeki ortalama rengi (R,G,B) döner. KMeans yerine Basit Ortalama."""
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((50, 50)) # Hız için küçült
        
        # Sadece ortadaki alana bak (Kıyafet genelde oradadır)
        w, h = img.size
        img = img.crop((w//4, h//4, 3*w//4, 3*h//4))
        
        # Basit Numpy Ortalaması (KMeans'ten daha hızlı ve güvenli)
        img_array = np.array(img)
        avg_color = img_array.mean(axis=(0, 1)).astype(int)
        return avg_color 
    except:
        return [0, 0, 0]

print("🎨 Renk analizi yapılıyor (Basit Mod)...")
df['dominant_color'] = df['local_path'].apply(get_average_color)
print("✅ Renkler çıkarıldı.")

# 3. VECTOR EMBEDDING (CLIP MODELİ)
print("🧠 CLIP Modeli yükleniyor...")
# Apple Silicon (M1/M2) için 'mps' veya CPU kullanımı otomatiktir
model = SentenceTransformer('clip-ViT-B-32')

print("📸 Görseller vektöre çevriliyor (Embedding)...")
image_paths = df['local_path'].tolist()
images = []
valid_indices = []

for idx, p in enumerate(image_paths):
    try:
        images.append(Image.open(p))
        valid_indices.append(idx)
    except:
        pass

# Batch işlemi
embeddings = model.encode(images, batch_size=32, show_progress_bar=True)

# İndeksleri eşitle
df = df.iloc[valid_indices].reset_index(drop=True)

# 4. KAYDETME
data_package = {
    "metadata": df,              
    "embeddings": embeddings     
}

with open(OUTPUT_PKL, "wb") as f:
    pickle.dump(data_package, f)

print(f"🎉 İŞLEM TAMAM! Veriler '{OUTPUT_PKL}' dosyasına kaydedildi.")
print(f"🧠 Vektör Boyutu: {embeddings.shape}")