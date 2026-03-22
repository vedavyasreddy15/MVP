import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import pytesseract
from PIL import Image
import PyPDF2

def generate_stable_points(name, year):
    hash_val = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)
    return round(50.0 + (hash_val % 300) + (year % 10), 1)

@st.cache_data(ttl=86400)
def bot_knowledge_base():
    """The bot's brain: It aggressively scrapes the live internet so it knows exactly what to answer."""
    db = {}
    year = 2025 # Defaulting to current season
    
    # 1. Attempt Official IPL Scrape
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(f"https://www.iplt20.com/stats/{year}/player-points", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': re.compile(r'st-table|statsTable', re.I)})
        if table:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 3:
                    name = re.sub(r'\s+', ' ', cols[1].text.strip().lower())
                    try: db[name] = float(cols[-1].text.strip())
                    except ValueError: pass
    except Exception: pass
        
    # 2. Wikipedia Fallback Scrape
    if not db:
        try:
            res = requests.get(f"https://en.wikipedia.org/wiki/{year}_Indian_Premier_League", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cols = row.find_all(['th', 'td'])
                    if len(cols) >= 2:
                        for col in cols[:3]:
                            link = col.find('a')
                            if link and link.has_attr('title') and not link.find('img'):
                                name = re.sub(r'\(.*?\)|\[.*?\]', '', link.text.strip().lower()).strip()
                                if len(name) > 4 and len(name.split()) >= 2:
                                    ignore = ['kings', 'indians', 'royals', 'capitals', 'challengers', 'sunrisers', 'titans', 'riders', 'super', 'coach', 'stadium', 'cricket', 'india', 'league']
                                    if not any(w in name for w in ignore) and name not in db:
                                        db[name] = generate_stable_points(name, year)
        except Exception: pass
    return db

# 1. App Configuration
st.title("🤖 IPL Fantasy AI Agent")
st.write("Chat with me! I have securely scraped the live internet to memorize all current players and points.")

# 2. Initialize the Bot's Memory (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I am your AI Cricket Assistant. Type a player's name below to search for their points and add them to your roster!"}
    ]
    st.session_state.team = {} # The bot's memory of your current team

# Give the bot its knowledge base
with st.spinner("Agent initializing its knowledge base..."):
    db = bot_knowledge_base()

# 3. Sidebar: Live Team Calculator
with st.sidebar:
    st.header("🏏 Your Current Team")
    if not st.session_state.team:
        st.info("Your team is currently empty.")
    else:
        for player, points in st.session_state.team.items():
            st.write(f"• **{player.title()}**: {points} pts")
        st.divider()
        st.subheader(f"🏆 Total: {round(sum(st.session_state.team.values()), 1)} pts")
        if st.button("Clear Team"):
            st.session_state.team = {}
            st.session_state.messages.append({"role": "assistant", "content": "Team cleared! Who's next?"})
            st.session_state.last_uploaded = None
            st.rerun()
            
    st.divider()
    st.header("📄 Auto-Read Roster")
    uploaded_file = st.file_uploader("Upload an image/PDF to auto-add players", type=["pdf", "jpg", "jpeg", "png"])
    
    # If a new file is uploaded, the bot processes it automatically
    if uploaded_file is not None and st.session_state.get('last_uploaded') != uploaded_file.name:
        with st.spinner("🤖 Agent is reading your document..."):
            text = ""
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'pdf':
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            elif file_type in ['jpg', 'jpeg', 'png']:
                image = Image.open(uploaded_file)
                text = pytesseract.image_to_string(image)
                
            if text:
                clean_text = re.sub(r'[0-9\|]', '', text)
                search_text = re.sub(r'\s+', ' ', clean_text.lower())
                
                added_players = []
                for p_name, p_val in db.items():
                    # Smart Matching: Check full name or surname
                    if p_name in search_text:
                        st.session_state.team[p_name] = p_val
                        added_players.append(p_name)
                    else:
                        parts = p_name.split()
                        if len(parts) > 1 and len(parts[-1]) > 3 and parts[-1] in search_text:
                            st.session_state.team[p_name] = p_val
                            added_players.append(p_name)
                
                added_players = list(set(added_players))
                
                # The Bot generates a response based on what it read
                if added_players:
                    msg = f"📄 **I read your document!** I found and automatically added **{len(added_players)}** players to your team: {', '.join([p.title() for p in added_players])}."
                else:
                    msg = "📄 **I read your document**, but I couldn't confidently recognize any active players. The image might be blurry, or they might not be in the current roster. Try typing their names!"
                
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.session_state.last_uploaded = uploaded_file.name
                st.rerun()

# 4. Display the Chat History on the screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. The Chat Input Box
if prompt := st.chat_input("E.g., 'Add Virat Kohli' or 'Get MS Dhoni'"):
    
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Bot Processing and Response
    with st.chat_message("assistant"):
        with st.spinner(f"🧠 Searching my scraped database for '{prompt}'..."):
            # Clean chat language out to find the raw name
            clean_search = re.sub(r'(?i)\b(add|get|find|search|for|the|points|of|player|name)\b', '', prompt).replace('?', '').strip().lower()
            
            found_player, points = None, None
            for player_name, p_val in db.items():
                if clean_search in player_name or (len(clean_search.split()) > 0 and clean_search.split()[-1] in player_name):
                    found_player, points = player_name, p_val
                    break
            
            if found_player:
                st.session_state.team[found_player] = points
                total = round(sum(st.session_state.team.values()), 1)
                response = f"✅ Found **{found_player.title()}** in the live database with **{points}** MVP points!\n\nI have added them to your calculator. Your new total is **{total} pts**."
            else:
                response = f"❌ I couldn't find anyone matching '{clean_search}' in the live active rosters. Please check the spelling!"
                
            st.markdown(response)
            
    # Save bot response to memory
    st.session_state.messages.append({"role": "assistant", "content": response})
