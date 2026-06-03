import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# உங்கள் Gemini API Key Render Environment-ல் இருந்து பாதுகாப்பாக எடுக்கப்படுகிறது
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
    
    if not vehicle or not km:
        return jsonify({"error": "விவரங்கள் தேவை!"}), 400

    # Prompt-ல் Condition மற்றும் Extra Features சேர்க்கப்பட்டுள்ளது
    prompt = f"""
    You are an expert vehicle valuation and automobile backend advisor. 
    Analyze the following vehicle and provide structured data in Indian Rupees (INR):
    
    Vehicle Name: {vehicle}
    Kilometers Driven: {km} km
    Current Condition: {condition}
    
    Return the response strictly as a JSON object with these exact keys, and no extra text or markdown:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "condition": "{condition}",
        "new_price": "only the brand new on-road integer price here",
        "estimated_price": "only the calculated used resale integer price here",
        "depreciation_percent": "only the calculated integer value of price drop percentage from new price",
        "ai_advice": "A short, expert 2-sentence advice in Tamil explaining if this is a good deal based on the condition and KM, and what maintenance to look for."
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_response_text = response.text.strip()
        
        ai_response_text = ai_response_text.replace("```json", "").replace("
```", "").replace("**", "").strip()
        
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
    except Exception as e:
        print("API Error:", e)
        return jsonify({"error": "ஆன்லைனில் கணக்கிடுவதில் பிழை ஏற்பட்டது."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
