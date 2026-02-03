import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Ayarları
st.set_page_config(page_title="KORAY BASARAN KÜTÜPHANE", page_icon="📚", layout="wide")

# 2. Modern Dashboard CSS
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-header {
        background: linear-gradient(90deg, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .dashboard-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .author-item {
        display: flex;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid #f0f0f0;
        transition: background 0.3s;
    }
    .author-item:hover { background-color: #f8f9fa; }
    .author-img {
        width: 55px;
        height: 80px;
        object-fit: cover;
        border-radius: 8px;
        margin-right: 18px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .badge {
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Sistemi
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
    # Veritabanı bağlantısı
    conn = st.connection("supabase", type=SupabaseConnection)
    
    st.markdown('<div class="main-header"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Koleksiyonum", "📊 Okuma Analizi"])

    # --- TAB 1: KİTAP KEŞFET ---
    with tab1:
        st.markdown("<div class='dashboard-card'><h3>🔍 Yeni Kitaplar Bul</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap veya yazar adı yazın...", key="search_k")
        if q:
            with st.spinner('Kütüphane taranıyor...'):
                try:
                    res = requests.get(f"https://openlibrary.org/search.json?q={q}&limit=10").json()
                    for doc in res.get('docs', []):
                        col1, col2, col3 = st.columns([1, 3, 1.5])
                        cover_id = doc.get('cover_i')
                        img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x120?text=Kapak+Yok"
                        
                        with col1:
                            st.image(img, width=90)
                        with col2:
                            st.markdown(f"#### {doc.get('title')}")
                            author = doc.get('author_name', ['Bilinmiyor'])[0]
                            st.write(f"✍️ **Yazar:** {author}")
                        with col3:
                            st.write("##")
                            status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                            if st.button("➕ Koleksiyona Ekle", key=f"add_{doc.get('key')}", use_container_width=True, type="primary"):
                                conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                                st.toast(f"'{doc.get('title')}' eklendi!", icon="✅")
                        st.divider()
                except: st.error("Bağlantı hatası oluştu.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='dashboard-card'><h3>🏠 Toplam {len(my_books)} Kitap</h3>", unsafe_allow_html=True)
                for b in my_books:
                    c_inf, c_d = st.columns([5, 1])
                    with c_inf:
                        st.markdown(f"**{b['kitap_adi']}** - <small>{b['yazar']}</small>  `{b['durum']}`", unsafe_allow_html=True)
                    with c_d:
                        if st.button("🗑️", key=f"del_{b['id']}", use_container_width=True):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Henüz kitap eklemediniz.")
        except: pass

    # --- TAB 3: ANALİZLER ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns([2, 1.2])

            with col_l:
                st.markdown("<div class='dashboard-card'><h3>📊 Okuma Dağılımı</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.6, 
                                            marker=dict(colors=['#1a2a6c', '#2ecc71', '#f1c40f']))])
                fig.update_layout(height=350, margin=dict(l=20,r=20,b=20,t=20))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_r:
                st.markdown("<div class='dashboard-card'><h3>✍️ En Çok Okunan Yazarlar</h3>", unsafe_allow_html=True)
                top_authors = df['yazar'].value_counts().head(5)
                
                for author, count in top_authors.items():
                    try:
                        # Yazara ait ilk kitabın kapak ID'sini bul
                        sample_book = df[df['yazar'] == author].iloc[0]['kitap_id']
                        clean_id = sample_book.split('/')[-1]
                        author_img = f"https://covers.openlibrary.org/b/olid/{clean_id}-M.jpg"
                    except:
                        author_img = "https://via.placeholder.com/55x80?text=Kitap"

                    st.markdown(f"""
                        <div class="author-item">
                            <img src="{author_img}" class="author-img" onerror="this.src='https://via.placeholder.com/55x80?text=Yok'">
                            <div>
                                <div style="font-weight:bold; color:#2c3e50;">{author}</div>
                                <div style="font-size:0.85em; color:#7f8c8d;">{count} Kitap</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Analizleri görmek için kitap eklemelisiniz.")
