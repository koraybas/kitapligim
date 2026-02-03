import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="KORAY BASARAN KÜTÜPHANE", page_icon="📖", layout="wide")

# 2. Modern Dashboard Tasarımı (v3 Tasarımı Geri Geldi)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f4f7fa; }
    .header-container {
        background: #1a202c; padding: 30px; border-radius: 20px; color: white;
        margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        display: flex; justify-content: space-between; align-items: center;
    }
    .header-title h1 { color: white; margin: 0; font-size: 2rem; font-weight: 700; }
    .stat-card {
        background: white; border-radius: 18px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #edf2f7; margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 12px; background: #3182ce; color: white; border: none;
        font-weight: 600; padding: 10px 24px; transition: all 0.3s;
    }
    .stButton>button:hover {
        background: #2b6cb0; transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(49, 130, 206, 0.3);
    }
    .summary-text {
        font-size: 0.95em; color: #444; background: #fff9f9; padding: 15px;
        border-radius: 10px; border-left: 5px solid #b21f1f; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Sistemi
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-container"><div class="header-title"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div></div>', unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1, 1, 1])
    with col2:
        with st.form("Login"):
            pwd = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Erişim Reddedildi.")
else:
    # Veritabanı bağlantısı
    conn = st.connection("supabase", type=SupabaseConnection)

    # Dashboard Header
    st.markdown(f'''
        <div class="header-container">
            <div class="header-title">
                <h1>📚 KORAY BASARAN KÜTÜPHANE</h1>
                <div style="opacity:0.7; font-size:0.9rem;">{pd.Timestamp.now().strftime('%d %B %Y | %H:%M')}</div>
            </div>
            <div style="font-weight: 600; background: #2d3748; padding: 10px 20px; border-radius: 12px; color: #cbd5e0; font-size: 0.8rem;">
                DASHBOARD PRO MAX
            </div>
        </div>
    ''', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Kütüphanem", "📊 Analiz"])

    # --- TAB 1: OPEN LIBRARY KEŞFET (Genişletilmiş) ---
    with tab1:
        st.markdown("<div class='stat-card'><h3>🔍 Kütüphane Taraması</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap veya yazar adı yazın...", key="search_k")
        if q:
            with st.spinner('Open Library taranıyor...'):
                try:
                    # Daha fazla sonuç (limit=15) ve her şeyi tara modu
                    res = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=15").json()
                    for doc in res.get('docs', []):
                        col1, col2, col3 = st.columns([1, 3, 1.5])
                        cover_id = doc.get('cover_i')
                        img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/100x150?text=Yok"
                        
                        with col1:
                            st.image(img, width=100)
                        with col2:
                            st.markdown(f"#### {doc.get('title')}")
                            author = doc.get('author_name', ['Bilinmiyor'])[0]
                            st.write(f"✍️ **Yazar:** {author}")
                            if st.button("📖 Özeti Gör", key=f"sum_{doc.get('key')}"):
                                det = requests.get(f"https://openlibrary.org{doc.get('key')}.json").json()
                                desc = det.get('description')
                                desc_text = desc.get('value') if isinstance(desc, dict) else desc
                                if desc_text:
                                    st.markdown(f"<div class='summary-text'>{desc_text[:800]}...</div>", unsafe_allow_html=True)
                                else:
                                    st.info("Bu kitap için özet bulunamadı.")
                        with col3:
                            st.write("##")
                            status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                            if st.button("➕ Ekle", key=f"add_{doc.get('key')}", use_container_width=True):
                                conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                                st.toast("Koleksiyona eklendi!", icon="✅")
                        st.divider()
                except: st.error("Bağlantı sorunu oluştu.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KÜTÜPHANEM (Güncelleme Özellikli) ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='stat-card'><h3>🏠 Koleksiyonunuz ({len(my_books)} Kitap)</h3>", unsafe_allow_html=True)
                for b in my_books:
                    ci, cs, cd = st.columns([3, 1.5, 0.5])
                    ci.markdown(f"**{b['kitap_adi']}**<br><small>{b['yazar']}</small>", unsafe_allow_html=True)
                    
                    opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                    new_s = cs.selectbox("Durum", opts, index=opts.index(b['durum']), key=f"up_{b['id']}", label_visibility="collapsed")
                    if new_s != b['durum']:
                        conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                        st.rerun()
                    
                    if cd.button("🗑️", key=f"del_{b['id']}"):
                        conn.table("kitaplar").delete().eq("id", b['id']).execute()
                        st.rerun()
                    st.markdown("<hr style='margin:10px 0; border:0.1px solid #edf2f7;'>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Henüz kitap eklemediniz.")
        except: pass

    # --- TAB 3: ANALİZ (Donut Grafik) ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns([1.5, 1])
            with col_l:
                st.markdown("<div class='stat-card'><h3>📊 Okuma Dağılımı</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.65, marker=dict(colors=['#1a202c', '#48bb78', '#ecc94b']))])
                fig.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_r:
                st.markdown("<div class='stat-card'><h3>✍️ Favori Yazarlar</h3>", unsafe_allow_html=True)
                top_authors = df['yazar'].value_counts().head(5)
                for author, count in top_authors.items():
                    st.write(f"👤 **{author}**: {count} Kitap")
                st.markdown("</div>", unsafe_allow_html=True)
