import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# 1. Sayfa Ayarları
st.set_page_config(page_title="Kitap Yolculuğum", page_icon="📚", layout="wide")

# 2. Şık Görünüm (CSS)
st.markdown("""
    <style>
    .book-container { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 25px; }
    .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; }
    .stButton>button { border-radius: 10px; font-weight: bold; }
    .delete-btn { color: #ff4b4b; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

# 3. Veritabanı Bağlantısı
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Arama Motoru (Open Library)
def search_books(query):
    if not query: return []
    url = f"https://openlibrary.org/search.json?q={query.replace(' ', '+')}&limit=8"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for doc in data.get('docs', []):
                cover_id = doc.get('cover_i')
                results.append({
                    "id": doc.get('key'),
                    "title": doc.get('title', 'Bilinmeyen Kitap'),
                    "author": ", ".join(doc.get('author_name', ['Bilinmiyor'])),
                    "desc": f"İlk yayın: {doc.get('first_publish_year', 'N/A')}",
                    "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/150x200?text=Kapak+Yok"
                })
            return results
    except: return []
    return []

# 5. Ana Arayüz
st.title("📚 Kitap Yolculuğum")
tab1, tab2 = st.tabs(["🔍 Kitap Keşfet", "🏠 Kitaplığım"])

# --- TAB 1: KİTAP KEŞFET VE EKLE ---
with tab1:
    search_input = st.text_input("Kitap veya Yazar Ara...", key="search_box")
    if search_input:
        books = search_books(search_input)
        if books:
            for b in books:
                with st.container():
                    st.markdown(f"""
                    <div class="book-container">
                        <img src="{b['cover']}" style="float:left; width:100px; margin-right:20px; border-radius:8px;">
                        <h3>{b['title']}</h3>
                        <p><b>Yazar:</b> {b['author']}</p>
                        <p style="color:#666; font-size:0.9em;">{b['desc']}</p>
                        <div style="clear:both;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([2,1])
                    with c1:
                        status = st.selectbox("Durum:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{b['id']}")
                    with c2:
                        if st.button("Kütüphaneme Ekle", key=f"b_{b['id']}"):
                            try:
                                conn.table("kitaplar").insert([{"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}]).execute()
                                st.success(f"Eklendi!")
                                st.balloons()
                            except: st.error("Ekleme başarısız.")

# --- TAB 2: KİTAPLIĞIM VE SİLME ---
with tab2:
    st.subheader("Okuma Serüvenim")
    try:
        data = conn.table("kitaplar").select("*").execute()
        if data.data:
            for item in data.data:
                renk = "#3498db" if item['durum'] == "Okuyacağım" else "#f1c40f" if item['durum'] == "Okuyorum" else "#2ecc71"
                
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="padding:10px; border-bottom:1px solid #eee;">
                        <b>{item['kitap_adi']}</b> - {item['yazar']} 
                        <span class="status-badge" style="background-color:{renk};">{item['durum']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    # SİLME BUTONU
                    if st.button("🗑️ Sil", key=f"del_{item['id']}"):
                        conn.table("kitaplar").delete().eq("id", item['id']).execute()
                        st.warning("Kitap silindi.")
                        st.rerun() # Sayfayı yenileyip listeyi günceller
        else:
            st.info("Kütüphaneniz boş.")
    except Exception as e:
        st.error(f"Liste hatası: {e}")
