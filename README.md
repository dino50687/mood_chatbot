# 🌌 AMIS — AI Mood Intelligence System

An advanced AI-powered chatbot that analyzes your mood and provides personalized music recommendations, wellness insights, and emotional support powered by cosmic frequencies and quantum insights.

## ✨ Features

### 🧠 Advanced Mood Analysis
- **NLP-based Mood Detection** - Analyzes conversations using natural language processing
- **Cosmic Frequency Mapping** - Associates moods with healing frequencies (528Hz, 741Hz, etc.)
- **Quantum State Analysis** - Predicts mood states using quantum superposition concepts
- **Astrological Influences** - Considers zodiac signs for personalized insights

### 🎵 Music Integration
- **Spotify Integration** - Curated music recommendations based on detected mood
- **Frequency-Based Playlists** - AI-generated playlists matching cosmic frequencies

### 🛡️ User Management
- **Secure Authentication** - User login and registration system
- **Session Management** - Persistent user sessions with encrypted passwords
- **User Dashboard** - View mood history and personal wellness metrics

### 📊 Analytics & Tracking
- **Mood History** - Track mood patterns over time
- **Wellness Dashboard** - Visual charts and insights
- **Emotional Patterns** - Identify trends in your emotional state

### 🌟 Wellness Features
- **Meditation Recommendations** - Mindfulness suggestions based on mood
- **Wellness Tips** - Personalized health and lifestyle advice
- **Emotional Support** - Empathetic AI conversations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Modern web browser

### Installation

1. **Clone or navigate to the project**
```bash
cd "/Users/karthik/Desktop/AI project/mood_chatbot"
```

2. **Install dependencies**
```bash
pip install flask nltk numpy requests
```

3. **Initialize the database**
```bash
python app.py
```

4. **Run the application**
```bash
python app.py
```

5. **Access the app**
Open your browser and go to:
```
http://localhost:5001
```

## 📁 Project Structure

```
mood_chatbot/
├── app.py                      # Main Flask application & AI engine
├── templates/
│   └── index.html             # Frontend UI & Dashboard
├── static/
│   └── style.css              # Styling & animations
├── database.db                # User data & mood history
└── README.md                  # This file
```

## 🔧 Usage

### Getting Started
1. **Create an Account** - Sign up with username and password
2. **Chat with AMIS** - Share how you're feeling
3. **Get Recommendations** - Receive music, meditation, or wellness tips
4. **Track Progress** - View your mood dashboard and emotional patterns

### Mood Categories Supported
- 😊 Happy
- 😢 Sad
- 😰 Stressed
- 😠 Angry
- 😍 Romantic
- ⚡ Energetic
- 😌 Chill
- 🎭 Nostalgic
- 💪 Confident
- 😑 Bored

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main dashboard |
| `/api/mood` | POST | Submit mood & get recommendations |
| `/api/history` | GET | Retrieve mood history |
| `/api/recommendations` | GET | Get personalized suggestions |
| `/login` | POST | User authentication |
| `/register` | POST | Create new account |

## 🔐 Security Features

- Passwords stored with SHA-256 hashing
- Session-based authentication
- SQLite database with encrypted sensitive data
- CSRF protection on forms

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **NLP**: NLTK (Natural Language Toolkit)
- **Database**: SQLite
- **Visualization**: Chart.js
- **APIs**: Spotify Web API

## 📝 Configuration

### Mood Detection Thresholds
Adjust sensitivity in `app.py`:
```python
self.confidence_threshold = 0.75  # 0-1 scale
```

### Cosmic Frequencies
Customize frequency mappings:
```python
self.cosmic_frequencies = {
    'happy': 528,      # Love frequency
    'sad': 417,        # Undoing situations
    # ... more mappings
}
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in app.py or kill existing process
lsof -i :5000
kill -9 <PID>
```

### NLTK Data Missing
```bash
python -m nltk.downloader punkt stopwords
```

### Database Errors
```bash
# Reset database
rm database.db
python app.py
```

## 🚀 Future Enhancements

- [ ] Voice input/output support
- [ ] Integration with Fitbit/Apple Health
- [ ] Multi-language support
- [ ] Real-time collaborative mood sessions
- [ ] Advanced ML mood prediction models
- [ ] Mobile app (iOS/Android)
- [ ] Social mood sharing & community features

## 📄 License

This project is open source. Feel free to use and modify for personal or educational purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📧 Support

For issues or questions, please open an issue in the repository.

---

**Made with 🌌 and ❤️ for emotional wellness through AI**
