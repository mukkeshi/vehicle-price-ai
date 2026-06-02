import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# ரகசிய கீ இங்கே நேரடியாக இருக்கக் கூடாது, Render-ல் இருந்து தானாக எடுத்துக்கொள்ளும்
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "default_key_if_needed")

try:
    client = genai.Client()
except Exception as e:
    print("Gemini Client Error:", e)

# வெப்சைட்டை நேரடியாக சர்வர் வழியே திறப்பதற்கான ரூட் (Root Route)
@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate_with_ai():
    data = request.get_json()
    vehicle = data.get('vehicle', '').strip()
    km = data.get('km', '').strip()
    
    if not vehicle or not km:
        return jsonify({"error": "விவரங்கள் தேவை!"}), 400

    prompt = f"""
    You are an expert vehicle valuation backend. 
    Analyze the following vehicle and provide two prices in Indian Rupees (INR):
    1. The current brand new on-road price of this vehicle model in India today.
    2. The estimated resale market price for this used vehicle based on the kilometers driven.
    
    Vehicle Name: {vehicle}
    Kilometers Driven: {km} km
    
    Return the response strictly as a JSON object with these exact keys, and no extra text or markdown:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "new_price": "only the brand new on-road integer price here",
        "estimated_price": "only the calculated used resale integer price here"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_response_text = response.text.strip()
        
        # எரர் வராமல் இருக்க கோடு ஒரே வரியாக மாற்றப்பட்டுள்ளது
        ai_response_text = ai_response_text.replace("```json", "").replace("```", "").replace("**", "").strip()
        
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
    except Exception as e:
        print("API Error:", e)
        return jsonify({"error": "ஆன்லைனில் கணக்கிடுவதில் பிழை ஏற்பட்டது."}), 500

# Render சர்வர் தானாகவே போர்ட் எடுப்பதற்காக இந்த பகுதி மாற்றப்பட்டுள்ளது
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)