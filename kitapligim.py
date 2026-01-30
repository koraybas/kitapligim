import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="Library Pro", page_icon="📑", layout="wide")

# 2. Ultra Modern CSS (Apple/SaaS Style)
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Üst Navigasyon ve Başlık Paneli */
    .hero-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }

    /* Kartlar (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }

    /* Metrik Kutuları */
    [data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    /* Modern Butonlar */
    .stButton>button {
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
        background: #4A90E2;
        color: white;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(74,144,226,0.3);
    }

    /* Durum Hapları */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 5px;
    }
    
    /* Sekme Stilini Sadeleştirme */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px;
        padding: 10px 20px;
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Güvenli Giriş Paneli
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if st.session_state.logged_in: return True

    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1><p>Kişisel kitap yolculuğunuza hoş geldiniz.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        with st.form("Login"):
            pwd = st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Giriş"):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Erişim Reddedildi.")
    return False

if login():
    conn = st.connection("supabase", type=SupabaseConnection)

    # Üst Bölüm
    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Keşfet", "🏠 Kütüphanem", "📊 İstatistikler"])

    # --- KEŞFET (MODERN KARTLAR) ---
    with tab1:
        q = st.text_input("", placeholder="Aramak istediğiniz kitabın adını yazın...", key="search")
        if q:
            data = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=6").json()
            for doc in data.get('docs', []):
                cover_id = doc.get('cover_i')
                img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/150"
                
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.image(img, width=120)
                    with col2:
                        st.markdown(f"### {doc.get('title')}")
                        st.caption(f"Yazar: {doc.get('author_name', ['Bilinmiyor'])[0]} | Yıl: {doc.get('first_publish_year', 'N/A')}")
                        
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            status = st.selectbox("Eylem:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                        with c2:
                            st.write("##")
                            if st.button("Kütüphaneye Ekle", key=f"add_{doc.get('key')}", use_container_width=True):
                                conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name')[0], "durum": status}]).execute()
                                st.toast("Koleksiyona eklendi!", icon="✨")
                st.divider()

    # --- KÜTÜPHANEM (GLASSMORPHISM LİSTE) ---
    with tab2:
        res = conn.table("kitaplar").select("*").execute()
        my_books = res.data
        if my_books:
            # Özet Bilgi Alanı
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam", len(my_books))
            c2.metric("Tamamlanan", len([b for b in my_books if b['durum'] == "Okudum"]))
            c3.metric("Devam Eden", len([b for b in my_books if b['durum'] == "Okuyorum"]))
            
            st.write("---")
            search_own = st.text_input("Koleksiyonumda ara...", placeholder="Kitap veya yazar adı...")
            
            for b in my_books:
                if search_own.lower() in b['kitap_adi'].lower() or search_own.lower() in b['yazar'].lower():
                    bg_color = "#E3F2FD" if b['durum'] == "Okuyacağım" else "#FFFDE7" if b['durum'] == "Okuyorum" else "#E8F5E9"
                    text_color = "#1565C0" if b['durum'] == "Okuyacağım" else "#F57F17" if b['durum'] == "Okuyorum" else "#2E7D32"
                    
                    st.markdown(f"""
                    <div style="background: white; border-radius: 15px; padding: 15px; margin-bottom: 10px; border: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; font-size: 16px;">{b['kitap_adi']}</div>
                            <div style="color: #888; font-size: 14px;">{b['yazar']}</div>
                            <span class="badge" style="background: {bg_color}; color: {text_color};">{b['durum']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ Koleksiyondan Çıkar", key=f"del_{b['id']}"):
                        conn.table("kitaplar").delete().eq("id", b['id']).execute()
                        st.rerun()
        else:
            st.info("Koleksiyonun henüz boş.")

    # --- İSTATİSTİKLER ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns(2)
            with col_l:
                st.write("**Okuma Alışkanlığı**")
                st.bar_chart(df['durum'].value_counts())
            with col_r:
                st.write("**En Çok Tercih Edilen Yazarlar**")
                st.dataframe(df['yazar'].value_counts(), use_container_width=True)
