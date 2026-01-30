import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

st.set_page_config(page_title="Kitap Yolculuğum", page_icon="📖", layout="wide")

st.markdown("""
    <style>
    .book-container { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 25px; }
    .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# --- YENİ VE GARANTİ ARAMA MOTORU (Open Library) ---
def search_books(query):
    if not query: return []
    # Türkçe kitapları da kapsayan açık kütüphane araması
    url = f"https://openlibrary.org/search.json?q={query.replace(' ', '+')}&limit=8"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for doc in data.get('docs', []):
                # Kapak resmi ID'si varsa oluştur, yoksa boş bırak
                cover_id = doc.get('cover_i')
                results.append({
                    "id": doc.get('key'),
                    "title": doc.get('title', 'Bilinmeyen Kitap'),
                    "author": ", ".join(doc.get('author_name', ['Bilinmiyor'])),
                    "desc": f"First published in {doc.get('first_publish_year', 'N/A')}. Subject: {', '.join(doc.get('subject', ['Literature'])[:3])}",
                    "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/150x200?text=No+Cover"
                })
            return results
    except:
        return []
    return []

# --- ARAYÜZ (DEĞİŞMEDİ) ---
st.title("📚 Kitap Yolculuğum")
tab1, tab2 = st.tabs(["🔍 Search & Discover", "🏠 My Library"])

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
                        status = st.selectbox("Durum:", ["Will Read", "Reading", "Read"], key=f"s_{b['id']}")
                    with c2:
                        if st.button("Add to Library", key=f"b_{b['id']}"):
                            conn.table("kitaplar").insert([{"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}]).execute()
                            st.success(f"Eklendi: {b['title']}")
        else:
            st.info("Henüz sonuç bulunamadı. Lütfen aramayı biraz detaylandırın.")

with tab2:
    st.subheader("Okuma Listem")
    try:
        data = conn.table("kitaplar").select("*").execute()
        if data.data:
            for item in data.data:
                color = "#3498db" if item['durum'] == "Will Read" else "#f1c40f" if item['durum'] == "Reading" else "#2ecc71"
                st.markdown(f'<div style="padding:10px; border-bottom:1px solid #eee;"><b>{item["kitap_adi"]}</b> - {item["yazar"]} <span class="status-badge" style="background-color:{color}; float:right;">{item["durum"]}</span></div>', unsafe_allow_html=True)
        else:
            st.info("Kütüphanen henüz boş.")
    except:
        st.error("Veritabanı tablosu 'kitaplar' bulunamadı.")
