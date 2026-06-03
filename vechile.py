import os
import json
import time
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image

app = Flask(__name__)
CORS(app)

# API Key setup
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client()

# Catch-all route to fix "Not Found" error
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate_with_ai():
    vehicle = request.form.get('vehicle', '').strip()
    km = request.form.get('km', '').strip()
    condition = request.form.get('condition', 'Good').strip()
    fuel_type = request.form.get('fuel_type', 'Petrol').strip()
    owners = request.form.get('owners', '1st Owner').strip()
    lang = request.form.get('lang', 'ta').strip()
    photo_file = request.files.get('photo')
    
    if not vehicle or not km:
        return jsonify({"error": "Details required"}), 400

    contents_list = []
    if photo_file:
        try:
            img = Image.open(io.BytesIO(photo_file.read()))
            contents_list.append(img)
        except: pass

    prompt = f"""
    You are an expert vehicle valuation analyst. Analyze: {vehicle}, {km}km, {condition}, {fuel_type}, {owners}.
    Return ONLY pure JSON. No markdown, no code blocks, no intro text.
    {{
        "vehicle_name": "{vehicle}",
        "kilometers": "{km}",
        "condition": "{condition}",
        "fuel_type": "{fuel_type}",
        "owners": "{owners}",
        "new_price": 0,
        "estimated_price": 0,
        "depreciation_percent": 0,
        "ai_advice": "Analyzed successfully."
    }}
    """
    contents_list.append(prompt)

    for attempt in range(3):
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=contents_list)
            text = response.text.replace("```json", "").replace("```", "").strip()
            
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                text = text[start:end]
            
            return jsonify(json.loads(text))
        except:
            time.sleep(2)
            continue
            
    return jsonify({"error": "Calculation error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
