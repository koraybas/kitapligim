import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="Library Pro v2", page_icon="📈", layout="wide")

# 2. Ultra Modern Tasarım (CSS)
st.markdown("""
    <style>
    .stApp { background: #f4f7f6; }
    .hero-section {
        background: white;
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    /* Analiz Kartları */
    .stat-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #edf2f7;
        text-align: center;
    }
    .author-tag {
        display: inline-block;
        background: #e2e8f0;
        color: #4a5568;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 13px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Kontrolü
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="hero-section"><h1>🔐 Library Pro</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        pwd = st.text_input("Giriş Kodu", type="password")
        if st.button("Sistemi Aç", use_container_width=True):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı!")
else:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.markdown('<div class="hero-section"><h1>✨ Library Pro Dashboard</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Ekle", "🏠 Koleksiyon", "📈 Analiz & Özet"])

    # --- TAB 1 & 2 Kısımları (Aynı Mantık, Görsel İyileştirmeli) ---
    with tab1:
        q = st.text_input("", placeholder="Kitap veya Yazar Ara...", key="search")
        if q:
            data = requests.get(f"https://openlibrary.org/search.json?q={q.replace(' ', '+')}&limit=5").json()
            for doc in data.get('docs', []):
                col1, col2 = st.columns([1, 4])
                with col1:
                    cid = doc.get('cover_i')
                    st.image(f"https://covers.openlibrary.org/b/id/{cid}-M.jpg" if cid else "https://via.placeholder.com/80x120", width=80)
                with col2:
                    st.markdown(f"**{doc.get('title')}**")
                    ca, cb = st.columns([2, 1])
                    status = ca.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"s_{doc.get('key')}", label_visibility="collapsed")
                    if cb.button("Ekle", key=f"a_{doc.get('key')}", use_container_width=True):
                        conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": doc.get('author_name')[0], "durum": status}]).execute()
                        st.toast("Kütüphaneye eklendi!")
                st.divider()

    with tab2:
        res = conn.table("kitaplar").select("*").execute()
        my_books = res.data
        if my_books:
            for b in my_books:
                c_inf, c_d = st.columns([5, 1])
                c_inf.markdown(f"**{b['kitap_adi']}** - <small>{b['yazar']}</small> ` {b['durum']} `", unsafe_allow_html=True)
                if c_d.button("🗑️", key=f"d_{b['id']}", use_container_width=True):
                    conn.table("kitaplar").delete().eq("id", b['id']).execute()
                    st.rerun()
        else: st.info("Henüz kitap yok.")

    # --- TAB 3: YENİ ANALİZ FORMATI (TAMAMEN DEĞİŞTİ) ---
    with tab3:
        if my_books:
            df = pd.DataFrame(my_books)
            
            # ÜST SIRA: ÖZET METRİKLER (KART SİSTEMİ)
            st.markdown("### 🎯 Genel Bakış")
            m1, m2, m3, m4 = st.columns(4)
            total = len(df)
            read = len(df[df['durum'] == "Okudum"])
            reading = len(df[df['durum'] == "Okuyorum"])
            
            m1.metric("Koleksiyon", total)
            m2.metric("Tamamlanan", read)
            m3.metric("Şu an", reading)
            score = int((read / total * 100) if total > 0 else 0)
            m4.metric("Okur Skoru", f"%{score}")

            st.write("---")

            # ALT SIRA: YENİ GÖRSEL FORMAT
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("#### 🥧 Okuma Dengesi")
                # Alanı daraltılmış pasta grafiği benzeri bar
                status_df = df['durum'].value_counts().reset_index()
                st.write("Durumlara göre kitap ağırlığınız:")
                st.dataframe(status_df.rename(columns={'count': 'Adet', 'durum': 'Durum'}), hide_index=True, use_container_width=True)
                # İlerleme çubuğu ile görselleştirme
                st.progress(score / 100, text=f"Kütüphane Tamamlama Oranı: %{score}")

            with col_right:
                st.markdown("#### 🏷️ En Çok Okunan Yazarlar")
                authors = df['yazar'].value_counts().head(7)
                # Yazarları liste yerine renkli "Tag/Etiket" formatında gösterelim
                tag_html = ""
                for author, count in authors.items():
                    tag_html += f'<span class="author-tag">{author} ({count})</span>'
                st.markdown(tag_html, unsafe_allow_html=True)
                
                st.write("##")
                # Küçük bir motivasyon mesajı
                if score > 50: st.success("🚀 Harika bir okuma temposu!")
                elif score > 20: st.info("📚 Kütüphanen yavaş yavaş doluyor.")
                else: st.warning("📖 Yeni bir maceraya başlamaya ne dersin?")
        else:
            st.info("Analiz için veri ekleyin.")
