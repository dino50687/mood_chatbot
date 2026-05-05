import re

with open("app_advanced.py", "r") as f:
    content = f.read()

llm_code = """
from dotenv import load_dotenv
load_dotenv()

def get_llm_response(user_input, mood, lang='en', user_id=None):
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    lang_name = "casual English (like a close friend texting)"
    if lang == "hi": 
        lang_name = "Hinglish (conversational Hindi mixed with English, casual and friendly)"
    elif lang == "te": 
        lang_name = "Tenglish (conversational Telugu mixed with English, casual and friendly)"

    history_text = ""
    if user_id:
        try:
            import sqlite3
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            history = c.execute("SELECT message, mood FROM mood_history WHERE user_id=? ORDER BY id DESC LIMIT 4", (user_id,)).fetchall()
            conn.close()
            history_text = "\\n".join([f"User: {row[0]}\\nAMIS: {row[1]}" for row in reversed(history)])
            if history_text:
                history_text = f"Recent chat history:\\n{history_text}\\n"
        except Exception as e:
            print("History error:", e)

    prompt = f"You are AMIS, an AI Mood Intelligence System. You are a highly empathetic, natural-sounding, warm friend.\\n{history_text}The user just said: '{user_input}'. Their detected mood is '{mood}'. Respond in a short, supportive manner (1-2 sentences max) taking into account their recent history if any. You must respond in {lang_name}. Do NOT use any markdown or special formatting. Use emojis naturally. Just raw text."

    payload = {
        "model": "meta/llama-3.1-70b-instruct",
        "messages": [{"role":"user","content":prompt}],
        "max_tokens": 150,
        "temperature": 0.5,
        "top_p": 0.7,
        "stream": False
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("LLM Error:", e)
        return None
"""

content = content.replace("from functools import wraps", "from functools import wraps\n" + llm_code)

content = content.replace("return render_template('index.html')", "return render_template('index_3d.html')")

# Replace `/api/mood` logic
api_mood_replacement = """
    mood = mood_ai.detect_mood(message)
    mood_data = mood_ai.get_mood_data(mood)
    
    # Try LLM first
    llm_msg = get_llm_response(message, mood, 'en', session['user_id'])
    if llm_msg:
        response_text = llm_msg
    else:
        response_text = mood_ai.get_response(mood, message)
        
    song = random.choice(mood_data['songs'])
"""
content = re.sub(r"    mood = mood_ai\.detect_mood\(message\)\n    mood_data = mood_ai\.get_mood_data\(mood\)\n    response_text = mood_ai\.get_response\(mood, message\)\n    song = random\.choice\(mood_data\['songs'\]\)", api_mood_replacement.strip('\n'), content)

with open("app.py", "w") as f:
    f.write(content)
