import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# Environment Variable-il irundhu API Key edukkapadugiradhu
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
    lang = data.get('lang', 'en').strip() # User therndhedukum mozhi (en / ta)
    
    if not vehicle or not km:
        return jsonify({"error": "Details are required!" if lang == 'en' else "விவரங்கள் தேவை!"}), 400

    # Mozhiyai poruthu advice ketkum logic
    advice_instruction = (
        "A short, expert 2-sentence market advice in English explaining if this is a good deal considering the fuel type, owners count, and condition, and mention what specific parts to check."
        if lang == 'en' else
        "A short, expert 2-sentence market advice in Tamil explaining if this is a good deal considering the fuel type, owners count, and condition, and mention what specific parts to check."
    )

    prompt = f"""
    You are an expert Indian vehicle valuation and automobile market analyst. 
    Analyze the following vehicle and provide structured data in Indian Rupees (INR):
    
    Vehicle Name: {vehicle}
    Kilometers Driven: {km} km
    Current Condition: {condition}
    Fuel Type: {fuel_type}
    Number of Owners: {owners}
    
    Take into account that EV resale value drop differs from Petrol/Diesel, and higher number of owners significantly reduces the used car market value in India.
    
    Return the response strictly as a JSON object with these exact keys, and no extra text or markdown:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "condition": "{condition}",
        "fuel_type": "{fuel_type}",
        "owners": "{owners}",
        "new_price": "only the brand new on-road integer price here based on current Indian market",
        "estimated_price": "only the calculated used resale integer price here based on market trends, condition, and owners",
        "depreciation_percent": "only the calculated integer value of price drop percentage from new price",
        "ai_advice": "{advice_instruction}"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_response_text = response.text.strip()
        ai_response_text = ai_response_text.replace("```json", "").replace("```", "").replace("**", "").strip()
        
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
    except Exception as e:
        print("API Error:", e)
        error_msg = "Error calculating online." if lang == 'en' else "ஆன்லைனில் கணக்கிடுவதில் பிழை ஏற்பட்டது."
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
