import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Ayarları
st.set_page_config(page_title="KORAY BASARAN KÜTÜPHANE", page_icon="📚", layout="wide")

# 2. Modern Tasarım CSS
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-header {
        background: linear-gradient(90deg, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;
    }
    .dashboard-card {
        background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .author-item { display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f0f0f0; }
    .author-img { width: 55px; height: 80px; object-fit: cover; border-radius: 8px; margin-right: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Sistemi (Session State Hatasını Önlemek İçin)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.form("login_form"):
            pwd = st.text_input("Giriş Şifresi", type="password")
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı Şifre!")
else:
    # --- Veritabanı Bağlantısı ---
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
    except Exception as e:
        st.error(f"Bağlantı Kurulamadı! Lütfen Secrets (API Key) ayarlarını kontrol et. Hata: {e}")
        st.stop()

    st.markdown('<div class="main-header"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Koleksiyonum", "📊 Analiz"])

    # --- TAB 1: KEŞFET ---
    with tab1:
        st.markdown("<div class='dashboard-card'><h3>🔍 Yeni Kitaplar</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap ara...", key="search_k")
        if q:
            try:
                res = requests.get(f"https://openlibrary.org/search.json?q={q}&limit=8", timeout=10).json()
                for doc in res.get('docs', []):
                    col1, col2, col3 = st.columns([1, 3, 1.5])
                    cover_id = doc.get('cover_i')
                    img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x120"
                    with col1: st.image(img, width=90)
                    with col2:
                        st.markdown(f"#### {doc.get('title')}")
                        author = doc.get('author_name', ['Bilinmiyor'])[0]
                        st.write(f"✍️ {author}")
                        if st.button("📖 Özeti Gör", key=f"sum_{doc.get('key')}"):
                            details = requests.get(f"https://openlibrary.org{doc.get('key')}.json").json()
                            desc = details.get('description', 'Özet yok.')
                            st.info(desc.get('value') if isinstance(desc, dict) else desc)
                    with col3:
                        status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                        if st.button("➕ Ekle", key=f"add_{doc.get('key')}", type="primary", use_container_width=True):
                            conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                            st.toast("Kütüphaneye eklendi!")
                    st.divider()
            except: st.error("Arama servisinde bir sorun var.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='dashboard-card'><h3>🏠 Koleksiyonunuz ({len(my_books)})</h3>", unsafe_allow_html=True)
                for b in my_books:
                    c_inf, c_status, c_del = st.columns([3, 2, 0.5])
                    with c_inf:
                        st.markdown(f"**{b['kitap_adi']}** - {b['yazar']}")
                    with c_status:
                        opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                        idx = opts.index(b['durum']) if b['durum'] in opts else 0
                        new_s = st.selectbox("Güncelle", opts, index=idx, key=f"up_{b['id']}", label_visibility="collapsed")
                        if new_s != b['durum']:
                            conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                            st.toast("Güncellendi!")
                    with c_del:
                        if st.button("🗑️", key=f"del_{b['id']}"):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Koleksiyon boş.")
        except: st.warning("Veriler şu an yüklenemiyor.")

    # --- TAB 3: ANALİZ ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns([1.5, 1])
            with col_l:
                st.markdown("<div class='dashboard-card'><h3>📊 Dağılım</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.6)])
                fig.update_layout(height=350, margin=dict(l=20,r=20,b=20,t=20))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_r:
                st.markdown("<div class='dashboard-card'><h3>✍️ Yazarlar</h3>", unsafe_allow_html=True)
                top_authors = df['yazar'].value_counts().head(5)
                for auth, count in top_authors.items():
                    st.write(f"👤 **{auth}**: {count} Kitap")
                st.markdown("</div>", unsafe_allow_html=True)
