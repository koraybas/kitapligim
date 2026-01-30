import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="Kitap Yolculuğum PRO", page_icon="📚", layout="wide")

# 2. Şık Görünüm (CSS)
st.markdown("""
    <style>
    .book-card { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
    .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- ÖZELLİK 1: BASİT GİRİŞ ŞİFRESİ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if st.session_state["password_correct"]:
        return True

    st.title("🔐 Özel Kütüphane Girişi")
    password = st.text_input("Lütfen giriş şifrenizi yazınız:", type="password")
    if st.button("Giriş Yap"):
        if password == "1234": # Şifreni buradan değiştirebilirsin!
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Yanlış şifre!")
    return False

if check_password():
    # 3. Veritabanı Bağlantısı
    conn = st.connection("supabase", type=SupabaseConnection)

    # 4. Arama Motoru
    def search_books(query):
        if not query: return []
        url = f"https://openlibrary.org/search.json?q={query.replace(' ', '+')}&limit=10"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results = []
                for doc in data.get('docs', []):
                    cover_id = doc.get('cover_i')
                    if 'title' in doc and 'author_name' in doc:
                        results.append({
                            "id": doc.get('key'),
                            "title": doc.get('title'),
                            "author": doc.get('author_name')[0],
                            "year": doc.get('first_publish_year', 'N/A'),
                            "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                        })
                return results
        except: return []
        return []

    # 5. Ana Arayüz Tasarımı
    st.title("📚 Kitap Yolculuğum")
    tab1, tab2, tab3 = st.tabs(["🔍 Kitap Keşfet", "🏠 Kitaplığım", "📊 İstatistikler"])

    # --- TAB 1: KİTAP KEŞFET ---
    with tab1:
        search_input = st.text_input("Yeni Kitap Ara...", placeholder="Örn: Nutuk, George Orwell...", key="main_search")
        if search_input:
            books = search_books(search_input)
            if books:
                for b in books:
                    with st.container():
                        c1, c2, c3 = st.columns([1, 2.5, 1.5])
                        with c1:
                            if b['cover']: st.image(b['cover'], use_container_width=True)
                            else: st.info("Kapak Yok")
                        with c2:
                            st.subheader(b['title'])
                            st.write(f"**Yazar:** {b['author']}")
                            st.write(f"**Yıl:** {b['year']}")
                        with c3:
                            st.write("###")
                            status = st.selectbox("Durum:", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"sel_{b['id']}")
                            if st.button("➕ Ekle", key=f"btn_{b['id']}", type="primary", use_container_width=True):
                                conn.table("kitaplar").insert([{"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}]).execute()
                                st.success("Eklendi!")
                                st.balloons()
                    st.divider()

    # --- TAB 2: KİTAPLIĞIM & ÖZELLİK 2: HIZLI ARAMA ---
    with tab2:
        try:
            res = conn.table("kitaplar").select("*").execute()
            my_books = res.data
            
            if my_books:
                # Kendi kitapların içinde arama yapma
                lib_search = st.text_input("📋 Kütüphanende Ara...", placeholder="Kitap veya yazar adı yazın...")
                
                filtered_books = [
                    b for b in my_books 
                    if lib_search.lower() in b['kitap_adi'].lower() or lib_search.lower() in b['yazar'].lower()
                ]

                st.divider()
                for item in filtered_books:
                    renk = "#3498db" if item['durum'] == "Okuyacağım" else "#f1c40f" if item['durum'] == "Okuyorum" else "#2ecc71"
                    with st.container():
                        ci, cd = st.columns([4, 1])
                        with ci:
                            st.markdown(f"""
                            <div style="padding:10px; border-left: 5px solid {renk}; background-color: #fdfdfd; margin-bottom: 5px;">
                                <b>{item['kitap_adi']}</b> - {item['yazar']}
                                <br><span class="status-badge" style="background-color:{renk};">{item['durum']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        with cd:
                            if st.button("🗑️ Sil", key=f"del_{item['id']}", use_container_width=True):
                                conn.table("kitaplar").delete().eq("id", item['id']).execute()
                                st.rerun()
            else:
                st.info("Kütüphanen henüz boş.")
        except Exception as e:
            st.error(f"Hata: {e}")

    # --- TAB 3: ÖZELLİK 3: İSTATİSTİKLER ---
    with tab3:
        st.subheader("📊 Okuma Analizi")
        if my_books:
            df = pd.DataFrame(my_books)
            
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.write("**Okuma Durumları Dağılımı**")
                status_counts = df['durum'].value_counts()
                st.bar_chart(status_counts)
            
            with col_stat2:
                st.write("**En Çok Okunan Yazarlar**")
                author_counts = df['yazar'].value_counts().head(5)
                st.write(author_counts)
            
            st.divider()
            st.metric("Kütüphanedeki Toplam Kitap", len(my_books))
        else:
            st.info("İstatistik oluşturmak için henüz yeterli veri yok.")
