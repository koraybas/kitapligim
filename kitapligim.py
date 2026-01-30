import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="Library Pro", page_icon="📑", layout="wide")

# 2. Modern & Kompakt CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .hero-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    .stButton>button { border-radius: 10px; font-weight: 600; }
    /* Grafik alanlarını sınırlamak için */
    [data-testid="stMetricValue"] { font-size: 24px !important; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Kontrolü
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login"):
            pwd = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Hatalı!")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Bul", "🏠 Koleksiyon", "📊 Analiz"])

    # --- TAB 1: KİTAP BUL ---
    with tab1:
        q = st.text_input("", placeholder="Arayın...", key="search")
        if q:
            data = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=6").json()
            for doc in data.get('docs', []):
                with st.container():
                    c1, c2 = st.columns([1, 4])
                    with c1: 
                        cover_id = doc.get('cover_i')
                        st.image(f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x120", width=80)
                    with c2:
                        st.write(f"**{doc.get('title')}**")
                        st.caption(doc.get('author_name', ['-'])[0])
                        ca, cb = st.columns([2, 1])
                        status = ca.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}", label_visibility="collapsed")
                        if cb.button("Ekle", key=f"a_{doc.get('key')}", use_container_width=True):
                            conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name')[0], "durum": status}]).execute()
                            st.toast("Eklendi!")
                st.divider()

    # --- TAB 2: KOLEKSİYON ---
    with tab2:
        res = conn.table("kitaplar").select("*").execute()
        my_books = res.data
        if my_books:
            # Kompakt Metrikler
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam", len(my_books))
            c2.metric("Okunan", len([b for b in my_books if b['durum'] == "Okudum"]))
            c3.metric("Devam", len([b for b in my_books if b['durum'] == "Okuyorum"]))
            
            st.write("---")
            for b in my_books:
                with st.container():
                    col_info, col_del = st.columns([5, 1.2])
                    bg = "#E3F2FD" if b['durum'] == "Okuyacağım" else "#FFFDE7" if b['durum'] == "Okuyorum" else "#E8F5E9"
                    tx = "#1565C0" if b['durum'] == "Okuyacağım" else "#F57F17" if b['durum'] == "Okuyorum" else "#2E7D32"
                    col_info.markdown(f"""
                        <div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee;">
                        <small>{b['yazar']}</small><br><b>{b['kitap_adi']}</b><br>
                        <span class="badge" style="background:{bg}; color:{tx};">{b['durum']}</span>
                        </div>""", unsafe_allow_html=True)
                    if col_del.button("🗑️", key=f"d_{b['id']}", use_container_width=True):
                        conn.table("kitaplar").delete().eq("id", b['id']).execute()
                        st.rerun()
        else: st.info("Boş.")

    # --- TAB 3: ANALİZ (KÜÇÜLTÜLMÜŞ & YAN YANA) ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            # Analizleri yan yana 3 sütuna böldük (Daha küçük görünmesi için)
            a1, a2, a3 = st.columns([1.5, 1, 1])
            
            with a1:
                st.caption("📈 Okuma Dağılımı")
                # Grafik boyutunu küçültmek için height ekledik
                st.bar_chart(df['durum'].value_counts(), height=180)
            
            with a2:
                st.caption("✍️ Top 5 Yazar")
                authors = df['yazar'].value_counts().head(5)
                st.write(authors)
            
            with a3:
                st.caption("🏆 Başarı")
                total = len(my_books)
                done = len([b for b in my_books if b['durum'] == "Okudum"])
                perc = int((done/total)*100) if total > 0 else 0
                st.metric("Tamamlama", f"%{perc}")
                st.progress(perc / 100)
        else: st.info("Veri yok.")
