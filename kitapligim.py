import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="Library Pro Max v4", page_icon="📚", layout="wide")

# 2. Modern Dashboard Tasarımı (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .header-container {
        background: #1e293b; padding: 25px; border-radius: 20px; color: white;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .stat-card {
        background: white; border-radius: 18px; padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 10px; background: #3b82f6; color: white; border: none; font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Sistemi
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-container"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        pwd = st.text_input("Şifre", type="password")
        if st.button("Giriş", use_container_width=True):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown('<div class="header-container"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet (Google & Open)", "🏠 Kütüphanem", "📊 İstatistik"])

    # --- TAB 1: GOOGLE BOOKS DESTEKLİ GENİŞ ARAMA ---
    with tab1:
        st.markdown("<div class='stat-card'><h3>🔍 Geniş Kitap Araması</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="D&R ve Amazon'da olan çoğu kitabı burada bulabilirsiniz...", key="search_q")
        
        if q:
            with st.spinner('Global kütüphaneler taranıyor...'):
                # GOOGLE BOOKS API SORGUSU (Türkçe içerik için çok daha iyi)
                try:
                    google_url = f"https://www.googleapis.com/books/v1/volumes?q={q.replace(' ', '+')}&maxResults=10&langRestrict=tr"
                    res = requests.get(google_url).json()
                    items = res.get('items', [])
                    
                    if items:
                        for item in items:
                            info = item.get('volumeInfo', {})
                            with st.container():
                                c1, c2, c3 = st.columns([1, 3, 1.5])
                                with c1:
                                    img = info.get('imageLinks', {}).get('thumbnail', "https://via.placeholder.com/100x150")
                                    st.image(img, width=100)
                                with c2:
                                    st.markdown(f"#### {info.get('title')}")
                                    author = info.get('authors', ['Bilinmiyor'])[0]
                                    st.write(f"✍️ **Yazar:** {author}")
                                    with st.expander("📖 Kitap Özetini Oku"):
                                        st.write(info.get('description', 'Özet bulunamadı.'))
                                with c3:
                                    st.write("##")
                                    status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{item.get('id')}")
                                    if st.button("➕ Koleksiyona Ekle", key=f"add_{item.get('id')}", use_container_width=True):
                                        conn.table("kitaplar").insert([{"kitap_id": item.get('id'), "kitap_adi": info.get('title'), "yazar": author, "durum": status}]).execute()
                                        st.toast("Koleksiyona eklendi!")
                            st.divider()
                    else:
                        st.warning("Google Books üzerinde de bulunamadı. Lütfen yazımı kontrol edin.")
                except:
                    st.error("Arama sırasında bir hata oluştu.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KÜTÜPHANEM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                for b in my_books:
                    ci, cs, cd = st.columns([3, 1.5, 0.5])
                    ci.markdown(f"**{b['kitap_adi']}**<br><small>{b['yazar']}</small>", unsafe_allow_html=True)
                    opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                    new_s = cs.selectbox("Güncelle", opts, index=opts.index(b['durum']), key=f"up_{b['id']}", label_visibility="collapsed")
                    if new_s != b['durum']:
                        conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                        st.rerun()
                    if cd.button("🗑️", key=f"del_{b['id']}"):
                        conn.table("kitaplar").delete().eq("id", b['id']).execute()
                        st.rerun()
                    st.markdown("<hr style='margin:10px 0; border:0.1px solid #eee;'>", unsafe_allow_html=True)
            else: st.info("Koleksiyon boş.")
        except: pass

    # --- TAB 3: ANALİZ ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            c_l, c_r = st.columns([1.5, 1])
            with c_l:
                cnt = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=cnt.index, values=cnt.values, hole=.5)])
                st.plotly_chart(fig, use_container_width=True)
            with c_r:
                top = df['yazar'].value_counts().head(5)
                for auth, count in top.items():
                    st.write(f"👤 **{auth}**: {count} Kitap")
