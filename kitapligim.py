import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# 1. Sayfa Ayarları
st.set_page_config(page_title="Kitap Yolculuğum", page_icon="📚", layout="wide")

# 2. Gelişmiş Görünüm (CSS)
st.markdown("""
    <style>
    .book-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.85em;
        color: white;
    }
    /* Butonları güzelleştirelim */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Veritabanı Bağlantısı
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Arama Fonksiyonu
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
                    "year": doc.get('first_publish_year', 'N/A'),
                    "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/150x200?text=Kapak+Yok"
                })
            return results
    except: return []
    return []

# 5. Arayüz
st.title("📚 Kitap Yolculuğum")

tab1, tab2 = st.tabs(["🔍 Kitap Keşfet", "🏠 Kitaplığım"])

with tab1:
    search_input = st.text_input("Kitap veya yazar adı giriniz...", placeholder="Örn: Nutuk, Sabahattin Ali...")
    
    if search_input:
        books = search_books(search_input)
        if books:
            for b in books:
                # Her kitap için bir kart oluşturalım
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1.2]) # Oranları butonlar için ayarladık
                    
                    with col1:
                        st.image(b['cover'], use_container_width=True)
                    
                    with col2:
                        st.subheader(b['title'])
                        st.write(f"**Yazar:** {b['author']}")
                        st.write(f"**İlk Yayın:** {b['year']}")
                    
                    with col3:
                        st.write("---") # Görsel ayraç
                        status = st.selectbox("Durum Seçin:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"sel_{b['id']}")
                        if st.button("➕ Kitaplığa Ekle", key=f"add_{b['id']}", type="primary"):
                            try:
                                conn.table("kitaplar").insert([
                                    {"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}
                                ]).execute()
                                st.success("Eklendi!")
                                st.balloons()
                            except:
                                st.error("Bir hata oluştu.")
                st.markdown("---") # Kitaplar arası çizgi
        else:
            st.info("Sonuç bulunamadı.")

with tab2:
    # Sayaç ekleyelim
    try:
        data = conn.table("kitaplar").select("*").execute()
        kitap_listesi = data.data
        
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("Toplam Kitap", len(kitap_listesi))
        
        if kitap_listesi:
            st.write("---")
            for item in kitap_listesi:
                renk = "#3498db" if item['durum'] == "Okuyacağım" else "#f1c40f" if item['durum'] == "Okuyorum" else "#2ecc71"
                
                with st.container():
                    c_info, c_del = st.columns([4, 1])
                    with c_info:
                        st.markdown(f"""
                        <div style="padding:10px; border-left: 5px solid {renk}; background-color: #ffffff; margin-bottom: 5px;">
                            <span style="font-size: 1.1em; font-weight: bold;">{item['kitap_adi']}</span> - {item['yazar']}
                            <br><span class="status-badge" style="background-color:{renk};">{item['durum']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️ Sil", key=f"del_{item['id']}"):
                            conn.table("kitaplar").delete().eq("id", item['id']).execute()
                            st.rerun()
        else:
            st.info("Kütüphaneniz henüz boş.")
    except Exception as e:
        st.error(f"Liste yüklenemedi: {e}")
