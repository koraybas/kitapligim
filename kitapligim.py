import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# Sayfa Ayarları
st.set_page_config(page_title="BookPulse | Kitap İzleyici", page_icon="📚", layout="centered")

# Şık Tasarım Dokunuşları
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .book-card { 
        background: white; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 5px solid #2e7d32;
    }
    .stButton>button { border-radius: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Veritabanı Bağlantısı
conn = st.connection("supabase", type=SupabaseConnection)

# --- ARAMA MOTORU (API KEY GEREKTİRMEZ) ---
def search_books(query):
    # Google Books'un halka açık arama servisini kullanıyoruz (Key gerekmez)
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&langRestrict=tr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            books = []
            for item in data.get('items', []):
                vol = item.get('volumeInfo', {})
                books.append({
                    "id": item.get('id'),
                    "baslik": vol.get('title', 'İsimsiz Kitap'),
                    "yazar": ", ".join(vol.get('authors', ['Bilinmiyor'])),
                    "ozet": vol.get('description', 'Özet bulunmuyor.'),
                    "kapak": vol.get('imageLinks', {}).get('thumbnail', "").replace("http://", "https://")
                })
            return books
    except:
        return []

# --- ARAYÜZ ---
st.title("🚀 BookPulse")
st.caption("Türkiye'nin Dijital Kitap Kütüphanesi")

tab1, tab2 = st.tabs(["🔍 Kitap Keşfet", "📖 Benim Kütüphanem"])

# TAB 1: ARAMA VE SEÇİM
with tab1:
    s_query = st.text_input("", placeholder="Kitap adı veya yazar yazın...")
    
    if s_query:
        results = search_books(s_query)
        for b in results:
            with st.container():
                st.markdown(f"""
                <div class="book-card">
                    <img src="{b['kapak']}" style="float:left; width:80px; margin-right:15px; border-radius:5px;">
                    <h4>{b['baslik']}</h4>
                    <p><b>Yazar:</b> {b['yazar']}</p>
                    <p style='font-size:0.9em; color:#555;'>{b['ozet'][:300]}...</p>
                    <div style="clear:both;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Seçenekler ve Ekleme Butonu
                col1, col2 = st.columns([2, 1])
                with col1:
                    status = st.selectbox("Durum Seçin:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"sel_{b['id']}")
                with col2:
                    if st.button("Kütüphaneme Ekle", key=f"btn_{b['id']}"):
                        try:
                            conn.table("kitaplar").insert([
                                {"kitap_id": b['id'], "kitap_adi": b['baslik'], "yazar": b['yazar'], "durum": status}
                            ]).execute()
                            st.success("Listeye eklendi!")
                        except:
                            st.error("Veritabanı hatası! Tablonun hazır olduğundan emin olun.")

# TAB 2: KÜTÜPHANEM
with tab2:
    try:
        my_books = conn.table("kitaplar").select("*").execute()
        if my_books.data:
            for kb in my_books.data:
                col_a, col_b, col_c = st.columns([3, 2, 1])
                col_a.write(f"**{kb['kitap_adi']}**")
                col_b.write(f"_{kb['yazar']}_")
                
                # Duruma göre renkli etiket
                color = "orange" if kb['durum'] == "Okuyorum" else "green" if kb['durum'] == "Okudum" else "blue"
                col_c.markdown(f'<span style="color:{color}; font-weight:bold;">{kb["durum"]}</span>', unsafe_allow_html=True)
                st.divider()
        else:
            st.info("Kütüphanenizde henüz kitap yok.")
    except:
        st.warning("Henüz hiç kitap eklenmemiş.")
