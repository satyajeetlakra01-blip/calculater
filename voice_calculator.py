from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import webbrowser
import threading
import os

app = Flask(__name__)

# Ollama Local OpenAI-compatible Client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)
SELECTED_MODEL = "qwen2.5:3b"

# Global AI Engine State
ai_enabled = True

def clean_for_speech(text):
    text = text.replace('\\frac', ' fraction ')
    text = text.replace('{', ' ').replace('}', ' ')
    text = text.replace('^', ' to the power of ')
    text = text.replace('*', ' times ').replace('/', ' divided by ')
    text = text.replace('=', ' equals ').replace('\\', ' ')
    return " ".join(text.split())

def open_browser():
    """Automatically opens the default web browser to the application URL."""
    webbrowser.open("http://127.0.0.1:5000/")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def get_status():
    """Health & AI Engine state endpoint."""
    return jsonify({
        "status": "online",
        "ai_enabled": ai_enabled,
        "model": SELECTED_MODEL
    })

@app.route('/toggle_ai', methods=['POST'])
def toggle_ai():
    """Endpoint to Start or Stop the AI engine remotely."""
    global ai_enabled
    data = request.json or {}
    if 'enabled' in data:
        ai_enabled = bool(data['enabled'])
    else:
        ai_enabled = not ai_enabled
    return jsonify({"ai_enabled": ai_enabled, "message": f"AI Engine is now {'ENABLED' if ai_enabled else 'STOPPED'}"})

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json or {}
    user_question = data.get('question', '')
    
    # Read settings sent from the website interface
    ai_temp = float(data.get('temperature', 0.001))
    ai_tokens = int(data.get('max_tokens', 800))
    request_ai_enabled = data.get('ai_enabled', ai_enabled)

    # If AI is stopped by user
    if not request_ai_enabled or not ai_enabled:
        return jsonify({
            "answer": f"AI Engine is currently STOPPED. Enable AI in settings for full reasoning.",
            "raw": "AI Engine Paused",
            "ai_active": False
        })

    try:
        response = client.chat.completions.create(
            model=SELECTED_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a voice-only calculator. "
                        "1. DO NOT use LaTeX, special symbols, or formatting tags. "
                        "2. Write out equations in plain English words. "
                        "3. Keep answers concise and direct."
                    )
                },
                {"role": "user", "content": user_question}
            ],
            temperature=ai_temp,
            max_tokens=ai_tokens
        )
        raw_answer = response.choices[0].message.content.strip()
        final_answer = clean_for_speech(raw_answer)
        
        return jsonify({"answer": final_answer, "raw": raw_answer, "ai_active": True})
        
    except Exception as e:
        return jsonify({
            "answer": "Error connecting to local Ollama AI server. Using client fallback.",
            "raw": str(e),
            "ai_active": False
        })

if __name__ == '__main__':
    # Automatically launch web browser after 1.25 seconds when server starts
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.25, open_browser).start()
    
    print("\n" + "="*60)
    print("🚀 3D Voice AI Calculator Server Starting on http://127.0.0.1:5000/")
    print("🤖 Ollama Backend Model:", SELECTED_MODEL)
    print("🌐 Automatically launching web browser...")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)