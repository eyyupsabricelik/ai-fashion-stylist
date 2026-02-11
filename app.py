import streamlit as st
import pandas as pd
import numpy as np
import pickle
from PIL import Image
from sentence_transformers import SentenceTransformer, util
import os
import google.generativeai as genai
import random
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Trendyol AI Stylist", page_icon="👗", layout="wide")

# --- KATEGORİ EŞLEŞTİRME MATRİSİ (Kombin Mantığı) ---
OUTFIT_RULES = {
    # --- KADIN ---
    "Kadin_Elbise": ["Kadin_Topuklu", "Kadin_Canta", "Kadin_Taki"],
    "Kadin_Tisort": ["Kadin_Jean", "Kadin_SporAyakkabi", "Kadin_Canta"],
    "Kadin_Gomlek": ["Kadin_Pantolon", "Kadin_Topuklu", "Kadin_Canta"],
    "Kadin_Pantolon": ["Kadin_Gomlek", "Kadin_Topuklu", "Kadin_Canta"],
    "Kadin_Jean": ["Kadin_Tisort", "Kadin_SporAyakkabi", "Kadin_Canta"],
    "Kadin_Etek": ["Kadin_Bluz", "Kadin_Topuklu", "Kadin_Canta"],
    "Kadin_Bluz": ["Kadin_Etek", "Kadin_Topuklu", "Kadin_Taki"],
    "Kadin_Ceket": ["Kadin_Jean", "Kadin_Tisort", "Kadin_Bot"],
    
    # --- ERKEK ---
    "Erkek_Tisort": ["Erkek_Jean", "Erkek_SporAyakkabi", "Erkek_Saat"],
    "Erkek_Gomlek": ["Erkek_Pantolon", "Erkek_Bot", "Erkek_Saat"],
    "Erkek_Pantolon": ["Erkek_Gomlek", "Erkek_Bot", "Erkek_Kemer"],
    "Erkek_Jean": ["Erkek_Tisort", "Erkek_SporAyakkabi", "Erkek_Saat"],
    "Erkek_Ceket": ["Erkek_Jean", "Erkek_Tisort", "Erkek_Bot"],
    "Erkek_Sweatshirt": ["Erkek_Jean", "Erkek_SporAyakkabi"],
    "Erkek_TakimElbise": ["Erkek_Gomlek", "Erkek_Bot", "Erkek_Saat"],
    "Erkek_Kazak": ["Erkek_Pantolon", "Erkek_Bot"]
}

# --- 1. MODELİ VE VERİYİ YÜKLE ---
@st.cache_resource
def load_model():
    return SentenceTransformer('clip-ViT-B-32')

@st.cache_data
def load_data():
    pkl_path = "dataset/fashion_features.pkl"
    if not os.path.exists(pkl_path): return None
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    return data

# --- ARAYÜZ BAŞLANGICI ---
st.title("👗 Trendyol AI Stylist")
st.markdown("Kıyafetinizi yükleyin, yapay zeka hem **benzerlerini bulsun** hem de **kombin önerisi** yapsın!")

# Sidebar: Ayarlar
st.sidebar.header("⚙️ Ayarlar")
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password", help="Google AI Studio'dan aldığınız anahtarı buraya yapıştırın.")

# Veriyi Yükle
with st.spinner("Moda Veritabanı Yükleniyor..."):
    model = load_model()
    data = load_data()

if data is None:
    st.error("❌ Veri dosyası bulunamadı! Lütfen önce feature_extractor.py çalıştırın.")
    st.stop()

df = data["metadata"]
embeddings = data["embeddings"]

# --- FOTOĞRAF YÜKLEME ---
uploaded_file = st.sidebar.file_uploader("📸 Bir kıyafet resmi seçin...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.sidebar.image(uploaded_file, caption="Seçtiğiniz Parça", use_container_width=True)
    user_image = Image.open(uploaded_file)
    
    # 1. Benzerlik Araması
    query_vector = model.encode(user_image)
    scores = util.cos_sim(query_vector, embeddings)[0]
    
    # TÜR DÖNÜŞÜMÜ HATASI DÜZELTİLDİ
    if hasattr(scores, "cpu"):
        scores = scores.cpu().numpy()
        
    top_k = 5
    top_indices = np.argpartition(-scores, range(top_k))[:top_k]
    
    best_match_idx = int(top_indices[0])
    detected_category = df.iloc[best_match_idx]['category']
    st.sidebar.info(f"🏷️ Algılanan Kategori: **{detected_category}**")

    # --- SEKME YAPISI ---
    tab1, tab2 = st.tabs(["🔍 Benzer Ürünler", "✨ Kombin Asistanı (Gemini)"])
    
    with tab1:
        st.subheader("Mağazadaki En Benzer Parçalar")
        cols = st.columns(5)
        for i, idx in enumerate(top_indices):
            row = df.iloc[idx]
            
            # --- FİYAT GÖRÜNTÜLEME DÜZELTMESİ ---
            price_display = row['price']
            if "0 TL" in str(price_display) or price_display == "0":
                price_display = "Tükendi / Fiyat Yok"
            
            with cols[i]:
                # use_column_width yerine use_container_width kullanıldı (Sarı uyarıyı çözer)
                img_source = row.get('image_url') if 'image_url' in row else row['local_path']
                st.image(img_source, use_container_width=True)
                                        
                st.caption(f"{row['brand']}")
                st.markdown(f"**{price_display}**")
                # İsim uzunsa kısalt
                short_name = row['name'][:35] + "..." if len(row['name']) > 35 else row['name']
                st.text(short_name)
                st.link_button("Git", row['product_url'])

    with tab2:
        if not api_key:
            st.warning("⚠️ Kombin özelliği için lütfen sol menüye Gemini API Anahtarınızı girin.")
        else:
            if st.button("✨ Bu Parçayla Kombin Yap!"):
                target_cats = OUTFIT_RULES.get(detected_category, [])
                
                if not target_cats:
                    st.error("Bu kategori için henüz kombin kuralı tanımlanmadı.")
                else:
                    candidates = []
                    candidate_images = []
                    
                    for cat in target_cats:
                        cat_products = df[df['category'] == cat]
                        if len(cat_products) > 0:
                            samples = cat_products.sample(min(3, len(cat_products)))
                            candidates.append(samples)
                            for _, row in samples.iterrows():
                                try:
                                    # Önce internetteki URL'yi dene (Cloud için şart)
                                    if 'image_url' in row and row['image_url']:
                                        response = requests.get(row['image_url'], stream=True, timeout=5)
                                        img = Image.open(response.raw)
                                    else:
                                        # URL yoksa yerel dosyayı dene (Yedek)
                                        img = Image.open(row['local_path'])
                                    
                                    candidate_images.append(img)
                                except Exception as e:
                                    # Hata olursa pas geç ama konsola yaz (Debug için)
                                    print(f"Resim yüklenemedi: {e}")
                                    pass
                    
                    if not candidate_images:
                        st.error("Kombin için uygun aday ürün bulunamadı.")
                    else:
                        try:
                            genai.configure(api_key=api_key)
                            
                            # --- MODEL DEĞİŞİKLİĞİ ---
                            # Flash sende çalışmadığı için PRO modelini kullanıyoruz.
                            # Bu model sende çalışıyor (sadece önceki denemede isim hatası vardı).
                            gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                            
                            with st.spinner("🤖 Stilist düşünüyor..."):
                                prompt = """
                                Sen uzman bir moda stilistisin.
                                1. İlk resim (kullanıcı resmi) ANA PARÇA.
                                2. Diğerleri ADAY TAMAMLAYICI parçalar.
                                
                                GÖREVİN:
                                Ana parça ile en iyi giden 1 veya 2 parçayı seç.
                                Renk uyumuna ve mevsime dikkat et.
                                
                                Lütfen seçiminizi ve nedenini samimi bir dille Türkçe anlatın.
                                """
                                content = [prompt, user_image] + candidate_images
                                response = gemini_model.generate_content(content)
                                
                                st.success("💡 Öneri Hazır!")
                                col_res, col_exp = st.columns([1, 1])
                                
                                with col_res:
                                    st.subheader("İncelenen Adaylar")
                                    st.image(candidate_images, width=100)
                                
                                with col_exp:
                                    st.subheader("📝 Stilist Notu")
                                    st.markdown(response.text)
                                    st.balloons()
                                    
                        except Exception as e:
                            st.error(f"API Hatası: {e}")

else:
    st.info("👈 Başlamak için sol taraftan bir resim yükleyin!")
    if len(df) > 0:
        st.image(df.sample(1).iloc[0]['local_path'], width=300, caption="Bugünün İlhamı")