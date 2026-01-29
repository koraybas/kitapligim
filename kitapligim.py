import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests

# 1. Page Configuration
st.set_page_config(page_title="Kitap Yolculuğum", page_icon="📖", layout="wide")

# 2. Custom Styling (CSS)
st.markdown("""
    <style>
    .book-container { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 25px; }
    .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Database Connection
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Search Function (No API Key Required)
def search_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=8&langRestrict=tr"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get('items', []):
                v = item.get('volumeInfo', {})
                results.append({
                    "id": item.get('id'),
                    "title": v.get('title', 'Unknown'),
                    "author": ", ".join(v.get('authors', ['Unknown'])),
                    "desc": v.get('description', 'No summary available.'),
                    "cover": v.get('imageLinks', {}).get('thumbnail', "").replace("http://", "https://")
                })
            return results
    except:
        return []

# 5. User Interface
st.title("📚 Kitap Yolculuğum")
st.write("Türkiye'deki kitapları keşfet ve okuma listeni yönet.")

tab1, tab2 = st.tabs(["🔍 Search & Discover", "🏠 My Library"])

with tab1:
    search_input = st.text_input("Search for a book or author...", placeholder="e.g., Nutuk")
    if search_input:
        books = search_books(search_input)
        for b in books:
            with st.container():
                st.markdown(f"""
                <div class="book-container">
                    <img src="{b['cover']}" style="float:left; width:100px; margin-right:20px; border-radius:8px;">
                    <h3>{b['title']}</h3>
                    <p><b>Author:</b> {b['author']}</p>
                    <p style="color:#666; font-size:0.9em;">{b['desc'][:400]}...</p>
                    <div style="clear:both;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([2,1])
                with c1:
                    status = st.selectbox("Status:", ["Will Read", "Reading", "Read"], key=f"s_{b['id']}")
                with c2:
                    if st.button("Add to Library", key=f"b_{b['id']}"):
                        conn.table("kitaplar").insert([
                            {"kitap_id": b['id'], "kitap_adi": b['title'], "yazar": b['author'], "durum": status}
                        ]).execute()
                        st.success("Added to your library!")

with tab2:
    st.subheader("Your Reading Journey")
    try:
        data = conn.table("kitaplar").select("*").execute()
        if data.data:
            for item in data.data:
                color = "#3498db" if item['durum'] == "Will Read" else "#f1c40f" if item['durum'] == "Reading" else "#2ecc71"
                st.markdown(f"""
                <div style="padding:10px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
                    <div><b>{item['kitap_adi']}</b> - {item['yazar']}</div>
                    <div class="status-badge" style="background-color:{color};">{item['durum']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Your library is empty. Start adding some books!")
    except:
        st.warning("Database connection error. Please check your Supabase settings.")
