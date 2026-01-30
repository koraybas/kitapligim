import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Ayarları (Responsive & Modern)
st.set_page_config(page_title="Library Pro", page_icon="📑", layout="wide")

# 2. Modern CSS (Glassmorphism & Mobil Uyumlu)
st.markdown("""
    <style>
    /* Arka Plan */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Ana Başlık Paneli */
    .hero-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        padding: 30px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
    }

    /* Kartlar */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 18px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 15px;
    }

    /* Butonlar */
    .stButton>button {
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 600;
        height: 3em;
    }
    
    /* Mobil İçin Durum Etiketleri */
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
        margin-top: 8px;
    }

    /* Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 12px;
        padding: 8px 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Şifre ve Oturum Kontrolü
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if st.session_state.logged_in: return True

    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1><p>Dijital kitaplığınıza giriş yapın.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("Login Form"):
            pwd = st.text_input("Giriş Şifresi", type="password")
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Hatalı Şifre!")
    return False

if login():
    # Veritabanı bağlantısı
    conn = st.connection("supabase", type=SupabaseConnection)

    # Başlık
    st.markdown('<div class="hero-section"><h1>✨ Library Pro</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Bul", "🏠 Koleksiyonum", "📊 Analizler"])

    # --- TAB 1: KİTAP BUL VE EKLE ---
    with tab1:
        q = st.text_input("", placeholder="Kitap, yazar veya konu ara...", key="search_bar")
        if q:
            with st.spinner('Kitaplar getiriliyor...'):
                try:
                    res_api = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=8", timeout=10).json()
                    for doc in res_api.get('docs', []):
                        cover_id = doc.get('cover_i')
                        img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/150x220?text=Kapak+Yok"
                        
                        with st.container():
                            col_img, col_txt = st.columns([1, 3])
                            with col_img:
                                st.image(img, use_container_width=True)
                            with col_txt:
                                st.subheader(doc.get('title'))
                                st.write(f"✍️ **Yazar:** {doc.get('author_name', ['Bilinmiyor'])[0]}")
                                st.write(f"📅 **Yıl:** {doc.get('first_publish_year', 'N/A')}")
                                
                                c_sel, c_add = st.columns([1, 1])
                                with c_sel:
                                    status = st.selectbox("Durum:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                                with c_add:
                                    st.write("##")
                                    if st.button("➕ Ekle", key=f"add_{doc.get('key')}", use_container_width=True, type="primary"):
                                        conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name')[0], "durum": status}]).execute()
                                        st.toast(f"{doc.get('title')} kütüphaneye eklendi!", icon="✨")
                                        st.balloons()
                        st.divider()
                except: st.error("Bir bağlantı sorunu oluştu.")

    # --- TAB 2: KOLEKSİYONUM (MOBİL OPTİMİZE) ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            
            if my_books:
                # Üst Özet Kartları
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam", len(my_books))
                m2.metric("Okunan", len([b for b in my_books if b['durum'] == "Okudum"]))
                m3.metric("Devam", len([b for b in my_books if b['durum'] == "Okuyorum"]))
                
                st.write("---")
                lib_q = st.text_input("Kütüphanende ara...", placeholder="Kitap veya yazar adı yazın...")
                
                for b in my_books:
                    if lib_q.lower() in b['kitap_adi'].lower() or lib_q.lower() in b['yazar'].lower():
                        # Renk paleti
                        bg_c = "#E3F2FD" if b['durum'] == "Okuyacağım" else "#FFFDE7" if b['durum'] == "Okuyorum" else "#E8F5E9"
                        tx_c = "#1565C0" if b['durum'] == "Okuyacağım" else "#F57F17" if b['durum'] == "Okuyorum" else "#2E7D32"
                        
                        st.markdown(f"""
                        <div style="background: white; border-radius: 18px; padding: 18px; margin-bottom: 12px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                            <div style="font-weight: 700; font-size: 1.1em; color: #333;">{b['kitap_adi']}</div>
                            <div style="color: #777; font-size: 0.9em; margin-top: 3px;">{b['yazar']}</div>
                            <span class="badge" style="background: {bg_c}; color: {tx_c};">{b['durum']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️ Sil", key=f"del_{b['id']}", use_container_width=True):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
            else:
                st.info("Kütüphaneniz henüz boş. Keşfet sekmesinden kitap ekleyin!")
        except Exception as e:
            st.error(f"Veri yüklenemedi: {e}")

    # --- TAB 3: İSTATİSTİKLER ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            st.markdown("### 📊 Okuma Alışkanlıklarınız")
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                st.write("**Durum Dağılımı**")
                st.bar_chart(df['durum'].value_counts())
            
            with col_table:
                st.write("**Yazar Listesi**")
                st.write(df['yazar'].value_counts())
        else:
            st.info("İstatistikleri görmek için kitap ekleyin.")
