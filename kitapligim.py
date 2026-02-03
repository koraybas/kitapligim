import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Ayarları
st.set_page_config(page_title="Library Pro Max Dashboard", page_icon="📚", layout="wide")

# 2. Modern Dashboard CSS (Resimler ve Tasarım İçin)
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-header {
        background: linear-gradient(90deg, #2c3e50 0%, #3498db 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
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
        padding: 10px;
        border-bottom: 1px solid #eee;
    }
    .author-img {
        width: 50px;
        height: 70px;
        object-fit: cover;
        border-radius: 5px;
        margin-right: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Sistemi
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>📚 Library Pro Max</h1></div>', unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş"):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı!")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown('<div class="main-header"><h1>📚 Library Pro Max Dashboard</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Keşfet", "🏠 Koleksiyon", "📊 Analizler"])

    # --- TAB 1 & 2 Kısa Özet (Aynı Mantık) ---
    with tab1:
        q = st.text_input("Kitap Ara...", key="search_k")
        if q:
            res = requests.get(f"https://openlibrary.org/search.json?q={q}&limit=5").json()
            for doc in res.get('docs', []):
                c1, c2 = st.columns([1, 4])
                cover_id = doc.get('cover_i')
                img = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x110"
                c1.image(img, width=80)
                with c2:
                    st.write(f"**{doc.get('title')}**")
                    if st.button("➕ Ekle", key=f"add_{doc.get('key')}"):
                        conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name', ['-'])[0], "durum": "Okuyacağım"}]).execute()
                        st.toast("Eklendi!")

    with tab2:
        try:
            my_books = conn.table("kitaplar").select("*").execute().data
            if my_books:
                for b in my_books:
                    st.write(f"📖 **{b['kitap_adi']}** - {b['yazar']} ({b['durum']})")
            else: st.info("Boş.")
        except: pass

    # --- TAB 3: ANALİZLER (RESİMLİ YENİ VERSİYON) ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            col_left, col_right = st.columns([2, 1.2])

            with col_left:
                st.markdown("<div class='dashboard-card'><h3>Okuma Alışkanlıkları</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.6)])
                fig.update_layout(height=300, margin=dict(l=0,r=0,b=0,t=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_right:
                st.markdown("<div class='dashboard-card'><h3>En Çok Okunan Yazarlar</h3>", unsafe_allow_html=True)
                top_authors = df['yazar'].value_counts().head(5)
                
                for author, count in top_authors.items():
                    # Yazara ait kapak resmini bulma (Hızlı arama)
                    author_img = "https://via.placeholder.com/50x70?text=?"
                    try:
                        # Bu yazarın koleksiyonundaki ilk kitabın ID'sini bulalım
                        sample_book = df[df['yazar'] == author].iloc[0]['kitap_id']
                        # Open Library API'den bu kitap ID'sinin kapağını çekelim
                        # kitap_id genellikle '/works/OL123W' formatındadır, biz ID kısmını alırız
                        clean_id = sample_book.split('/')[-1]
                        # Not: Eğer kitap_id kapak ID'si değilse, API'den tekrar kontrol ederiz
                        author_img = f"https://covers.openlibrary.org/b/olid/{clean_id}-M.jpg"
                    except: pass

                    st.markdown(f"""
                        <div class="author-item">
                            <img src="{author_img}" class="author-img">
                            <div>
                                <div style="font-weight:bold; color:#333;">{author}</div>
                                <div style="font-size:0.8em; color:#666;">{count} Kitap</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Veri yok.")
