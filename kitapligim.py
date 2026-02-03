import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="KORAY BASARAN KÜTÜPHANE", page_icon="📚", layout="wide")

# 2. Modern Tasarım CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f4f7fa; }
    .header-container {
        background: #1a202c; padding: 25px; border-radius: 20px; color: white;
        margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        display: flex; justify-content: space-between; align-items: center;
    }
    .stat-card {
        background: white; border-radius: 18px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #edf2f7; margin-bottom: 15px;
    }
    .book-row {
        padding: 15px 0;
        border-bottom: 1px solid #edf2f7;
    }
    </style>
    """, unsafe_allow_html=True)

# İsim Normalleştirme
def normalize_author_name(name):
    if not name: return "Bilinmiyor"
    name = name.strip().title()
    translation_table = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return name.translate(translation_table)

# 3. Giriş Sistemi
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-container"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1, 1, 1])
    with col2:
        pwd = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı Şifre")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown(f'''
        <div class="header-container">
            <h1>📚 KORAY BASARAN KÜTÜPHANE</h1>
            <div style="background: #2d3748; padding: 8px 15px; border-radius: 10px; font-size: 0.8rem;">FIXED UI v9.2</div>
        </div>
    ''', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Koleksiyonum", "📊 Analiz"])

    # --- TAB 1: KEŞFET ---
    with tab1:
        st.markdown("<div class='stat-card'><h3>🔍 Global ve Türkçe Arama</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap veya yazar adı yazın...", key="search_bar")
        if q:
            with st.spinner('Aranıyor...'):
                combined_results = []
                try:
                    g_res = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={q.replace(' ', '+')}&maxResults=8").json()
                    for item in g_res.get('items', []):
                        info = item.get('volumeInfo', {})
                        combined_results.append({
                            'id': f"g_{item.get('id')}",
                            'title': info.get('title'),
                            'author': info.get('authors', ['Bilinmiyor'])[0],
                            'cover': info.get('imageLinks', {}).get('thumbnail', ""),
                            'desc': info.get('description', 'Özet yok.')
                        })
                except: pass

                if combined_results:
                    for book in combined_results:
                        with st.container():
                            col1, col2, col3 = st.columns([1, 3, 1.5])
                            with col1: st.image(book['cover'] if book['cover'] else "https://via.placeholder.com/100x150", width=100)
                            with col2:
                                st.markdown(f"#### {book['title']}")
                                st.write(f"✍️ {book['author']}")
                                if st.button("📖 Özet", key=f"sum_{book['id']}"):
                                    st.info(book['desc'])
                            with col3:
                                st.write("##")
                                status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{book['id']}")
                                if st.button("➕ Ekle", key=f"add_{book['id']}", use_container_width=True):
                                    conn.table("kitaplar").insert([{"kitap_id": book['id'], "kitap_adi": book['title'], "yazar": book['author'], "durum": status}]).execute()
                                    st.toast("Eklendi!")
                        st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM (SİLME BUTONU DÜZELTİLDİ) ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='stat-card'><h3>🏠 Koleksiyon ({len(my_books)} Kitap)</h3>", unsafe_allow_html=True)
                
                # Başlık Satırı
                h1, h2, h3 = st.columns([3, 1.5, 0.7])
                h1.caption("KİTAP VE YAZAR")
                h2.caption("DURUM")
                h3.caption("İŞLEM")
                st.divider()

                for b in my_books:
                    c_info, c_status, c_del = st.columns([3, 1.5, 0.7])
                    
                    with c_info:
                        st.markdown(f"**{b['kitap_adi']}**")
                        st.markdown(f"<small style='color:gray;'>{b['yazar']}</small>", unsafe_allow_html=True)
                    
                    with c_status:
                        opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                        current_idx = opts.index(b['durum']) if b['durum'] in opts else 0
                        new_s = st.selectbox("Durum", opts, index=current_idx, key=f"up_{b['id']}", label_visibility="collapsed")
                        if new_s != b['durum']:
                            conn.table("kitaplar").update({"durum": new_s}).eq("id", b['id']).execute()
                            st.rerun()

                    with c_del:
                        # Butonun her zaman en sağda ve erişilebilir olması için
                        if st.button("🗑️", key=f"del_{b['id']}", use_container_width=True, help="Silmek için tıklayın"):
                            conn.table("kitaplar").delete().eq("id", b['id']).execute()
                            st.toast("Kitap silindi.")
                            st.rerun()
                    
                    st.markdown("<hr style='margin:10px 0; border:0.1px solid #edf2f7;'>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Koleksiyonunuz şu an boş.")
        except Exception as e:
            st.error(f"Veri yükleme hatası: {e}")

    # --- TAB 3: ANALİZ ---
    with tab3:
        if 'my_books' in locals() and my_books:
            df = pd.DataFrame(my_books)
            df['clean_author'] = df['yazar'].apply(normalize_author_name)
            col_l, col_r = st.columns([1.5, 1])
            with col_l:
                st.markdown("<div class='stat-card'><h3>📊 Dağılım</h3>", unsafe_allow_html=True)
                counts = df['durum'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.6, marker=dict(colors=['#1a202c', '#48bb78', '#ecc94b']))])
                fig.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_r:
                st.markdown("<div class='stat-card'><h3>🔝 Yazarlar</h3>", unsafe_allow_html=True)
                top_authors = df['clean_author'].value_counts().head(5)
                for author, count in top_authors.items():
                    orig = df[df['clean_author'] == author]['yazar'].iloc[0]
                    st.write(f"👤 **{orig}**: {count} Kitap")
        else: st.info("Analiz için veri ekleyin.")
