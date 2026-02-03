import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="Library Pro Max", page_icon="📚", layout="wide")

# 2. Modern Tasarım (CSS)
st.markdown("""
    <style>
    .stApp { background: #f8fafc; }
    .hero-section {
        background: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .book-row {
        background: white;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
    }
    .author-tag {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Kontrolü
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="hero-section"><h1>🔐 Library Pro</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("Kütüphaneyi Aç", use_container_width=True):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı!")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown('<div class="hero-section"><h1>✨ Library Pro Dashboard</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Genişletilmiş Kitap Ara", "🏠 Koleksiyonum", "📊 Analizler"])

    # --- TAB 1: GÜÇLENDİRİLMİŞ ARAMA ---
    with tab1:
        q = st.text_input("", placeholder="Kitap, yazar veya konu ara (Örn: Reşat Nuri Güntekin)...", key="search")
        if q:
            # LİMİTİ 20'YE ÇIKARDIK VE SIRALAMAYI DOĞRULADIK
            search_url = f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=20&mode=everything"
            with st.spinner('Kütüphane taranıyor, lütfen bekleyin...'):
                try:
                    res = requests.get(search_url, timeout=10).json()
                    docs = res.get('docs', [])
                    
                    if docs:
                        st.write(f"🔍 **{len(docs)}** sonuç bulundu.")
                        for doc in docs:
                            with st.container():
                                # Tasarımı daha ince (row) hale getirdik
                                col1, col2, col3 = st.columns([0.6, 3, 1.4])
                                
                                with col1:
                                    cid = doc.get('cover_i')
                                    img_url = f"https://covers.openlibrary.org/b/id/{cid}-S.jpg" if cid else "https://via.placeholder.com/60x90?text=Yok"
                                    st.image(img_url, width=60)
                                
                                with col2:
                                    st.markdown(f"**{doc.get('title')}**")
                                    author = doc.get('author_name', ['Bilinmiyor'])[0]
                                    year = doc.get('first_publish_year', 'N/A')
                                    st.caption(f"✍️ {author} | 📅 {year}")
                                
                                with col3:
                                    status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}", label_visibility="collapsed")
                                    if st.button("➕ Ekle", key=f"a_{doc.get('key')}", use_container_width=True):
                                        conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                                        st.toast(f"Eklendi: {doc.get('title')}")
                            st.markdown('<hr style="margin:5px 0; border:0.1px solid #eee">', unsafe_allow_html=True)
                    else:
                        st.warning("Maalesef sonuç bulunamadı. Aramayı basitleştirmeyi deneyin.")
                except:
                    st.error("Bağlantı hatası. Lütfen tekrar deneyin.")

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        try:
            res_db = conn.table("kitaplar").select("*").execute()
            my_books = res_db.data
            if my_books:
                st.write(f"📚 Toplam **{len(my_books)}** kitabınız var.")
                for b in my_books:
                    c_inf, c_d = st.columns([5, 1])
                    with c_inf:
                        st.markdown(f"**{b['kitap_adi']}** - <small>{b['yazar']}</small> ` {b['durum']} `", unsafe_allow_html=True)
                    with c_d:
                        if st.button("🗑️", key=f"d_{b['id']}", use_container_width=True):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
            else: st.info("Koleksiyonunuz boş.")
        except: st.error("Veritabanı hatası.")

    # --- TAB 3: ANALİZ & ÖZET ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam", len(df))
            read_count = len(df[df['durum'] == "Okudum"])
            m2.metric("Biten", read_count)
            m3.metric("Tamamlama", f"%{int(read_count/len(df)*100) if len(df)>0 else 0}")
            
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                st.write("📊 **Okuma Durumu**")
                st.bar_chart(df['durum'].value_counts(), height=200)
            with cr:
                st.write("🏷️ **Favori Yazarlar**")
                authors = df['yazar'].value_counts().head(5)
                for auth, count in authors.items():
                    st.markdown(f'<span class="author-tag">{auth} ({count})</span>', unsafe_allow_html=True)
        else:
            st.info("Analiz için veri ekleyin.")
