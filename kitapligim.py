import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# Sayfa Ayarları
st.set_page_config(page_title="Kişisel Kitaplığım", page_icon="📚", layout="wide")

# CSS Tasarımı
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #4CAF50; color: white; font-weight: bold; }
    .book-card { border: 1px solid #eee; padding: 15px; border-radius: 12px; background: white; margin-bottom: 20px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    img { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Veritabanı Bağlantısı
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Veritabanına bağlanılamadı.")

# AKILLI ARAMA MOTORU (Google + Open Library Yedekli)
def smart_search(q):
    results = []
    # Önce Google API Key kontrolü
    google_key = st.secrets.get("GOOGLE_BOOKS") or st.secrets.get("api_keys", {}).get("GOOGLE_BOOKS")
    
    if google_key:
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q={q.replace(' ', '+')}&maxResults=10&key={google_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    inf = item.get('volumeInfo', {})
                    img = inf.get('imageLinks', {}).get('thumbnail', "").replace("http://", "https://")
                    results.append({"id": item.get('id'), "title": inf.get('title'), "author": ", ".join(inf.get('authors', ['Bilinmiyor'])), "img": img})
                if results: return results
        except:
            pass # Google hata verirse Open Library'ye geçecek

    # YEDEK MOTOR: Open Library (API Key İstemez)
    try:
        url = f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=10"
        response = requests.get(url, timeout=5).json()
        for doc in response.get('docs', []):
            img_id = doc.get('cover_i')
            results.append({
                "id": doc.get('key'),
                "title": doc.get('title'),
                "author": ", ".join(doc.get('author_name', ['Bilinmiyor'])),
                "img": f"https://covers.openlibrary.org/b/id/{img_id}-M.jpg" if img_id else ""
            })
    except Exception as e:
        st.error(f"Arama hatası: {e}")
    return results

# ARAYÜZ
st.title("📚 Kişisel Kitap Takip Sistemi")
tab1, tab2 = st.tabs(["🔍 Yeni Kitap Ekle", "📖 Kütüphanem"])

with tab1:
    search_query = st.text_input("Kitap veya Yazar Ara:", placeholder="Örn: Nutuk")
    if search_query:
        books = smart_search(search_query)
        cols = st.columns(3)
        for idx, book in enumerate(books):
            with cols[idx % 3]:
                st.markdown(f'<div class="book-card"><img src="{book["img"]}" height="180"><br><b>{book["title"]}</b><br><small>{book["author"]}</small></div>', unsafe_allow_html=True)
                if st.button("Listeye Ekle",
