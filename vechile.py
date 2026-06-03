import os
import json
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image # போட்டோக்களை பிராசஸ் செய்ய Pillow இம்போர்ட் செய்கிறோம்

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
    # போட்டோ வருவதால் request.form மூலமாக டேட்டாவை எடுக்க வேண்டும்
    vehicle = request.form.get('vehicle', '').strip()
    km = request.form.get('km', '').strip()
    condition = request.form.get('condition', 'Good').strip()
    fuel_type = request.form.get('fuel_type', 'Petrol').strip()
    owners = request.form.get('owners', '1st Owner').strip()
    lang = request.form.get('lang', 'ta').strip()
    
    # போட்டோ ஃபைலை எடுக்கிறோம்
    photo_file = request.files.get('photo')
    
    if not vehicle or not km:
        error_text = "விவரங்கள் தேவை!" if lang == 'ta' else "Details are required!"
        return jsonify({"error": error_text}), 400

    # ஜெமினிக்கு அனுப்பும் கன்டென்ட் லிஸ்ட்
    contents_list = []

    if photo_file:
        try:
            image_bytes = photo_file.read()
            img = Image.open(io.BytesIO(image_bytes))
            contents_list.append(img) # போட்டோ இருந்தால் லிஸ்ட்டில் சேர்க்கிறோம்
        except Exception as e:
            print("Image Load Error:", e)

    # மொழிக்கு தகுந்தாற்போல் AI அட்வைஸ் கேட்கும் லாஜிக்
    advice_prompt = (
        "A short, expert 2-sentence market advice in Tamil explaining if this is a good deal considering the fuel type, owners count, and condition. If an image was uploaded, strictly mention what visual defects (like scratches, dents, or clean paint) you found in the photo, and state whether it matches the user claimed condition."
        if lang == 'ta' else
        "A short, expert 2-sentence market advice in English explaining if this is a good deal considering the fuel type, owners count, and condition. If an image was uploaded, strictly mention what visual defects (like scratches, dents, or clean paint) you found in the photo, and state whether it matches the user claimed condition."
    )

    prompt = f"""
    You are an expert Indian vehicle valuation and automobile market analyst. 
    Analyze the following vehicle and the uploaded photo (if present) to determine its exact used market resale value:
    
    Vehicle Name: {vehicle}
    Kilometers Driven: {km} km
    User Claimed Condition: {condition}
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
        "ai_advice": "{advice_prompt}"
    }}
    """
    
    contents_list.append(prompt) # பிராம்ப்ட்டை சேர்க்கிறோம்

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_list, # இமேஜ் மற்றும் டெக்ஸ்ட் இரண்டையும் ஒன்றாக அனுப்புகிறோம்
        )
        ai_response_text = response.text.strip()
        
        ai_response_text = ai_response_text.replace("```json", "").replace("```", "").replace("**", "").strip()
        
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
    except Exception as e:
        print("API Error:", e)
        error_text = "ஆன்லைனில் கணக்கிடுவதில் பிழை ஏற்பட்டது." if lang == 'ta' else "An error occurred during online calculation."
        return jsonify({"error": error_text}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
