import os
import json
import io
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image

app = Flask(__name__)
CORS(app)

# 1. கீகளை மேனேஜ் செய்யும் பகுதி
keys_string = os.environ.get("API_KEYS", "")
if not keys_string:
    keys_string = os.environ.get("GEMINI_API_KEY", "")

API_KEYS = keys_string.split(",") if keys_string else []

def get_client():
    # லிஸ்ட்டில் இருந்து ஒரு கீயை ரேண்டமாகத் தேர்வு செய்யும்
    selected_key = random.choice(API_KEYS) if API_KEYS else None
    return genai.Client(api_key=selected_key)

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate_with_ai():
    # இப்போது ஒவ்வொரு முறை அழைக்கும்போதும் புது client உருவாக்கப்படும் (Key rotation)
    client = get_client()
    
    vehicle = request.form.get('vehicle', '').strip()
    km = request.form.get('km', '').strip()
    condition = request.form.get('condition', 'Good').strip()
    fuel_type = request.form.get('fuel_type', 'Petrol').strip()
    owners = request.form.get('owners', '1st Owner').strip()
    lang = request.form.get('lang', 'ta').strip()
    
    photo_file = request.files.get('photo')
    
    if not vehicle or not km:
        error_text = "விவரங்கள் தேவை!" if lang == 'ta' else "Details are required!"
        return jsonify({"error": error_text}), 400

    contents_list = []

    if photo_file:
        try:
            image_bytes = photo_file.read()
            img = Image.open(io.BytesIO(image_bytes))
            contents_list.append(img)
        except Exception as e:
            print("Image Load Error:", e)

    advice_prompt = (
        "CRITICAL IMAGE VALIDATION: If the uploaded image is NOT a vehicle, set 'estimated_price' to 0 and 'ai_advice' to 'தயவுசெய்து சரியான வாகனத்தின் புகைப்படத்தை பதிவேற்றவும்!'"
        if lang == 'ta' else
        "CRITICAL IMAGE VALIDATION: If the uploaded image is NOT a vehicle, set 'estimated_price' to 0 and 'ai_advice' to 'Please upload a valid vehicle image!'"
    )

    prompt = f"""
    Vehicle: {vehicle}, KM: {km}, Condition: {condition}, Fuel: {fuel_type}, Owners: {owners}.
    Return strictly as JSON:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "new_price": "integer price",
        "estimated_price": "integer price",
        "depreciation_percent": "integer",
        "ai_advice": "{advice_prompt}"
    }}
    """
    contents_list.append(prompt)

    try:
        # மாடலை 1.5-flash என மாற்றியுள்ளேன் (இதுவே நிலையானது)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=contents_list,
        )
        ai_response_text = response.text.replace("```json", "").replace("```", "").replace("**", "").strip()
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
    except Exception as e:
        print("API Error:", e)
        return jsonify({"error": "Error during calculation"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
