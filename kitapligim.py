import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import pandas as pd
import plotly.graph_objects as go # Yuvarlak grafikler için

# 1. Sayfa Konfigürasyonu
st.set_page_config(page_title="Library Pro Max Dashboard", page_icon="📚", layout="wide")

# 2. Ultra Modern Dashboard CSS
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp {
        background-color: #f0f2f6; /* Açık gri arka plan */
    }

    /* Üst Navigasyon / Başlık Bandı */
    .main-header {
        background: linear-gradient(90deg, #4b79a1 0%, #283e51 100%); /* Koyu lacivert/gri gradyan */
        padding: 15px 25px;
        border-radius: 15px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8em;
    }
    .main-header .date-info {
        font-size: 0.9em;
        opacity: 0.8;
    }

    /* Dashboard Kartları */
    .dashboard-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        height: 100%; /* Kartların aynı hizada durması için */
    }
    .dashboard-card h3 {
        color: #333;
        font-size: 1.2em;
        margin-bottom: 15px;
    }

    /* Metrik Kutuları */
    [data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.02);
        border: 1px solid #e2e8f0;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8em;
        font-weight: 600;
        color: #283e51;
    }
    [data-testid="stMetricLabel"] {
        color: #666;
        font-size: 0.9em;
    }

    /* Butonlar ve Seçim Kutuları */
    .stButton>button {
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.2s ease;
        background: #4A90E2;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(74,144,226,0.2);
    }

    /* Durum Etiketleri */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 500;
        color: white;
        margin-top: 5px;
    }

    /* Yazar Profilleri (Görseldeki gibi) */
    .author-profile {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    .author-profile img {
        border-radius: 50%;
        margin-right: 10px;
        width: 40px;
        height: 40px;
        object-fit: cover;
    }
    .author-profile .author-name {
        font-weight: 600;
        color: #333;
    }
    .author-profile .book-count {
        font-size: 0.8em;
        color: #777;
        margin-left: auto;
    }

    /* Yuvarlak Grafik Legend Stili */
    .js-plotly-plot .plotly .legend .item {
        font-size: 12px !important;
    }

    </style>
    """, unsafe_allow_html=True)

# 3. Giriş Kontrolü
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Login sayfasında da modern başlık
    st.markdown(f'''
        <div class="main-header">
            <h1>📚 Library Pro Max</h1>
            <span class="date-info">{pd.Timestamp.now().strftime('%A, %B %d, %Y %I:%M %p')}</span>
        </div>
    ''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.form("login_form"):
            pwd = st.text_input("Giriş Şifresi", type="password", help="Şifre: 1234")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                if pwd == "1234":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Hatalı Şifre!")
    st.image("https://via.placeholder.com/600x200?text=Hoşgeldiniz", use_container_width=True) # Alt kısımda bir hoşgeldin görseli

else:
    # --- Supabase Bağlantısı ---
    conn = st.connection("supabase", type=SupabaseConnection)

    # --- Üst Başlık ve Tarih ---
    st.markdown(f'''
        <div class="main-header">
            <h1>📚 Library Pro Max</h1>
            <span class="date-info">{pd.Timestamp.now().strftime('%A, %B %d, %Y %I:%M %p')}</span>
        </div>
    ''', unsafe_allow_html=True)

    # --- Sekmeler ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Keşfet", "🏠 Koleksiyon", "📊 Analizler", "👤 Profil"])

    # --- TAB 1: KİTAP KEŞFET ---
    with tab1:
        st.markdown("<div class='dashboard-card'><h3>Yeni Kitaplar Keşfet</h3>", unsafe_allow_html=True)
        search_query = st.text_input("Kitap veya Yazar Ara...", placeholder="Örn: Nutuk, Dostoyevski...", key="discover_search")
        if search_query:
            with st.spinner('Kitaplar aranıyor...'):
                try:
                    search_url = f"https://openlibrary.org/search.json?q={search_query.replace(' ', '+')}&limit=10"
                    res = requests.get(search_url, timeout=8).json()
                    docs = res.get('docs', [])
                    
                    if docs:
                        for doc in docs:
                            col_img, col_info, col_action = st.columns([1, 3, 1.5])
                            with col_img:
                                cover_id = doc.get('cover_i')
                                img_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "https://via.placeholder.com/80x120?text=Kapak+Yok"
                                st.image(img_url, width=80)
                            with col_info:
                                st.markdown(f"**{doc.get('title', 'Bilinmeyen Başlık')}**")
                                author = doc.get('author_name', ['Bilinmiyor'])[0]
                                year = doc.get('first_publish_year', 'N/A')
                                st.caption(f"✍️ {author} | 📅 {year}")
                            with col_action:
                                status_option = st.selectbox("Durum", ["Okuyacağım", "Okuyorum", "Okudum"], key=f"ds_{doc.get('key')}", label_visibility="collapsed")
                                if st.button("➕ Ekle", key=f"da_{doc.get('key')}", use_container_width=True):
                                    conn.table("kitaplar").insert([{"kitap_id": doc.get('key'), "kitap_adi": doc.get('title'), "yazar": author, "durum": status_option}]).execute()
                                    st.toast(f"'{doc.get('title')}' eklendi!", icon="✅")
                            st.markdown('<hr style="margin:10px 0; border:0.5px solid #f0f0f0;">', unsafe_allow_html=True)
                    else:
                        st.info("Sonuç bulunamadı. Lütfen daha genel bir arama yapın.")
                except Exception as e:
                    st.error(f"Arama sırasında bir hata oluştu: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: KOLEKSİYONUM ---
    with tab2:
        st.markdown("<div class='dashboard-card'><h3>Koleksiyonum</h3>", unsafe_allow_html=True)
        try:
            res_db = conn.table("kitaplar").select("*").execute()
            my_books = res_db.data
            
            if my_books:
                # Toplam Kitap Metriği
                st.metric("Toplam Kitap Sayısı", len(my_books))
                st.markdown('<hr style="margin:15px 0;">', unsafe_allow_html=True)

                collection_search = st.text_input("Koleksiyonumda Ara...", placeholder="Kitap adı veya yazar...", key="collection_search")
                filtered_collection = [
                    book for book in my_books 
                    if collection_search.lower() in book['kitap_adi'].lower() or collection_search.lower() in book['yazar'].lower()
                ]

                if filtered_collection:
                    for book in filtered_collection:
                        col_text, col_status, col_delete = st.columns([3, 1.5, 0.8])
                        with col_text:
                            st.markdown(f"**{book['kitap_adi']}**")
                            st.caption(f"✍️ {book['yazar']}")
                        with col_status:
                            status_color = {"Okuyacağım": "#3498db", "Okuyorum": "#f1c40f", "Okudum": "#2ecc71"}
                            st.markdown(f'<span class="status-badge" style="background-color:{status_color.get(book["durum"], "#95a5a6")};">{book["durum"]}</span>', unsafe_allow_html=True)
                        with col_delete:
                            if st.button("🗑️", key=f"del_{book['id']}", use_container_width=True):
                                conn.table("kitaplar").delete().eq("id", book['id']).execute()
                                st.toast(f"'{book['kitap_adi']}' silindi.", icon="🗑️")
                                st.rerun()
                        st.markdown('<hr style="margin:8px 0; border:0.5px solid #f8f8f8;">', unsafe_allow_html=True)
                else:
                    st.info("Koleksiyonunuzda eşleşen kitap bulunamadı.")
            else:
                st.info("Koleksiyonunuz henüz boş. 'Keşfet' sekmesinden kitap ekleyin!")
        except Exception as e:
            st.error(f"Koleksiyon yüklenirken hata oluştu: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 3: ANALİZLER (GÖRSELDEKİ DASHBOARD) ---
    with tab3:
        st.markdown("<div class='dashboard-card'><h3>Okuma Analizleri</h3>", unsafe_allow_html=True)
        try:
            res_db = conn.table("kitaplar").select("*").execute()
            all_books = res_db.data
            
            if all_books:
                df_books = pd.DataFrame(all_books)

                # Üst Metrikler
                col1, col2, col3 = st.columns(3)
                total_books = len(df_books)
                read_books = len(df_books[df_books['durum'] == "Okudum"])
                
                col1.metric("Toplam Kitap", total_books)
                col2.metric("Tamamlanan", f"{int((read_books / total_books * 100) if total_books > 0 else 0)}%")
                col3.metric("Okuma Skoru", f"{min(100, int((read_books / total_books * 100 * 1.2) if total_books > 0 else 0))}%") # Biraz bonus puan

                st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)

                # Orta Bölüm: Yuvarlak Grafikler ve Yazar Profilleri
                chart_col, authors_col = st.columns([2, 1])

                with chart_col:
                    st.markdown("<h3>Okuma Alışkanlıkları</h3>", unsafe_allow_html=True)
                    status_counts = df_books['durum'].value_counts()
                    
                    if not status_counts.empty:
                        labels = status_counts.index
                        values = status_counts.values
                        
                        # Yuvarlak (Donut) Grafik Oluşturma
                        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7,
                                                    marker_colors=['#4A90E2', '#FFC107', '#28A745'], # Mavi, Sarı, Yeşil
                                                    hoverinfo="label+percent+value")])
                        fig.update_layout(showlegend=True,
                                        margin=dict(l=0, r=0, t=0, b=0),
                                        height=250, width=350,
                                        annotations=[dict(text=f'{total_books}<br>Kitap', x=0.5, y=0.5, font_size=20, showarrow=False)])
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.info("Okuma durumu verisi yok.")

                with authors_col:
                    st.markdown("<h3>En Çok Okunan Yazarlar</h3>", unsafe_allow_html=True)
                    top_authors = df_books['yazar'].value_counts().head(5)
                    for author, count in top_authors.items():
                        # Yazar görseli için placeholder
                        author_img = "https://via.placeholder.com/40x40?text=👤" # Gerçek görsel yerine placeholder
                        st.markdown(f'''
                            <div class="author-profile">
                                <img src="{author_img}">
                                <span class="author-name">{author}</span>
                                <span class="book-count">{count} Kitap</span>
                            </div>
                        ''', unsafe_allow_html=True)
                    st.markdown("<p style='text-align:center; color:#888; font-size:0.9em; margin-top:20px;'>'Daha fazlasını keşfetmeye devam et!'</p>", unsafe_allow_html=True)

            else:
                st.info("Analizleri görmek için koleksiyonunuza kitap ekleyin.")
        except Exception as e:
            st.error(f"Analizler yüklenirken hata oluştu: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 4: PROFİL (BASİT BİR YER TUTUCU) ---
    with tab4:
        st.markdown("<div class='dashboard-card'><h3>Profil Ayarları</h3>", unsafe_allow_html=True)
        st.write("Bu bölümde kullanıcı profil ayarları ve kişiselleştirme seçenekleri yer alacaktır.")
        st.text_input("Adınız", value="Koray")
        st.text_input("Email", value="koray@example.com")
        if st.button("Profili Kaydet"):
            st.success("Profil güncellendi!")
        if st.button("Çıkış Yap", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
