import os
import re
import json
import hashlib
import sqlite3
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps

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
                            'thrilled', 'blessed', 'grateful', 'smile', 'laugh', 'fun', 'party', 'sunshine'],
                'emoji': '??',
                'frequency': 528,
                'color': '#FFD700',
                'energy': 0.9,
                'songs': [
                    {'title': 'Happy - Pharrell Williams', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'},
                    {'title': 'Walking on Sunshine - Katrina & The Waves', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3'},
                    {'title': 'Good Vibrations - Beach Boys', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3'},
                    {'title': 'Uptown Funk - Bruno Mars', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3'}
                ]
            },
            'sad': {
                'keywords': ['sad', 'cry', 'depressed', 'lonely', 'heartbroken', 'down', 'unhappy',
                            'grief', 'sorry', 'miss', 'lost', 'alone', 'hurt', 'pain', 'melancholy',
                            'blue', 'sorrow', 'gloomy', 'tears', 'hopeless', 'broken'],
                'emoji': '??',
                'frequency': 417,
                'color': '#4A90D9',
                'energy': 0.2,
                'songs': [
                    {'title': 'Someone Like You - Adele', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3'},
                    {'title': 'Fix You - Coldplay', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3'},
                    {'title': 'Hurt - Johnny Cash', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3'},
                    {'title': 'Yesterday - The Beatles', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3'}
                ]
            },
            'stressed': {
                'keywords': ['stressed', 'anxious', 'overwhelmed', 'worried', 'panic', 'nervous',
                            'frazzled', 'tense', 'pressure', 'deadline', 'busy', 'chaos', 'frustrated',
                            'burnout', 'exhausted', 'tired', 'swamped', 'drowning', 'restless'],
                'emoji': '??',
                'frequency': 639,
                'color': '#FF6B35',
                'energy': 0.3,
                'songs': [
                    {'title': 'Weightless - Marconi Union', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3'},
                    {'title': 'Clair de Lune - Debussy', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3'},
                    {'title': 'Ocean Waves - Nature Sounds', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3'},
                    {'title': 'Meditation - Yoga Relax', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3'}
                ]
            },
            'angry': {
                'keywords': ['angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed', 'frustrated',
                            'pissed', 'hate', 'upset', 'fuming', 'livid', 'outraged', 'hostile',
                            'aggressive', 'fierce', 'enraged', 'infuriated', 'temper'],
                'emoji': '??',
                'frequency': 396,
                'color': '#FF0000',
                'energy': 0.9,
                'songs': [
                    {'title': 'Eye of the Tiger - Survivor', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3'},
                    {'title': 'Lose Yourself - Eminem', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3'},
                    {'title': 'We Will Rock You - Queen', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'},
                    {'title': 'Thunder - Imagine Dragons', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3'}
                ]
            },
            'romantic': {
                'keywords': ['romantic', 'love', 'crush', 'heart', 'beautiful', 'passion', 'date',
                            'kiss', 'hug', 'cherish', 'adore', 'sweetheart', 'darling', 'baby',
                            'forever', 'together', 'us', 'we', 'couple', 'dreamy'],
                'emoji': '??',
                'frequency': 528,
                'color': '#FF69B4',
                'energy': 0.7,
                'songs': [
                    {'title': 'Perfect - Ed Sheeran', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3'},
                    {'title': 'All of Me - John Legend', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3'},
                    {'title': 'Can\'t Help Falling in Love - Elvis Presley', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3'},
                    {'title': 'At Last - Etta James', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3'}
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
                    {'title': 'Stronger - Kanye West', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3'},
                    {'title': 'Can\'t Stop - Red Hot Chili Peppers', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3'},
                    {'title': 'Titanium - David Guetta', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3'},
                    {'title': 'Levels - Avicii', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3'}
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
                    {'title': 'Sunset Lover - Petit Biscuit', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3'},
                    {'title': 'Weightless - Marconi Union', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3'},
                    {'title': 'Electric Feel - MGMT', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3'},
                    {'title': 'Breathe - Telepopmusik', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3'}
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
                    {'title': 'Bohemian Rhapsody - Queen', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'},
                    {'title': 'Sweet Child O\' Mine - Guns N\' Roses', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3'},
                    {'title': 'Hotel California - Eagles', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3'},
                    {'title': 'Piano Man - Billy Joel', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3'}
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
                    {'title': 'Stronger - Kanye West', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3'},
                    {'title': 'We Are the Champions - Queen', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3'},
                    {'title': 'I Will Always Love You - Whitney Houston', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3'},
                    {'title': 'Hall of Fame - The Script', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3'}
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
                    {'title': 'Viva La Vida - Coldplay', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3'},
                    {'title': 'Mr. Blue Sky - ELO', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3'},
                    {'title': 'Shut Up and Dance - Walk the Moon', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3'},
                    {'title': 'Adventure of a Lifetime - Coldplay', 'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3'}
                ]
            }
        }
        self.default_mood = 'happy'
        
    def detect_mood(self, text):
        text_lower = text.lower()
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
    return render_template('index.html')

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

# ============================================================
# API ENDPOINTS
# ============================================================
@app.route('/api/mood', methods=['POST'])
@login_required
def analyze_mood():
    data = request.get_json()
    message = data.get('message', '')
    
    mood = mood_ai.detect_mood(message)
    mood_data = mood_ai.get_mood_data(mood)
    response_text = mood_ai.get_response(mood, message)
    song = random.choice(mood_data['songs'])
    
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

@app.route('/api/mood-debug', methods=['POST'])
def analyze_mood_debug():
    """Debug endpoint for testing mood API without authentication"""
    data = request.get_json()
    message = data.get('message', '')
    
    mood = mood_ai.detect_mood(message)
    mood_data = mood_ai.get_mood_data(mood)
    response_text = mood_ai.get_response(mood, message)
    song = random.choice(mood_data['songs'])
    
    return jsonify({
        'mood': mood,
        'emoji': mood_data['emoji'],
        'color': mood_data['color'],
        'frequency': mood_data['frequency'],
        'energy': mood_data['energy'],
        'response': response_text,
        'song': song,
        'timestamp': datetime.now().isoformat(),
        'debug': True
    })

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
    app.run(debug=True, host='0.0.0.0', port=5002)
