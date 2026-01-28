import streamlit as st
import requests
import pandas as pd
import uuid
from st_supabase_connection import SupabaseConnection

# --- SAYFA AYARLARI (Mobil ve Web Uyumluluk) ---
st.set_page_config(
    page_title="BookPulse Cloud", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BULUT VERİTABANI BAĞLANTISI ---
# Bu kısım Streamlit Cloud üzerindeki "Secrets" kısmından bilgileri otomatik çeker.
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Veritabanı bağlantısı henüz yapılandırılmadı. Lütfen Secrets ayarlarını kontrol edin.")

# --- VERİTABANI İŞLEMLERİ ---
def get_books():
    try:
        res = conn.table("kitaplar").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def add_to_library(bid, title, author, status, img):
    data = {
        "id": bid, 
        "title": title, 
        "author": author, 
        "date": "2026", 
        "durum": status, 
        "image_url": img
    }
    try:
        conn.table("kitaplar").insert(data).execute()
        st.toast(f"✅ '{title}' kütüphaneye eklendi!")
        st.rerun()
    except:
        st.error("Kitap eklenirken bir hata oluştu.")

def delete_book(bid):
    conn.table("kitaplar").delete().eq("id", bid).execute()
    st.rerun()

def update_status(bid, new_status):
    conn.table("kitaplar").update({"durum": new_status}).eq("id", bid).execute()
    st.rerun()

# --- ARAMA MOTORU (Google Books API) ---
def master_search(q):
    results = []
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={q.replace(' ','+')}&maxResults=6"
        res = requests.get(url, timeout=5).json()
        for item in res.get('items', []):
            inf = item['volumeInfo']
            results.append({
                "id": f"WEB_{item['id']}", 
                "title": inf.get('title', 'Bilinmiyor'),
                "author": ", ".join(inf.get('authors', ['Bilinmiyor'])),
                "img": inf.get('imageLinks', {}).get('thumbnail', ""),
                "src": "Global Kaynak"
            })
    except:
        pass
    return results

# --- ARAYÜZ TASARIMI ---
st.title("📚 BookPulse Ultra Cloud")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Yeni Kitap Ekle", "📋 Benim Kütüphanem"])

# --- TAB 1: ARAMA VE EKLEME ---
with tab1:
    q = st.text_input("Kitap, Yazar veya ISBN ara:", placeholder="Örn: Suç ve Ceza")
    col_search, _ = st.columns([1, 4])
    if col_search.button("🔍 Kitabı Bul", use_container_width=True):
        if q:
            with st.spinner('Kitaplar taranıyor...'):
                st.session_state.search_results = master_search(q)
        else:
            st.warning("Lütfen bir isim yazın.")

    if 'search_results' in st.session_state:
        for k in st.session_state.search_results:
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    if k['img']:
                        st.image(k['img'], width=100)
                    else:
                        st.write("📷 Resim Yok")
                with c2:
                    st.subheader(k['title'])
                    st.caption(f"Yazar: {k['author']}")
                    
                    b1, b2, b3 = st.columns(3)
                    if b1.button("⏳ Okuyacağım", key=f"w_{k['id']}", use_container_width=True):
                        add_to_library(k['id'], k['title'], k['author'], "Okuyacağım", k['img'])
                    if b2.button("📖 Okuyorum", key=f"r_{k['id']}", use_container_width=True):
                        add_to_library(k['id'], k['title'], k['author'], "Okuyorum", k['img'])
                    if b3.button("✅ Okudum", key=f"f_{k['id']}", use_container_width=True):
                        add_to_library(k['id'], k['title'], k['author'], "Okudum", k['img'])

# --- TAB 2: LİSTEM ---
with tab2:
    df = get_books()
    
    if not df.empty:
        # İstatistikler
        okundu_sayisi = len(df[df['durum'] == 'Okudum'])
        st.metric("Okuma Hedefi", f"{okundu_sayisi} / {len(df)} Kitap")
        st.progress(okundu_sayisi / len(df))
        st.divider()

        # Kitap Kartları
        for _, row in df.iterrows():
            with st.container(border=True):
                col_img, col_txt, col_act = st.columns([1, 3, 1])
                with col_img:
                    if row['image_url']:
                        st.image(row['image_url'], width=70)
                with col_txt:
                    st.markdown(f"**{row['title']}**")
                    st.caption(f"{row['author']}")
                    
                    # Durum Güncelleme
                    durum_listesi = ["Okuyacağım", "Okuyorum", "Okudum"]
                    mevcut_idx = durum_listesi.index(row['durum']) if row['durum'] in durum_listesi else 0
                    yeni_durum = st.selectbox("Durum", durum_listesi, index=mevcut_idx, key=f"edit_{row['id']}")
                    if yeni_durum != row['durum']:
                        update_status(row['id'], yeni_durum)
                
                with col_act:
                    st.write("") # Boşluk
                    if st.button("🗑️ Sil", key=f"del_{row['id']}", use_container_width=True):
                        delete_book(row['id'])
    else:
        st.info("Kütüphaneniz henüz boş. Arama yaparak kitap eklemeye başlayın!")
