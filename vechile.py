import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

@app.route('/estimate', methods=['POST'])
def estimate():
    # 1. API Key-ஐ எடுக்கும் முயற்சி
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API Key not found in Render settings!"}), 500
    
    # 2. Gemini Client உருவாக்கம்
    client = genai.Client(api_key=api_key)
    
    # 3. AI-யிடம் கேள்வி கேட்டல்
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash', # இதை 1.5-க்கு மாற்றியுள்ளேன்
            contents="Return a JSON object for a vehicle valued at 3 lakhs."
        )
        return response.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
