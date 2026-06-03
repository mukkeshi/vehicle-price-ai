import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

try:
    client = genai.Client()
except Exception as e:
    print("Gemini Client Error:", e)

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate_with_ai():
    data = request.get_json()
    vehicle = data.get('vehicle', '').strip()
    km = data.get('km', '').strip()
    condition = data.get('condition', 'Good').strip()
    fuel_type = data.get('fuel_type', 'Petrol').strip()
    owners = data.get('owners', '1st Owner').strip()
    lang = data.get('lang', 'en').strip()
    
    prompt = f"""
    You are an expert Indian vehicle valuation analyst. 
    Vehicle: {vehicle}, KM: {km}, Condition: {condition}, Fuel: {fuel_type}, Owners: {owners}.
    Return strictly as JSON:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "condition": "{condition}",
        "fuel_type": "{fuel_type}",
        "owners": "{owners}",
        "new_price": "integer price",
        "estimated_price": "integer price",
        "depreciation_percent": "integer percentage",
        "ai_advice": "2 sentence expert advice in {lang}."
    }}
    """
    try:
        response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        ai_text = response.text.replace("```json", "").replace("```", "").replace("**", "").strip()
        return jsonify(json.loads(ai_text))
    except Exception as e:
        return jsonify({"error": "Calculation error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
