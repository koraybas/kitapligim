import streamlit as st
import requests
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="BookPulse Ultra", page_icon="📚", layout="wide")

# --- BULUT BAĞLANTISI ---
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    st.error("Veritabanı bağlantısı kurulamadı.")

# --- FONKSİYONLAR ---
def get_books():
    try:
        res = conn.table("kitaplar").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def add_to_library(bid, title, author, status, img):
    data = {"id": bid, "title": title, "author": author, "date": "2026", "durum": status, "image_url": img}
    conn.table("kitaplar").insert(data).execute()
    st.toast(f"✅ {title} eklendi!")
    st.rerun()

# --- GOOGLE API DESTEKLİ ARAMA MOTORU ---
def master_search(q):
    results = []
    try:
        # Secrets'tan hem Google Key'i hem de Supabase bilgilerini güvenli çekiyoruz
        google_key = st.secrets["api_keys"]["GOOGLE_BOOKS"]
        query = q.replace(' ', '+')
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&key={google_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                inf = item.get('volumeInfo', {})
                # Resim URL'sini HTTPS yaparak güvenli hale getiriyoruz
                img_url = inf.get('imageLinks', {}).get('thumbnail', "").replace("http://", "https://")
                results.append({
                    "id": item.get('id'),
                    "title": inf.get('title', 'Bilinmiyor'),
                    "author": ", ".join(inf.get('authors', ['Bilinmiyor'])),
                    "img": img_url
                })
        else:
            st.error(f"Google Servis Hatası: {response.status_code}. Lütfen API Key'i kontrol edin.")
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
    return results

# --- ARAYÜZ ---
st.title("📚 BookPulse Ultra")

tab1, tab2 = st.tabs(["🔍 Kitap Ara & Ekle", "📋 Listem"])

with tab1:
    col_input, col_btn = st.columns([4, 1])
    search_query = col_input.text_input("Kitap veya Yazar Adı:", key="search_text", placeholder="Örn: Simyacı")
    
    if col_btn.button("🔍 Ara", use_container_width=True):
        if search_query:
            with st.spinner('Kitaplar aranıyor...'):
                st.session_state['results'] = master_search(search_query)

    if 'results' in st.session_state and st.session_state['results']:
        for k in st.session_state['results']:
            with st.container(border=True):
                c1, c2 = st.columns([1, 5])
                with c1:
                    if k['img']: st.image(k['img'], width=80)
                with c2:
                    st.subheader(k['title'])
                    st.write(f"✍️ {k['author']}")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("⏳ Okuyacağım", key=f"w_{k['id']}"): add_to_library(k['id'], k['title'], k['author'], "Okuyacağım", k['img'])
                    if b2.button("📖 Okuyorum", key=f"r_{k['id']}"): add_to_library
