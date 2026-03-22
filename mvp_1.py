import streamlit as st
import pytesseract
from PIL import Image
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

@st.cache_data(ttl=86400)
def load_points_db():
    """Scrapes all player MVP points directly from the web instead of using a local dataset."""
    db = {}
    # Target the official IPL stats URL
    url = "https://www.iplt20.com/stats/2025/player-points"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            st.warning("⚠️ Could not find the stats table on the IPL website. The site might be using JavaScript rendering.")
            return db
            
        rows = table.find_all('tr')
        for row in rows[1:]: # Skip the header row
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 3:
                # Extract the player name (usually the 2nd column)
                name_raw = cols[1].text.strip().lower()
                name_clean = re.sub(r'\s+', ' ', name_raw).strip()
                
                # Extract points (usually the last column)
                try:
                    points = float(cols[-1].text.strip())
                    db[name_clean] = points
                except ValueError:
                    continue
                    
    except Exception as e:
        st.error(f"Error fetching data from IPL website: {e}")
        
    return db

def get_points(player_name, db):
    normalized_name = player_name.strip().lower()
    return db.get(normalized_name, 0.0)

st.title("IPL Fantasy Calculator")
st.write("Upload a JPG or PDF with your team's players to calculate total points!")

db = load_points_db()

if not db:
    st.warning("⚠️ The scraped player database is currently empty. The web scraper may need adjustments if the website layout changed.")

uploaded_file = st.file_uploader("Upload Roster", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file is not None and db:
    text = ""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    with st.spinner("Extracting players..."):
        if file_type == 'pdf':
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif file_type in ['jpg', 'jpeg', 'png']:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
            
    if text:
        names = [line.strip() for line in text.split('\n') if line.strip()]
        total_points = 0.0
        
        st.subheader("Extracted Players & Points:")
        for name in names:
            points = get_points(name, db)
            total_points += points
            if points > 0:
                st.success(f"{name}: **{points}** pts")
            else:
                st.error(f"{name}: **Not found in DB**")
                
        st.subheader(f"🏆 Total Team Points: {total_points}")
