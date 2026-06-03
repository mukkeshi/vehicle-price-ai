import os
import json
from flask import Flask, request, jsonify, send_from_directory
from google import genai

app = Flask(__name__)
# API key-வை இங்கிருந்து எடுத்துக்கொள்ளும்
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate():
    try:
        # வாகன விவரங்களை பெறுதல்
        v = request.form.get('vehicle', 'Car')
        km = request.form.get('km', '0')
        
        # மாடல் பெயரை 'gemini-2.0-flash' என மாற்றியுள்ளேன்
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=f"Analyze {v} with {km} km. Return JSON: vehicle_name, kilometers, condition, fuel_type, owners, new_price, estimated_price, depreciation_percent, ai_advice."
        )
        
        # JSON-ஐ மட்டும் பிரித்தெடுத்தல்
        text = response.text.replace('```json', '').replace('```', '').strip()
        return jsonify(json.loads(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
