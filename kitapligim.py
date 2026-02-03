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
    .summary-text {
        font-size: 0.95em; color: #444; background: #fff9f9; padding: 15px;
        border-radius: 10px; border-left: 5px solid #b21f1f; margin: 10px 0;
    }
    .author-item { display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f0f0f0; }
    .author-img { width: 55px; height: 80px; object-fit: cover; border-radius: 8px; margin-right: 18px; }
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
                else: st.error("❌ Hatalı Şifre!")
else:
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
    except:
        st.error("Veritabanı bağlantı hatası.")
        st.stop()

    st.markdown('<div class="main-header"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Koleksiyonum", "📊 Okuma Analizi"])

    # --- TAB 1: GELİŞMİŞ KİTAP KEŞFET ---
    with tab1:
        st.markdown("<div class='dashboard-card'><h3>🔍 Geniş Kapsamlı Arama</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap, yazar veya konu yazın...", key="search_k")
        if q:
            with st.spinner('Derin arama yapılıyor...'):
                try:
                    # 'q' yerine 'title' veya 'author' gibi spesifik alanlar yerine genel 'q' kullanarak kapsama alanını genişlettik
                    # limit=15 yaparak daha fazla sonuç gelmesini sağladık
                    search_url = f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=15"
                    res = requests.get(search_url, timeout=10).json()
                    docs = res.get('docs', [])
                    
                    if not docs:
                        st.warning("Sonuç bulunamadı. Lütfen daha genel kelimelerle (sadece yazar soyadı veya sadece kitap adı gibi) tekrar deneyin.")
                    
                    for doc in docs:
                        col1, col2, col3 = st.columns([1, 3, 1.5])
                        cover_id = doc.get('cover_i')
                        img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x120?text=Yok"
                        
                        with col1:
                            st.image(img, width=100)
                        
                        with col2:
                            st.markdown(f"#### {doc.get('title')}")
                            author = doc.get('author_name', ['Bilinmiyor'])[0]
                            year = doc.get('first_publish_year', 'N/A')
                            st.write(f"✍️ **Yazar:** {author} | 📅 **Yıl:** {year}")
                            
                            if st.button("📖 Özeti Gör", key=f"sum_{doc.get('key')}"):
                                try:
                                    details = requests.get(f"https://openlibrary.org{doc.get('key')}.json", timeout=5).json()
                                    desc = details.get('description')
                                    desc_text = desc.get('value') if isinstance(desc, dict) else desc
                                    if desc_text:
                                        st.markdown(f"<div class='summary-text'>{desc_text[:800]}...</div>", unsafe_allow_html=True)
                                    else:
                                        st.info("Bu spesifik baskı için özet bulunamadı.")
                                except:
                                    st.warning("Özet yüklenemedi.")

                        with col3:
                            st.write("##")
                            status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}")
                            if st.button("➕ Ekle", key=f"add_{doc.get('key')}", use_container_width=True, type="primary"):
                                conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status}]).execute()
                                st.toast("Eklendi!")
                        st.divider()
                except Exception as e:
                    st.error("Bir sorun oluştu. İnternet bağlantınızı kontrol edin.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='dashboard-card'><h3>🏠 Koleksiyonunuz ({len(my_books)} Kitap)</h3>", unsafe_allow_html=True)
                for b in my_books:
                    c_inf, c_status, c_del = st.columns([3, 2, 0.5])
                    with c_inf:
                        st.markdown(f"**{b['kitap_adi']}**")
                        st.caption(f"✍️ {b['yazar']}")
                    with c_status:
                        opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                        idx = opts.index(b['durum']) if b['durum'] in opts else 0
                        new_s = st.selectbox("Güncelle", opts, index=idx, key=f"up_{b['id']}", label_visibility="collapsed")
                        if new_s != b['durum']:
                            conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                            st.toast("Durum güncellendi.")
                    with c_del:
                        if st.button("🗑️", key=f"del_{b['id']}"):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.rerun()
                    st.markdown('<hr style="margin:8px 0; border:0.1px solid #eee;">', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Kütüphaneniz henüz boş.")
        except: pass

    # --- TAB 3: ANALİZLER ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            col_l, col_r = st.columns([1.5, 1])
            with col_l:
                st.markdown("<div class='dashboard-card'><h3>📊 Okuma Dağılımı</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.6, marker=dict(colors=['#1a2a6c', '#2ecc71', '#f1c40f']))])
                fig.update_layout(height=350, margin=dict(l=20,r=20,b=20,t=20))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_r:
                st.markdown("<div class='dashboard-card'><h3>✍️ En Çok Okunanlar</h3>", unsafe_allow_html=True)
                top_authors = df['yazar'].value_counts().head(5)
                for author, count in top_authors.items():
                    st.markdown(f"<div class='author-item'><b>{author}</b>: {count} Kitap</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
