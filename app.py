import os
import re
import json
import hashlib
import sqlite3
import random
import requests
import urllib.parse
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from songs_db import LANG_SONGS as ALL_LANG_SONGS
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

def get_llm_response(user_input, mood, lang='en', user_id=None):
    lang_name = "casual English (like a close friend texting)"
    if lang == "hi": 
        lang_name = "Hinglish (conversational Hindi mixed with English, casual and friendly)"
    elif lang == "te": 
        lang_name = "Tenglish (conversational Telugu mixed with English, casual and friendly)"

    history_text = ""
    if user_id:
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            history = c.execute("SELECT message, mood FROM mood_history WHERE user_id=? ORDER BY id DESC LIMIT 4", (user_id,)).fetchall()
            conn.close()
            history_text = "\n".join([f"User: {row[0]}\nAMIS: {row[1]}" for row in reversed(history)])
            if history_text:
                history_text = f"Recent chat history:\n{history_text}\n"
        except Exception as e:
            print("History error:", e)

    system_prompt = f"""You are AMIS, a warm and caring AI friend. Rules:
1. NEVER repeat or echo what the user said. Give your OWN original response.
2. Be casual, friendly, and natural — like a best friend chatting on WhatsApp.
3. Keep responses short (1-3 sentences max).
4. Use emojis naturally but don't overdo it.
5. You MUST respond in {lang_name}.
6. If user speaks in Telugu/Hindi/English, match their vibe and energy.
7. Give genuine emotional support, not generic advice.
8. If the user asks you to play songs or do something, respond naturally acknowledging it.
{history_text}"""

    messages = [
        {"role":"system","content":system_prompt},
        {"role":"user","content":user_input}
    ]

    # Provider list: try Groq first (fastest), then NVIDIA keys as fallback
    providers = []
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        providers.append({
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key": groq_key,
            "model": "llama-3.3-70b-versatile",
            "name": "Groq"
        })
    for env_name in ["NVIDIA_API_KEY", "NVIDIA_API_KEY_2"]:
        nv_key = os.environ.get(env_name, "")
        if nv_key:
            providers.append({
                "url": "https://integrate.api.nvidia.com/v1/chat/completions",
                "key": nv_key,
                "model": "meta/llama-3.1-70b-instruct",
                "name": f"NVIDIA ({env_name})"
            })

    for p in providers:
        try:
            headers = {"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"}
            payload = {"model": p["model"], "messages": messages, "max_tokens": 150, "temperature": 0.6, "top_p": 0.8, "stream": False}
            response = requests.post(p["url"], headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip()
            print(f"LLM OK via {p['name']}")
            return result
        except Exception as e:
            print(f"LLM Error ({p['name']}): {e}")
            continue
    return None


app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# ============================================================
# DATABASE SETUP
# ============================================================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mood_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  mood TEXT,
                  message TEXT,
                  song TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# ============================================================
# MOOD AI ENGINE
# ============================================================
class MoodAI:
    def __init__(self):
        self.mood_keywords = {
            'happy': {
                'keywords': ['happy', 'great', 'wonderful', 'amazing', 'joy', 'excited', 'fantastic',
                            'good', 'love', 'awesome', 'beautiful', 'glad', 'cheerful', 'delighted',
                            'thrilled', 'blessed', 'grateful', 'smile', 'laugh', 'fun', 'party', 'sunshine',
                            'khushi', 'masti', 'mazaa', 'badhiya', 'shandar', 'zabardast', 'accha',
                            'santosham', 'anandham', 'bagundi', 'chala bagundi', 'super', 'maja'],
                'emoji': '??',
                'frequency': 528,
                'color': '#FFD700',
                'energy': 0.9,
                'songs': [
                    {'title': 'Happy - Pharrell Williams', 'url': 'https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3'},
                    {'title': 'Walking on Sunshine - Katrina & The Waves', 'url': 'https://cdn.pixabay.com/audio/2022/10/09/audio_30e9b4f44b.mp3'},
                    {'title': 'Good Vibrations - Beach Boys', 'url': 'https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3'},
                    {'title': 'Uptown Funk - Bruno Mars', 'url': 'https://cdn.pixabay.com/audio/2021/11/25/audio_91b32e02f9.mp3'}
                ]
            },
            'sad': {
                'keywords': ['sad', 'cry', 'depressed', 'lonely', 'heartbroken', 'down', 'unhappy',
                            'grief', 'sorry', 'miss', 'lost', 'alone', 'hurt', 'pain', 'melancholy',
                            'blue', 'sorrow', 'gloomy', 'tears', 'hopeless', 'broken',
                            'udaas', 'dukhi', 'rona', 'akela', 'tanha', 'dard', 'takleef', 'gham',
                            'baadha', 'dhukham', 'edustunna', 'chala badhaga', 'baadhalo', 'virakti'],
                'emoji': '??',
                'frequency': 417,
                'color': '#4A90D9',
                'energy': 0.2,
                'songs': [
                    {'title': 'Someone Like You - Adele', 'url': 'https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3'},
                    {'title': 'Fix You - Coldplay', 'url': 'https://cdn.pixabay.com/audio/2022/03/15/audio_115bf7b75c.mp3'},
                    {'title': 'Hurt - Johnny Cash', 'url': 'https://cdn.pixabay.com/audio/2022/05/16/audio_dbcb6e8610.mp3'},
                    {'title': 'Yesterday - The Beatles', 'url': 'https://cdn.pixabay.com/audio/2022/08/25/audio_4f3b0a816e.mp3'}
                ]
            },
            'stressed': {
                'keywords': ['stressed', 'anxious', 'overwhelmed', 'worried', 'panic', 'nervous',
                            'frazzled', 'tense', 'pressure', 'deadline', 'busy', 'chaos', 'frustrated',
                            'burnout', 'exhausted', 'tired', 'swamped', 'drowning', 'restless',
                            'tension', 'pareshan', 'chinta', 'thak', 'thakaan', 'mushkil',
                            'alochanalu', 'tension ga', 'kastam', 'bhayam', 'alasata'],
                'emoji': '??',
                'frequency': 639,
                'color': '#FF6B35',
                'energy': 0.3,
                'songs': [
                    {'title': 'Weightless - Marconi Union', 'url': 'https://cdn.pixabay.com/audio/2022/02/22/audio_d1718ab41b.mp3'},
                    {'title': 'Clair de Lune - Debussy', 'url': 'https://cdn.pixabay.com/audio/2021/12/16/audio_4cfc579990.mp3'},
                    {'title': 'Ocean Waves - Nature Sounds', 'url': 'https://cdn.pixabay.com/audio/2022/04/27/audio_67bcce37c3.mp3'},
                    {'title': 'Meditation - Yoga Relax', 'url': 'https://cdn.pixabay.com/audio/2022/09/06/audio_dc39bde3a0.mp3'}
                ]
            },
            'angry': {
                'keywords': ['angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed', 'frustrated',
                            'pissed', 'hate', 'upset', 'fuming', 'livid', 'outraged', 'hostile',
                            'aggressive', 'fierce', 'enraged', 'infuriated', 'temper',
                            'gussa', 'naraz', 'krodh', 'chid', 'jalan', 'nafrat',
                            'kopam', 'asahyam', 'chirakku', 'erripuku'],
                'emoji': '??',
                'frequency': 396,
                'color': '#FF0000',
                'energy': 0.9,
                'songs': [
                    {'title': 'Eye of the Tiger - Survivor', 'url': 'https://cdn.pixabay.com/audio/2022/06/07/audio_b9bd4170a4.mp3'},
                    {'title': 'Lose Yourself - Eminem', 'url': 'https://cdn.pixabay.com/audio/2022/10/18/audio_e4045e2bfa.mp3'},
                    {'title': 'We Will Rock You - Queen', 'url': 'https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3'},
                    {'title': 'Thunder - Imagine Dragons', 'url': 'https://cdn.pixabay.com/audio/2022/10/09/audio_30e9b4f44b.mp3'}
                ]
            },
            'romantic': {
                'keywords': ['romantic', 'love', 'crush', 'heart', 'beautiful', 'passion', 'date',
                            'kiss', 'hug', 'cherish', 'adore', 'sweetheart', 'darling', 'baby',
                            'forever', 'together', 'us', 'we', 'couple', 'dreamy',
                            'pyaar', 'ishq', 'mohabbat', 'dil', 'jaanu', 'jaan',
                            'premam', 'priyatama', 'istam', 'nee kosam', 'manasu'],
                'emoji': '??',
                'frequency': 528,
                'color': '#FF69B4',
                'energy': 0.7,
                'songs': [
                    {'title': 'Perfect - Ed Sheeran', 'url': 'https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3'},
                    {'title': 'All of Me - John Legend', 'url': 'https://cdn.pixabay.com/audio/2021/11/25/audio_91b32e02f9.mp3'},
                    {'title': 'Can\'t Help Falling in Love - Elvis Presley', 'url': 'https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3'},
                    {'title': 'At Last - Etta James', 'url': 'https://cdn.pixabay.com/audio/2022/03/15/audio_115bf7b75c.mp3'}
                ]
            },
            'energetic': {
                'keywords': ['energetic', 'pumped', 'hyped', 'energized', 'ready', 'motivated',
                            'strong', 'power', 'workout', 'gym', 'run', 'dance', 'party', 'wild',
                            'crazy', 'amped', 'charged', 'alive', 'unstoppable', 'radiant'],
                'emoji': '??',
                'frequency': 741,
                'color': '#00FF00',
                'energy': 1.0,
                'songs': [
                    {'title': 'Stronger - Kanye West', 'url': 'https://cdn.pixabay.com/audio/2022/05/16/audio_dbcb6e8610.mp3'},
                    {'title': 'Can\'t Stop - Red Hot Chili Peppers', 'url': 'https://cdn.pixabay.com/audio/2022/08/25/audio_4f3b0a816e.mp3'},
                    {'title': 'Titanium - David Guetta', 'url': 'https://cdn.pixabay.com/audio/2022/02/22/audio_d1718ab41b.mp3'},
                    {'title': 'Levels - Avicii', 'url': 'https://cdn.pixabay.com/audio/2021/12/16/audio_4cfc579990.mp3'}
                ]
            },
            'chill': {
                'keywords': ['chill', 'relaxed', 'calm', 'peaceful', 'serene', 'tranquil', 'mellow',
                            'laid back', 'easy', 'cool', 'zen', 'balanced', 'harmony', 'gentle',
                            'quiet', 'rest', 'nap', 'cozy', 'warm', 'comfortable'],
                'emoji': '??',
                'frequency': 852,
                'color': '#00CED1',
                'energy': 0.3,
                'songs': [
                    {'title': 'Sunset Lover - Petit Biscuit', 'url': 'https://cdn.pixabay.com/audio/2022/04/27/audio_67bcce37c3.mp3'},
                    {'title': 'Weightless - Marconi Union', 'url': 'https://cdn.pixabay.com/audio/2022/09/06/audio_dc39bde3a0.mp3'},
                    {'title': 'Electric Feel - MGMT', 'url': 'https://cdn.pixabay.com/audio/2022/06/07/audio_b9bd4170a4.mp3'},
                    {'title': 'Breathe - Telepopmusik', 'url': 'https://cdn.pixabay.com/audio/2022/10/18/audio_e4045e2bfa.mp3'}
                ]
            },
            'nostalgic': {
                'keywords': ['nostalgic', 'memory', 'remember', 'childhood', 'old days', 'past',
                            'flashback', 'vintage', 'retro', 'classic', 'remember when', 'used to',
                            'grew up', 'miss those days', 'good old', 'history', 'melancholy'],
                'emoji': '??',
                'frequency': 417,
                'color': '#8B4513',
                'energy': 0.4,
                'songs': [
                    {'title': 'Bohemian Rhapsody - Queen', 'url': 'https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3'},
                    {'title': 'Sweet Child O\' Mine - Guns N\' Roses', 'url': 'https://cdn.pixabay.com/audio/2022/10/09/audio_30e9b4f44b.mp3'},
                    {'title': 'Hotel California - Eagles', 'url': 'https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3'},
                    {'title': 'Piano Man - Billy Joel', 'url': 'https://cdn.pixabay.com/audio/2021/11/25/audio_91b32e02f9.mp3'}
                ]
            },
            'confident': {
                'keywords': ['confident', 'boss', 'win', 'success', 'achievement', 'proud', 'powerful',
                            'unstoppable', 'king', 'queen', 'champion', 'best', 'number one', 'winner',
                            'victory', 'dominant', 'savage', 'legend', 'iconic', 'superior'],
                'emoji': '??',
                'frequency': 741,
                'color': '#FF4500',
                'energy': 0.95,
                'songs': [
                    {'title': 'Stronger - Kanye West', 'url': 'https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3'},
                    {'title': 'We Are the Champions - Queen', 'url': 'https://cdn.pixabay.com/audio/2022/03/15/audio_115bf7b75c.mp3'},
                    {'title': 'I Will Always Love You - Whitney Houston', 'url': 'https://cdn.pixabay.com/audio/2022/05/16/audio_dbcb6e8610.mp3'},
                    {'title': 'Hall of Fame - The Script', 'url': 'https://cdn.pixabay.com/audio/2022/08/25/audio_4f3b0a816e.mp3'}
                ]
            },
            'bored': {
                'keywords': ['bored', 'tired', 'nothing', 'lazy', 'dull', 'monotonous', 'same old',
                            'uninterested', 'meh', 'whatever', 'sleepy', 'drowsy', 'blank', 'empty',
                            'stuck', 'waiting', 'killing time', 'routine', 'mundane'],
                'emoji': '??',
                'frequency': 285,
                'color': '#808080',
                'energy': 0.1,
                'songs': [
                    {'title': 'Viva La Vida - Coldplay', 'url': 'https://cdn.pixabay.com/audio/2022/02/22/audio_d1718ab41b.mp3'},
                    {'title': 'Mr. Blue Sky - ELO', 'url': 'https://cdn.pixabay.com/audio/2021/12/16/audio_4cfc579990.mp3'},
                    {'title': 'Shut Up and Dance - Walk the Moon', 'url': 'https://cdn.pixabay.com/audio/2022/04/27/audio_67bcce37c3.mp3'},
                    {'title': 'Adventure of a Lifetime - Coldplay', 'url': 'https://cdn.pixabay.com/audio/2022/09/06/audio_dc39bde3a0.mp3'}
                ]
            }
        }
        self.default_mood = 'happy'
        
    def detect_mood(self, text):
        text_lower = text.lower()
        
        # Negative context overrides - these words force sad/stressed even if positive keywords exist
        sad_overrides = ['reject', 'rejected', 'broke up', 'breakup', 'break up', 'dumped', 'cheated',
                        'died', 'death', 'suicide', 'kill', 'fail', 'failed', 'failure', 'lost her',
                        'lost him', 'left me', 'she left', 'he left', 'crying', 'cried', 'no one',
                        'nobody', 'worthless', 'hopeless', 'give up', 'cant take', 'cant handle',
                        'vadilesi', 'poyyindi', 'dhukham', 'dukh', 'toot', 'toota', 'roya', 'akela']
        
        for neg in sad_overrides:
            if neg in text_lower:
                return 'sad'
        
        scores = {}
        for mood, data in self.mood_keywords.items():
            score = 0
            for kw in data['keywords']:
                if kw in text_lower:
                    score += 1
            # Check for multi-word phrases
            for i, kw in enumerate(data['keywords']):
                if ' ' in kw and kw in text_lower:
                    score += 2
            scores[mood] = score
        
        # Get the mood with highest score
        max_score = max(scores.values())
        if max_score == 0:
            return self.default_mood
        
        # Get all moods with max score
        top_moods = [m for m, s in scores.items() if s == max_score]
        return random.choice(top_moods)
    
    def get_mood_data(self, mood):
        return self.mood_keywords.get(mood, self.mood_keywords[self.default_mood])
    
    def get_response(self, mood, user_message):
        responses = {
            'happy': [
                f"Your energy is absolutely contagious! {random.choice(['??', '??', '??'])}",
                f"I can feel the joy radiating from you! That's beautiful. {random.choice(['??', '??', '??'])}",
                f"You're glowing with happiness and I love that for you! Keep shining!",
                f"Your happiness lights up this whole space! What's making you feel this amazing?",
                f"This is your energy ? vibrant, alive, unstoppable. Savor it!"
            ],
            'sad': [
                f"I hear you, and I'm here with you. It's okay to feel this way. {random.choice(['??', '??', '??'])}",
                f"Those feelings are valid. Take a deep breath ? you're not alone in this.",
                f"Sometimes we just need to sit with our feelings. I'm right here beside you.",
                f"It hurts now, but storms don't last forever. The sun always finds its way back.",
                f"Your feelings matter. Let it out ? I'm listening, really listening."
            ],
            'stressed': [
                f"Take a breath with me. In... and out... You've got this. {random.choice(['??', '??', '??'])}",
                f"Let's press pause together. You don't have to solve everything right now.",
                f"The pressure is real, but so is your strength. One step at a time.",
                f"Close your eyes for a moment. Imagine a calm ocean. You're the stillness above it.",
                f"You're carrying a lot, and you're doing an incredible job. Let's lighten the load."
            ],
            'angry': [
                f"I feel that fire. Let's channel it into something powerful. {random.choice(['??', '??', '??'])}",
                f"Your voice matters. Let that passion fuel something amazing.",
                f"It's okay to be angry. What matters is what we do with that fire.",
                f"That intensity? That's power. Let's aim it, not suppress it.",
                f"Breathe with me. Let the heat pass through you like a wave."
            ],
            'romantic': [
                f"There's something magical in the air tonight... {random.choice(['??', '??', '??'])}",
                f"Love makes everything more beautiful. You're glowing with it.",
                f"Cherish every moment of this feeling ? it's one of life's greatest gifts.",
                f"The universe leans in when hearts speak. Tell me more.",
                f"Romance isn't just a feeling ? it's the poetry we live."
            ],
            'energetic': [
                f"LET'S GO! That energy is ELECTRIC! {random.choice(['??', '??', '??'])}",
                f"I'm matching your energy right now! This is what being alive feels like!",
                f"You're a force of nature! Channel that power into something epic!",
                f"The universe can feel your vibration! Keep riding that wave!",
                f"Energy like yours moves mountains. What are we conquering today?"
            ],
            'chill': [
                f"Everything is flowing. Just vibe with it. {random.choice(['??', '??', '??'])}",
                f"This peaceful energy is everything. Let's stay here a while.",
                f"No rush, no pressure. Just good vibes and good music.",
                f"You've found your center. Hold onto this peace.",
                f"The world slows down when you do. Breathe it in."
            ],
            'nostalgic': [
                f"Those memories shaped you. Honor them. {random.choice(['??', '??', '??'])}",
                f"The past lives in us, making us who we are. That's beautiful.",
                f"Some memories are like old photographs ? faded but precious.",
                f"Looking back isn't going backward. It's gathering the gems.",
                f"The best part? You can create new beautiful memories starting now."
            ],
            'confident': [
                f"THAT'S IT! THAT'S THE ENERGY! YOU'RE UNSTOPPABLE! {random.choice(['??', '??', '??'])}",
                f"Look at you owning it! This is your moment, your world!",
                f"Confidence looks incredible on you! Remember this feeling.",
                f"You weren't built to blend in. You were built to stand out.",
                f"The world is yours for the taking. Go claim what's yours."
            ],
            'bored': [
                f"Let's shake things up! Adventure is calling. {random.choice(['??', '??', '??'])}",
                f"Time to add some color to the canvas! What sounds fun to you?",
                f"Boredom is just the universe nudging you toward something new.",
                f"Let me find you something that'll wake up those neurons!",
                f"Every great story starts with 'I was bored, so...' Let's begin yours."
            ]
        }
        
        mood_responses = responses.get(mood, responses['happy'])
        return random.choice(mood_responses)


mood_ai = MoodAI()

# ============================================================
# AUTH DECORATOR
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# ROUTES
# ============================================================
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/spotify_login')
@login_required
def spotify_login():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    scope = 'streaming user-read-email user-read-private user-modify-playback-state'
    url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={urllib.parse.quote(redirect_uri)}&scope={urllib.parse.quote(scope)}"
    return redirect(url)

@app.route('/spotify_callback')
@login_required
def spotify_callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }

    try:
        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        response.raise_for_status()
        token_info = response.json()
        
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in', 3600)
        expires_at = int(datetime.now().timestamp()) + expires_in

        # Save to DB
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            UPDATE users 
            SET spotify_access_token = ?, spotify_refresh_token = ?, spotify_expires_at = ?
            WHERE id = ?
        """, (access_token, refresh_token, expires_at, session['user_id']))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error getting token: {e}", 400

@app.route('/api/spotify/token')
@login_required
def spotify_token():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Check if spotify columns exist
        c.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in c.fetchall()]
        if 'spotify_access_token' not in cols:
            conn.close()
            return jsonify({'token': None})
        user = c.execute("SELECT spotify_access_token, spotify_expires_at, spotify_refresh_token FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if user and user[0]:
            access_token, expires_at, refresh_token = user
            now_ts = int(datetime.now().timestamp())
            if expires_at and expires_at > now_ts + 60:
                conn.close()
                return jsonify({'token': access_token})
            # Try refresh
            if refresh_token:
                client_id = os.getenv('SPOTIFY_CLIENT_ID')
                client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
                auth_str = f"{client_id}:{client_secret}"
                b64_auth_str = base64.b64encode(auth_str.encode()).decode()
                try:
                    r = requests.post('https://accounts.spotify.com/api/token',
                        headers={'Authorization': f'Basic {b64_auth_str}', 'Content-Type': 'application/x-www-form-urlencoded'},
                        data={'grant_type': 'refresh_token', 'refresh_token': refresh_token})
                    r.raise_for_status()
                    token_info = r.json()
                    new_token = token_info.get('access_token')
                    new_exp = now_ts + token_info.get('expires_in', 3600)
                    c.execute("UPDATE users SET spotify_access_token=?, spotify_expires_at=? WHERE id=?", (new_token, new_exp, session['user_id']))
                    conn.commit()
                    conn.close()
                    return jsonify({'token': new_token})
                except Exception as e:
                    print("Spotify refresh error:", e)
        conn.close()
    except Exception as e:
        print("Spotify token error:", e)
    return jsonify({'token': None})

# ============================================================
# SPOTIFY PLAYLISTS (per language + mood)
# ============================================================
SPOTIFY_LINKS = {
    "en": {
        "happy":"https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC",
        "sad":"https://open.spotify.com/playlist/37i9dQZF1DX7qK8ma5wgG1",
        "stressed":"https://open.spotify.com/playlist/37i9dQZF1DWZd79rJ6a7lp",
        "angry":"https://open.spotify.com/playlist/37i9dQZF1DX4eRPd9frC1m",
        "romantic":"https://open.spotify.com/playlist/37i9dQZF1DX50QitR6t0sD",
        "energetic":"https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP",
        "chill":"https://open.spotify.com/playlist/37i9dQZF1DX4WYpdgoIcn6",
        "nostalgic":"https://open.spotify.com/playlist/37i9dQZF1DX4o1oenSJRJd",
        "confident":"https://open.spotify.com/playlist/37i9dQZF1DX4eRPd9frC1m",
        "bored":"https://open.spotify.com/playlist/37i9dQZF1DX0BcQWzuB7ZO",
    },
    "hi": {
        "happy":"https://open.spotify.com/playlist/37i9dQZF1DXdGk6PmNRhMr",
        "sad":"https://open.spotify.com/playlist/37i9dQZF1DX4Bj3FwJsVkj",
        "stressed":"https://open.spotify.com/playlist/37i9dQZF1DX18jTM2l2fJY",
        "angry":"https://open.spotify.com/playlist/37i9dQZF1DX0XUfTFmNBRM",
        "romantic":"https://open.spotify.com/playlist/37i9dQZF1DX4g8Gs5nUhpp",
        "energetic":"https://open.spotify.com/playlist/37i9dQZF1DX0XUfTFmNBRM",
        "chill":"https://open.spotify.com/playlist/37i9dQZF1DX18jTM2l2fJY",
        "nostalgic":"https://open.spotify.com/playlist/37i9dQZF1DWTtTyjgSLWpl",
        "confident":"https://open.spotify.com/playlist/37i9dQZF1DX0XUfTFmNBRM",
        "bored":"https://open.spotify.com/playlist/37i9dQZF1DXdGk6PmNRhMr",
    },
    "te": {
        "happy":"https://open.spotify.com/playlist/37i9dQZF1DX6XE7HRLM75P",
        "sad":"https://open.spotify.com/playlist/37i9dQZF1DX0Tkc6ltcBfU",
        "stressed":"https://open.spotify.com/playlist/37i9dQZF1DX0Tkc6ltcBfU",
        "angry":"https://open.spotify.com/playlist/37i9dQZF1DX6XE7HRLM75P",
        "romantic":"https://open.spotify.com/playlist/37i9dQZF1DWVEerxa93vDL",
        "energetic":"https://open.spotify.com/playlist/37i9dQZF1DX6XE7HRLM75P",
        "chill":"https://open.spotify.com/playlist/37i9dQZF1DX0Tkc6ltcBfU",
        "nostalgic":"https://open.spotify.com/playlist/37i9dQZF1DWVEerxa93vDL",
        "confident":"https://open.spotify.com/playlist/37i9dQZF1DX6XE7HRLM75P",
        "bored":"https://open.spotify.com/playlist/37i9dQZF1DX6XE7HRLM75P",
    }
}

# ============================================================
# SPOTIFY TRACK SEARCH (with caching)
# ============================================================
_spotify_track_cache = {}
_spotify_client_token = {"token": None, "expires": 0}

def get_spotify_client_token():
    """Get a Spotify client credentials token (no user auth needed)"""
    import time, base64
    now = time.time()
    if _spotify_client_token["token"] and _spotify_client_token["expires"] > now:
        return _spotify_client_token["token"]
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID', '')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        return None
    
    try:
        auth_str = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post("https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth_str}"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            _spotify_client_token["token"] = data["access_token"]
            _spotify_client_token["expires"] = now + data.get("expires_in", 3600) - 60
            return data["access_token"]
    except Exception as e:
        print(f"Spotify client token error: {e}")
    return None

def search_spotify_track(title):
    """Search Spotify for a track and return its ID"""
    if title in _spotify_track_cache:
        return _spotify_track_cache[title]
    
    token = get_spotify_client_token()
    if not token:
        return ""
    
    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/search",
            params={"q": title, "type": "track", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("tracks", {}).get("items"):
                track_id = data["tracks"]["items"][0]["id"]
                _spotify_track_cache[title] = track_id
                return track_id
    except Exception as e:
        print(f"Spotify search error for '{title}': {e}")
    
    return ""

# ============================================================
# API ENDPOINTS
# ============================================================
@app.route('/api/mood', methods=['POST'])
@login_required
def analyze_mood():
    data = request.get_json()
    message = data.get('message', '')
    lang = data.get('lang', 'en')
    
    mood = mood_ai.detect_mood(message)
    mood_data = mood_ai.get_mood_data(mood)
    
    # Try LLM first
    llm_msg = get_llm_response(message, mood, lang, session['user_id'])
    if llm_msg:
        response_text = llm_msg
    else:
        response_text = mood_ai.get_response(mood, message)
    # Load the full song library from songs_db.py
    LANG_SONGS = ALL_LANG_SONGS

    # Smart no-repeat shuffle — tracks seen songs per session per mood+lang
    lang_key = lang if lang in LANG_SONGS else "en"
    mood_songs = LANG_SONGS[lang_key].get(mood, LANG_SONGS[lang_key].get("happy", []))
    if mood_songs:
        seen_key = f"seen_{lang_key}_{mood}"
        seen = set(session.get(seen_key, []))
        # Filter out already-seen songs; reset if all played
        unseen = [s for s in mood_songs if s["sp"] not in seen]
        if not unseen:
            seen = set()
            unseen = list(mood_songs)
        picked = random.choice(unseen)
        seen.add(picked["sp"])
        session[seen_key] = list(seen)
        session.modified = True
        song = {"title": picked["title"], "sp": picked["sp"]}
    else:
        song = {"title": "Chill Vibes", "sp": "3hRV0jL3vUpRrcy398teAU"}
    
    # Get language-specific Spotify link
    lang_links = SPOTIFY_LINKS.get(lang, SPOTIFY_LINKS["en"])
    spotify_link = lang_links.get(mood, lang_links.get("happy", ""))
    lang_labels = {"en": "English", "hi": "Bollywood Hindi", "te": "Tollywood Telugu"}
    
    # Save to history
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO mood_history (user_id, mood, message, song) VALUES (?, ?, ?, ?)",
              (session['user_id'], mood, message, song['title']))
    conn.commit()
    conn.close()
    
    return jsonify({
        'mood': mood,
        'emoji': mood_data['emoji'],
        'color': mood_data['color'],
        'frequency': mood_data['frequency'],
        'energy': mood_data['energy'],
        'response': response_text,
        'song': song,
        'spotify_link': spotify_link,
        'spotify_label': lang_labels.get(lang, "English"),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT mood, message, song, timestamp FROM mood_history WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
              (session['user_id'],))
    history = [{'mood': row[0], 'message': row[1], 'song': row[2], 'timestamp': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(history)

@app.route('/api/change-song', methods=['POST'])
@login_required
def change_song():
    """Lightweight endpoint that returns only a new song without LLM call"""
    data = request.get_json()
    mood = data.get('mood', 'happy')
    lang = data.get('lang', 'en')
    LANG_SONGS = ALL_LANG_SONGS
    lang_key = lang if lang in LANG_SONGS else "en"
    mood_songs = LANG_SONGS[lang_key].get(mood, LANG_SONGS[lang_key].get("happy", []))
    if mood_songs:
        seen_key = f"seen_{lang_key}_{mood}"
        seen = set(session.get(seen_key, []))
        # Also exclude the current song passed from frontend if any
        current_sp = data.get('current_sp', '')
        if current_sp:
            seen.add(current_sp)
        unseen = [s for s in mood_songs if s["sp"] not in seen]
        if not unseen:
            seen = set()
            unseen = list(mood_songs)
        picked = random.choice(unseen)
        seen.add(picked["sp"])
        session[seen_key] = list(seen)
        session.modified = True
        return jsonify({'song': {'title': picked['title'], 'sp': picked['sp']}})
    return jsonify({'song': {'title': 'Chill Vibes', 'sp': '3hRV0jL3vUpRrcy398teAU'}})

@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM mood_history WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({
        'username': session.get('username'),
        'user_id': session.get('user_id')
    })

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("""
    ????????????????????????????????????????????????????????????????????????
    ?     ?? AMIS - AI Mood Intelligence System    ?
    ?     Advanced 3D + Voice + Music Chatbot      ?
    ????????????????????????????????????????????????????????????????????????
    """)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
