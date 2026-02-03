import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="Library Pro Max", page_icon="📚", layout="wide")

# 2. Ultra Modern Custom CSS
st.markdown("""
    <style>
    /* Ana Arka Plan ve Yazı Tipi */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #eef2f3 0%, #8e9eab 100%);
    }

    /* Başlık Bandı */
    .main-header {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 25px;
        border-radius: 25px;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
    }

    /* Modern Kart Tasarımı */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Butonlar */
    .stButton>button {
        border-radius: 12px;
        border: none;
        background: linear-gradient(90deg, #4b79a1 0%, #283e51 100%);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* Durum Etiketleri */
    .badge {
        padding: 5px 12px;
        border-radius: 10px;
        font-size: 0.75em;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255,255,255,0.3);
        padding: 5px;
        border-radius: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px;
        padding: 8px 20px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Kontrolü
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>✨ Library Pro Max</h1><p>Giriş Yaparak Koleksiyonunuza Erişin</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("Login"):
            pwd = st.text_input("Sistem Şifresi", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Erişim Reddedildi")
else:
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
    except:
        st.error("Veritabanı bağlantısı kurulamadı.")
        st.stop()

    # Dashboard Başlığı
    st.markdown(f'''
        <div class="main-header">
            <h1>📑 KORAY BASARAN KÜTÜPHANE</h1>
            <p style="opacity:0.7; font-size:0.9em;">{pd.Timestamp.now().strftime('%d %B %Y | %H:%M')}</p>
        </div>
    ''', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Keşfet", "🏠 Kütüphanem", "📈 Analitik"])

    # --- TAB 1: MODERNIZE KEŞFET ---
    with tab1:
        st.markdown("<div class='glass-card'><h3>🔍 Akıllı Arama</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Aramak istediğiniz kitap veya yazarı yazın...", key="search_bar")
        if q:
            with st.spinner('Kütüphaneler taranıyor...'):
                try:
                    res = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=12").json()
                    for doc in res.get('docs', []):
                        with st.container():
                            col_img, col_txt, col_btn = st.columns([1, 3, 1.5])
                            with col_img:
                                cid = doc.get('cover_i')
                                st.image(f"https://covers.openlibrary.org/b/id/{cid}-M.jpg" if cid else "https://via.placeholder.com/100x150", width=100)
                            with col_txt:
                                st.subheader(doc.get('title'))
                                author = doc.get('author_name', ['Bilinmiyor'])[0]
                                st.write(f"✍️ **{author}**")
                                if st.button("📋 Özeti Gör", key=f"sum_{doc.get('key')}"):
                                    det = requests.get(f"https://openlibrary.org{doc.get('key')}.json").json()
                                    desc = det.get('description', 'Özet bilgisi eklenmemiş.')
                                    st.info(desc.get('value') if isinstance(desc, dict) else desc)
                            with col_btn:
                                st.write("##")
                                status = st.selectbox("Eylem", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                                if st.button("➕ Koleksiyona Ekle", key=f"add_{doc.get('key')}", use_container_width=True):
                                    conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                                    st.toast("Eklendi!", icon="✨")
                        st.divider()
                except: st.error("Arama servisi şu an meşgul.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: MODERNIZE KÜTÜPHANEM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='glass-card'><h3>🏠 Koleksiyon Durumu ({len(my_books)} Kitap)</h3>", unsafe_allow_html=True)
                for b in my_books:
                    with st.container():
                        c_info, c_upd, c_del = st.columns([3, 2, 0.5])
                        c_info.markdown(f"**{b['kitap_adi']}**<br><small>{b['yazar']}</small>", unsafe_allow_html=True)
                        
                        opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                        new_s = c_upd.selectbox("Durum", opts, index=opts.index(b['durum']), key=f"up_{b['id']}", label_visibility="collapsed")
                        if new_s != b['durum']:
                            conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                            st.rerun()
                            
                        if c_del.button("🗑️", key=f"del_{b['id']}"):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
                        st.markdown("<hr style='margin:5px 0; border:0.1px solid rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Koleksiyonunuz boş.")
        except: pass

    # --- TAB 3: PROFESYONEL ANALİTİK ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns([1.5, 1])
            
            with col_l:
                st.markdown("<div class='glass-card'><h3>📊 Okuma Analitiği</h3>", unsafe_allow_html=True)
                cnt = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=cnt.index, values=cnt.values, hole=.5, marker=dict(colors=['#2c3e50', '#2ecc71', '#f1c40f']))])
                fig.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_r:
                st.markdown("<div class='glass-card'><h3>🏆 En Çok Okunanlar</h3>", unsafe_allow_html=True)
                top_auth = df['yazar'].value_counts().head(5)
                for auth, count in top_auth.items():
                    st.markdown(f"""
                        <div style="padding:10px; border-radius:10px; background:white; margin-bottom:10px; border:1px solid #eee;">
                            <span style="font-weight:bold;">{auth}</span>
                            <span style="float:right; color:#2c3e50;">{count} Kitap</span>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("Analiz için kitap ekleyin.")
