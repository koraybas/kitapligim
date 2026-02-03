import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go
import urllib.parse

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
    .summary-box {
        background: #f1f5f9; border-left: 5px solid #3182ce; padding: 15px; 
        border-radius: 10px; margin-top: 10px; font-size: 0.92rem; color: #1e293b;
        max-height: 250px; overflow-y: auto; line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# Yazar isimlerini temizleme fonksiyonu
def normalize_author_name(name):
    if not name: return "Bilinmiyor"
    name = name.strip().title()
    trans = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return name.translate(trans)

# 3. Giriş Sistemi
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-container"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1></div>', unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1, 1, 1])
    with col2:
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı Şifre!")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown(f'''<div class="header-container"><h1>📚 KORAY BASARAN KÜTÜPHANE</h1>
    <div style="background: #3182ce; padding: 8px 15px; border-radius: 10px; font-size: 0.8rem; font-weight: bold;">v10.3 FIXED</div></div>''', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Koleksiyonum", "📊 Analiz"])

    # --- TAB 1: GELİŞMİŞ HİBRİT KEŞFET ---
    with tab1:
        st.markdown("<div class='stat-card'><h3>🔍 Kapsamlı Kitap ve Yazar Arama</h3>", unsafe_allow_html=True)
        q = st.text_input("", placeholder="Kitap veya yazar adı...", key="ultra_search")
        
        if q:
            with st.spinner('Kütüphaneler taranıyor...'):
                combined_results = []
                search_query = urllib.parse.quote(q)
                
                # A: Google Books
                try:
                    g_res = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={search_query}&maxResults=8", timeout=5).json()
                    if 'items' in g_res:
                        for item in g_res['items']:
                            info = item.get('volumeInfo', {})
                            combined_results.append({
                                'source': 'google', 'id': item.get('id'),
                                'title': info.get('title', 'Başlıksız'),
                                'author': info.get('authors', ['Bilinmiyor'])[0],
                                'cover': info.get('imageLinks', {}).get('thumbnail', ""),
                                'desc': info.get('description', 'Özet bilgisi mevcut değil.')
                            })
                except: pass

                # B: Open Library
                try:
                    ol_res = requests.get(f"https://openlibrary.org/search.json?q={search_query}&limit=8", timeout=5).json()
                    if 'docs' in ol_res:
                        for doc in ol_res['docs']:
                            cid = doc.get('cover_i')
                            combined_results.append({
                                'source': 'ol', 'id': doc.get('key').replace('/', '_'),
                                'title': doc.get('title', 'Başlıksız'),
                                'author': doc.get('author_name', ['Bilinmiyor'])[0],
                                'cover': f"https://covers.openlibrary.org/b/id/{cid}-M.jpg" if cid else "",
                                'desc': doc.get('key')
                            })
                except: pass

                if combined_results:
                    for b in combined_results:
                        with st.container():
                            c1, c2, c3 = st.columns([1, 3, 1.5])
                            with c1: st.image(b['cover'] if b['cover'] else "https://via.placeholder.com/100x150", width=100)
                            with c2:
                                st.markdown(f"#### {b['title']}")
                                st.write(f"✍️ {b['author']}")
                                if st.button("📖 Özet Bilgi", key=f"sum_{b['id']}"):
                                    if b['source'] == 'ol':
                                        try:
                                            # JSONDecodeError'ı engellemek için kontrol ekledik
                                            resp = requests.get(f"https://openlibrary.org{b['desc']}.json", timeout=5)
                                            if resp.status_code == 200:
                                                det = resp.json()
                                                d_val = det.get('description', 'Özet bulunamadı.')
                                                final_txt = d_val.get('value') if isinstance(d_val, dict) else d_val
                                                st.markdown(f"<div class='summary-box'>{final_txt}</div>", unsafe_allow_html=True)
                                            else: st.warning("Open Library detayı şu an veremiyor.")
                                        except: st.warning("Özet yükleme hatası.")
                                    else:
                                        st.markdown(f"<div class='summary-box'>{b['desc']}</div>", unsafe_allow_html=True)
                            with c3:
                                st.write("##")
                                status = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{b['id']}")
                                if st.button("➕ Ekle", key=f"add_{b['id']}", use_container_width=True):
                                    conn.table("kitaplar").insert([{"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}]).execute()
                                    st.toast("Koleksiyona eklendi!")
                            st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        try:
            db_res = conn.table("kitaplar").select("*").execute()
            my_books = db_res.data
            if my_books:
                st.markdown(f"<div class='stat-card'><h3>🏠 Koleksiyonum ({len(my_books)} Kitap)</h3>", unsafe_allow_html=True)
                for bk in my_books:
                    ci, cs, cd = st.columns([3, 1.5, 0.7])
                    ci.markdown(f"**{bk['kitap_adi']}**<br><small>{bk['yazar']}</small>", unsafe_allow_html=True)
                    opts = ["Okuyacağım", "Okuyorum", "Okudum"]
                    new_s = cs.selectbox("Durum", opts, index=opts.index(bk['durum']) if bk['durum'] in opts else 0, key=f"up_{bk['id']}", label_visibility="collapsed")
                    if new_s != bk['durum']:
                        conn.table("kitaplar").update({"durum": new_s}).eq("id", bk['id']).execute()
                        st.rerun()
                    if cd.button("🗑️", key=f"del_{bk['id']}", use_container_width=True):
                        conn.table("kitaplar").delete().eq("id", bk['id']).execute()
                        st.rerun()
                    st.divider()
            else: st.info("Koleksiyonunuz boş.")
        except: pass

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
        else: st.info("İstatistik için kitap ekleyin.")
