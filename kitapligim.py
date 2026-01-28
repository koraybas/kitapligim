import streamlit as st
import requests
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="BookPulse Cloud", page_icon="📚", layout="wide")

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

# --- GELİŞTİRİLMİŞ ARAMA MOTORU ---
def master_search(q):
    results = []
    try:
        # Boşlukları + ile değiştiriyoruz ve güvenli bağlantı kuruyoruz
        query = q.replace(' ', '+')
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                inf = item.get('volumeInfo', {})
                results.append({
                    "id": item.get('id'),
                    "title": inf.get('title', 'Bilinmiyor'),
                    "author": ", ".join(inf.get('authors', ['Bilinmiyor'])),
                    "img": inf.get('imageLinks', {}).get('thumbnail', "").replace("http://", "https://")
                })
        else:
            st.error(f"Google Servis Hatası: {response.status_code}")
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
    return results

# --- ARAYÜZ ---
st.title("📚 BookPulse Ultra")

tab1, tab2 = st.tabs(["🔍 Kitap Ara & Ekle", "📋 Listem"])

with tab1:
    # Arama kutusu ve butonu yanyana
    col_input, col_btn = st.columns([4, 1])
    search_query = col_input.text_input("Kitap veya Yazar Adı:", key="search_text", placeholder="Örn: Simyacı")
    
    if col_btn.button("🔍 Ara", use_container_width=True) or search_query:
        if search_query:
            with st.spinner('Kitaplar aranıyor...'):
                # Sonuçları session_state'e kaydediyoruz ki sayfa yenilendiğinde gitmesin
                st.session_state['results'] = master_search(search_query)

    # Sonuçları ekrana bas
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
                    if b2.button("📖 Okuyorum", key=f"r_{k['id']}"): add_to_library(k['id'], k['title'], k['author'], "Okuyorum", k['img'])
                    if b3.button("✅ Okudum", key=f"f_{k['id']}"): add_to_library(k['id'], k['title'], k['author'], "Okudum", k['img'])

with tab2:
    df = get_books()
    if not df.empty:
        st.dataframe(df[['title', 'author', 'durum']], use_container_width=True)
    else:
        st.info("Henüz kitap eklemediniz.")
