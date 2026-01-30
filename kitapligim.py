import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# 1. Sayfa Ayarları
st.set_page_config(page_title="Kitap Yolculuğum", page_icon="📚", layout="wide")

# 2. Şık Görünüm (CSS)
st.markdown("""
    <style>
    .book-card { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
    .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Veritabanı Bağlantısı
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Arama Motoru
def search_books(query):
    if not query: return []
    url = f"https://openlibrary.org/search.json?q={query.replace(' ', '+')}&limit=12"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for doc in data.get('docs', []):
                cover_id = doc.get('cover_i')
                # Sadece başlığı ve yazarı olanları al
                if 'title' in doc and 'author_name' in doc:
                    results.append({
                        "id": doc.get('key'),
                        "title": doc.get('title'),
                        "author": doc.get('author_name')[0],
                        "year": doc.get('first_publish_year', 'N/A'),
                        "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                    })
            return results
    except: return []
    return []

# 5. Arayüz Tasarımı
st.title("📚 Kitap Yolculuğum")
tab1, tab2 = st.tabs(["🔍 Kitap Keşfet", "🏠 Kitaplığım"])

with tab1:
    search_input = st.text_input("Kitap veya Yazar Ara...", placeholder="Örn: Nutuk, George Orwell...", key="main_search")
    
    if search_input:
        books = search_books(search_input)
        if books:
            for b in books:
                with st.container():
                    # Tasarımı 3 sütuna böldük: Kapak | Bilgiler | Ekleme Paneli
                    c1, c2, c3 = st.columns([1, 2.5, 1.5])
                    
                    with c1:
                        if b['cover']:
                            st.image(b['cover'], use_container_width=True)
                        else:
                            st.info("Kapak Yok")
                    
                    with c2:
                        st.subheader(b['title'])
                        st.write(f"**Yazar:** {b['author']}")
                        st.write(f"**İlk Yayın:** {b['year']}")
                    
                    with c3:
                        st.write("###") # Boşluk bırakmak için
                        status = st.selectbox("Okuma Durumu:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"sel_{b['id']}")
                        if st.button("➕ Listeme Ekle", key=f"btn_{b['id']}", type="primary", use_container_width=True):
                            try:
                                conn.table("kitaplar").insert([{"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}]).execute()
                                st.success("Eklendi!")
                                st.balloons()
                            except: st.error("Kayıt hatası!")
                st.divider()
        else:
            st.warning("Aradığınız kitap bulunamadı.")

with tab2:
    try:
        res = conn.table("kitaplar").select("*").execute()
        my_books = res.data
        
        # Sayaç Paneli
        if my_books:
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Toplam Kayıt", len(my_books))
            st.divider()
            
            for item in my_books:
                renk = "#3498db" if item['durum'] == "Okuyacağım" else "#f1c40f" if item['durum'] == "Okuyorum" else "#2ecc71"
                with st.container():
                    ci, cd = st.columns([4, 1])
                    with ci:
                        st.markdown(f"""
                        <div style="padding:10px; border-left: 5px solid {renk}; background-color: #fdfdfd; border-radius: 5px;">
                            <span style="font-size: 1.1em; font-weight: bold;">{item['kitap_adi']}</span> - {item['yazar']}
                            <br><span class="status-badge" style="background-color:{renk};">{item['durum']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with cd:
                        st.write("###")
                        if st.button("🗑️ Sil", key=f"del_{item['id']}", use_container_width=True):
                            conn.table("kitaplar").delete().eq("id", item['id']).execute()
                            st.rerun()
        else:
            st.info("Henüz kütüphanene kitap eklemedin.")
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
