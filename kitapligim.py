import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# Sayfa Ayarları
st.set_page_config(page_title="Kişisel Kitaplığım", page_icon="📚", layout="wide")

# CSS ile Şık Tasarım
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    .book-card { border: 1px solid #ddd; padding: 15px; border-radius: 10px; background: white; margin-bottom: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 1. BAĞLANTI: Supabase
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error(f"Veritabanı bağlantı hatası: {e}")

# 2. FONKSİYON: Google Books Arama
def master_search(q):
    results = []
    # Secrets içinden anahtarı çekiyoruz
    try:
        # Önce [api_keys] altında arar, yoksa direkt kök dizinde arar
        if "api_keys" in st.secrets:
            google_key = st.secrets["api_keys"].get("GOOGLE_BOOKS")
        else:
            google_key = st.secrets.get("GOOGLE_BOOKS")
            
        if not google_key:
            st.error("Hata: Google API Key (GOOGLE_BOOKS) Secrets içinde bulunamadı!")
            return []

        query = q.replace(' ', '+')
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&key={google_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                inf = item.get('volumeInfo', {})
                img_links = inf.get('imageLinks', {})
                # Resim varsa çek, yoksa boş bırak
                img_url = img_links.get('thumbnail', "").replace("http://", "https://")
                
                results.append({
                    "id": item.get('id'),
                    "title": inf.get('title', 'Bilinmeyen Kitap'),
                    "author": ", ".join(inf.get('authors', ['Bilinmeyen Yazar'])),
                    "img": img_url
                })
        elif response.status_code == 403:
            st.error("Google API Hatası (403): Anahtarınızın Books API izni kapalı veya kısıtlı.")
        else:
            st.error(f"Google API Hatası: {response.status_code}")
    except Exception as e:
        st.error(f"Arama sırasında hata oluştu: {e}")
    return results

# ARAYÜZ
st.title("📚 Kişisel Kitap Takip Sistemi")

tab1, tab2 = st.tabs(["🔍 Yeni Kitap Ekle", "📖 Kütüphanem"])

# TAB 1: ARAMA VE EKLEME
with tab1:
    search_query = st.text_input("Kitap Adı veya Yazar Ara:", placeholder="Örn: Nutuk veya Sabahattin Ali")
    
    if search_query:
        books = master_search(search_query)
        if books:
            cols = st.columns(3)
            for idx, book in enumerate(books):
                with cols[idx % 3]:
                    st.markdown(f'''
                        <div class="book-card">
                            <img src="{book['img']}" style="height:150px; margin-bottom:10px;"><br>
                            <b>{book['title']}</b><br>
                            <small>{book['author']}</small>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    if st.button(f"Kütüphaneye Ekle", key=f"btn_{book['id']}"):
                        try:
                            # Supabase'e ekleme işlemi
                            conn.table("kitaplar").insert([
                                {"kitap_id": book['id'], "kitap_adi": book['title'], "yazar": book['author'], "durum": "Okunacak"}
                            ]).execute()
                            st.success(f"'{book['title']}' başarıyla eklendi!")
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
        else:
            st.warning("Sonuç bulunamadı.")

# TAB 2: KÜTÜPHANEM LİSTESİ
with tab2:
    try:
        res = conn.table("kitaplar").select("*").execute()
        if res.data:
            st.table(res.data)
        else:
            st.info("Kütüphaneniz henüz boş.")
    except Exception as e:
        st.error(f"Liste yüklenirken hata oluştu: {e}")
