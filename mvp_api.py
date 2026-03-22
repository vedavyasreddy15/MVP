import streamlit as st
import pytesseract
from PIL import Image
import PyPDF2
import requests
import re

@st.cache_data(ttl=86400)
def load_points_db(year, source):
    """Fetches ALL players directly from a third-party Sports API."""
    db = {}
    messages = []
    
    # ==========================================
    # 🔑 PUT YOUR API KEY HERE
    # ==========================================
    API_KEY = "YOUR_API_KEY_HERE" 
    
    # Example using a standard JSON API endpoint (like Sportmonks or FreeCricketAPI)
    # You will replace this URL with the exact endpoint provided by your chosen API service.
    api_url = f"https://api.sportmonks.com/v3/cricket/squads?season={year}&api_token={API_KEY}"
    
    try:
        if API_KEY == "YOUR_API_KEY_HERE":
            messages.append(("warning", "⚠️ No API Key found! Using simulated offline data for testing. Please enter your key in mvp_api.py."))
            # Dummy data so your app works perfectly while you register for an API key
            db = {
                "virat kohli": 350.5, "ms dhoni": 200.0, "rohit sharma": 280.0,
                "shubman gill": 250.0, "jitesh sharma": 120.0, "mitchell starc": 180.5, 
                "mitchell marsh": 150.0, "prabhsimran singh": 110.0, "quinton de kock": 210.0, 
                "bhuvneshwar kumar": 175.0, "mohit sharma": 190.0, "yashasvi jaiswal": 240.0,
                "nicholas pooran": 220.0, "harpreet brar": 95.0, "avesh khan": 140.0,
                "josh inglis": 160.0, "ruturaj gaikwad": 230.0, "ravi bishnoi": 155.0,
                "rahmanullah gurbaz": 130.0, "rahul tripathi": 145.0, "deepak chahar": 165.0,
                "devdutt padikkal": 125.0, "harshal patel": 205.0, "jofra archer": 185.0,
                "matheesha pathirana": 195.0, "akash deep": 85.0, "abhinav manohar": 75.0
            }
        else:
            # This is where the magic happens once you have a key!
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # APIs return clean data dictionaries! No HTML parsing needed.
            for player in data.get('data', []):
                name = player.get('name', '').lower()
                points = player.get('fantasy_points', 0.0) # Replace with the actual API field
                if name:
                    db[name] = float(points)
                    
        # Apply website multipliers if they want to simulate other sites
        if db:
            multiplier = 1.0
            if source == "Cricbuzz (Fantasy Points)": multiplier = 1.25
            elif source == "ESPN Cricinfo (Impact Points)": multiplier = 0.85
            db = {k: round(v * multiplier, 1) for k, v in db.items()}
            
            if API_KEY != "YOUR_API_KEY_HERE":
                messages.append(("success", f"✅ Successfully loaded {len(db)} players via API!"))
        else:
            messages.append(("error", "❌ API returned an empty list. Check your endpoint and parameters."))
            
    except Exception as e:
        messages.append(("error", f"API Connection Error: {e}"))
        
    return db, messages

def get_points(player_name, db):
    normalized_name = player_name.strip().lower()
    return db.get(normalized_name, 0.0)

st.title("IPL Fantasy Calculator (API Version)")
st.write("Upload a JPG or PDF with your team's players to calculate total points!")

col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox(
        "Select IPL Season", 
        options=list(range(2026, 2007, -1)),
        index=1
    )
with col2:
    data_source = st.selectbox(
        "Select Data Source",
        options=["Official IPL (via API)", "Cricbuzz (Simulation)", "ESPN Cricinfo (Simulation)"]
    )

with st.spinner("🌐 Connecting to API..."):
    db, messages = load_points_db(selected_year, data_source)

for msg_type, msg in messages:
    if msg_type == "error": st.error(msg)
    elif msg_type == "warning": st.warning(msg)
    elif msg_type == "success": st.success(msg)

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
        clean_text = re.sub(r'[0-9\|]', '', text)
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()
        
        with st.expander("👀 See raw extracted text (Helpful for debugging)"):
            st.text(clean_text)
            
        search_text = re.sub(r'\s+', ' ', clean_text.lower())
        extracted_names = []
        for player in db.keys():
            if player in search_text:
                extracted_names.append(player)
            else:
                parts = player.split()
                if len(parts) > 1 and len(parts[-1]) > 3 and parts[-1] in search_text:
                    extracted_names.append(player)
        extracted_names = list(set(extracted_names))
        
        st.subheader("🏏 Verify Your Team")
        
        selected_players = st.multiselect(
            "Add or Remove Players:",
            options=list(db.keys()), 
            default=extracted_names, 
            format_func=lambda x: x.title()
        )
        
        total_points = 0.0
        st.subheader("Team Breakdown:")
        for name in selected_players:
            points = get_points(name, db)
            total_points += points
            st.success(f"{name.title()}: **{points}** pts")
                
        st.subheader(f"🏆 Total Team Points: {round(total_points, 1)}")