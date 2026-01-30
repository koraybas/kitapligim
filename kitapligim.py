import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Ayarları & Tema
st.set_page_config(page_title="Kitap Yolculuğum Dashboard", page_icon="📖", layout="wide")

# 2. Gelişmiş Modern Arayüz Tasarımı (Görseldeki Stilde)
st.markdown("""
    <style>
    /* Arka Plan */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* Üst Başlık Paneli */
    .main-header {
        background: linear-gradient(90deg, #4b79a1 0%, #283e51 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Kart Tasarımları */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .book-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .book-card:hover {
        transform: translateY(-3px);
    }

    /* Durum Etiketleri */
    .status-pill {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Şifre Kontrolü
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True

    st.markdown('<div class="main-header"><h1>📖 Kitap Yolculuğum</h1><p>Lütfen devam etmek için giriş yapın</p></div>', unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            password = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                if password == "1234":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("Hatalı şifre!")
    return False

if check_password():
    conn = st.connection("supabase", type=SupabaseConnection)

    # Üst Başlık
    st.markdown('<div class="main-header"><h1>📖 Kitap Yolculuğum</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Keşfet", "🏠 Kütüphanem", "📊 Analiz"])

    # --- TAB 1: KİTAP KEŞFET ---
    with tab1:
        search_q = st.text_input("Aramak istediğiniz kitap...", placeholder="🔍 Kitap, yazar veya konu...")
        if search_q:
            url = f"https://openlibrary.org/search.json?q={search_q.replace(' ', '+')}&limit=6"
            try:
                data = requests.get(url).json()
                for doc in data.get('docs', []):
                    cover_id = doc.get('cover_i')
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/100x150"
                    
                    with st.container():
                        col_img, col_txt, col_btn = st.columns([1, 3, 1.5])
                        with col_img:
                            st.image(cover_url, width=100)
                        with col_txt:
                            st.subheader(doc.get('title'))
                            st.write(f"**Yazar:** {doc.get('author_name', ['Bilinmiyor'])[0]}")
                        with col_btn:
                            st.write("###")
                            status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                            if st.button("➕ Ekle", key=f"b_{doc.get('key')}", type="primary", use_container_width=True):
                                conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name')[0], "durum": status}]).execute()
                                st.toast(f"{doc.get('title')} eklendi!", icon="✅")
                    st.divider()
            except: st.error("Arama sırasında bir hata oluştu.")

    # --- TAB 2: KÜTÜPHANEM (MODERN LİSTE) ---
    with tab2:
        try:
            res = conn.table("kitaplar").select("*").execute()
            my_books = res.data
            
            if my_books:
                # Üst Metrikler (Görseldeki gibi)
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam Kitap", len(my_books))
                m2.metric("Okunan", len([b for b in my_books if b['durum'] == "Okudum"]))
                m3.metric("Hedef", "50") # Manuel hedef

                st.write("---")
                search_lib = st.text_input("Kendi kitaplarımda ara...", placeholder="Kitap veya yazar adı...")
                
                for b in my_books:
                    if search_lib.lower() in b['kitap_adi'].lower() or search_lib.lower() in b['yazar'].lower():
                        renk = "#3498db" if b['durum'] == "Okuyacağım" else "#f1c40f" if b['durum'] == "Okuyorum" else "#2ecc71"
                        
                        with st.container():
                            c_info, c_action = st.columns([4, 1])
                            with c_info:
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; background: white; padding: 15px; border-radius: 12px; border-left: 8px solid {renk};">
                                    <div style="flex-grow: 1;">
                                        <div style="font-weight: bold; font-size: 1.1em;">{b['kitap_adi']}</div>
                                        <div style="color: #666;">{b['yazar']}</div>
                                        <span class="status-pill" style="background-color: {renk};">{b['durum']}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c_action:
                                st.write("###")
                                if st.button("🗑️ Sil", key=f"d_{b['id']}", use_container_width=True):
                                    conn.table("kitaplar").delete().eq("id", b['id']).execute()
                                    st.rerun()
            else: st.info("Kütüphane boş.")
        except: st.error("Veri yüklenemedi.")

    # --- TAB 3: ANALİZ (GÖRSELDEKİ GRAFİKLER) ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            c_left, c_right = st.columns(2)
            
            with c_left:
                st.markdown("### 📈 Okuma Durumu")
                status_counts = df['durum'].value_counts()
                st.bar_chart(status_counts, color="#4b79a1")
            
            with c_right:
                st.markdown("### ✍️ Favori Yazarlar")
                author_counts = df['yazar'].value_counts().head(5)
                st.write(author_counts)
        else: st.info("Analiz için veri ekleyin.")
