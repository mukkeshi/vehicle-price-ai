import os
import json
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image

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

    # போட்டோ இருந்தால் பிராசஸ் செய்கிறது
    if photo_file:
        try:
            image_bytes = photo_file.read()
            img = Image.open(io.BytesIO(image_bytes))
            contents_list.append(img)
        except Exception as e:
            print("Image Load Error:", e)

    # நாய்/விலங்கு போட்டோக்களை கண்டறியும் துல்லியமான பிராம்ப்ட் லாஜிக்
    advice_prompt = (
        "CRITICAL IMAGE VALIDATION: If the uploaded image is NOT a vehicle (e.g., if it is a dog, cat, animal, person, building, food or random object), you must strictly set the 'estimated_price' to 0 and 'new_price' to 0, and set 'ai_advice' to 'தயவுசெய்து சரியான வாகனத்தின் புகைப்படத்தை பதிவேற்றவும்! நீங்கள் பதிவேற்றிய புகைப்படம் ஒரு வாகனம் அல்ல.'. Otherwise, write a short, expert 2-sentence market advice in Tamil. If a valid vehicle image was uploaded, mention what visual defects (like scratches, dents, or clean paint) you found in the photo."
        if lang == 'ta' else
        "CRITICAL IMAGE VALIDATION: If the uploaded image is NOT a vehicle (e.g., if it is a dog, cat, animal, person, building, food or random object), you must strictly set the 'estimated_price' to 0 and 'new_price' to 0, and set 'ai_advice' to 'Please upload a valid vehicle image! The uploaded image is not a vehicle.'. Otherwise, write a short, expert 2-sentence market advice in English. If a valid vehicle image was uploaded, mention what visual defects (like scratches, dents, or clean paint) you found in the photo."
    )

    prompt = f"""
    You are an expert Indian vehicle valuation and automobile market analyst. 
    Analyze the following vehicle details and the uploaded photo (if present):
    
    Vehicle Name: {vehicle}
    Kilometers Driven: {km} km
    User Claimed Condition: {condition}
    Fuel Type: {fuel_type}
    Number of Owners: {owners}
    
    CRITICAL INSTRUCTION: Look at the uploaded image. If it contains a dog, cat, animal, human face, building, food or anything that is NOT a car, bike, scooter, truck, or commercial vehicle, treat it as an INVALID image. For invalid images, you MUST return 'new_price': 0, 'estimated_price': 0, 'depreciation_percent': 0 and the rejection warning inside 'ai_advice'.
    
    Return the response strictly as a JSON object with these exact keys. Do not include markdown codeblocks or '```json'. Just pure JSON content text:
    {{
        "vehicle_name": "{vehicle.upper()}",
        "kilometers": "{km}",
        "condition": "{condition}",
        "fuel_type": "{fuel_type}",
        "owners": "{owners}",
        "new_price": "integer price or 0 if image is invalid",
        "estimated_price": "integer used resale price or 0 if image is invalid",
        "depreciation_percent": "integer drop percentage or 0 if image is invalid",
        "ai_advice": "{advice_prompt}"
    }}
    """
    
    contents_list.append(prompt)

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_list,
        )
        ai_response_text = response.text.strip()
        
        # எர்ரர் வராமல் தடுக்க மார்க்-டவுன் குறியீடுகள் (```) இங்கே நீக்கப்படுகின்றன
        if "```json" in ai_response_text:
            ai_response_text = ai_response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_response_text:
            ai_response_text = ai_response_text.split("
```")[1].split("```")[0].strip()
            
        ai_response_text = ai_response_text.replace("**", "").strip()
        
        # கிளீன் செய்யப்பட்ட சுத்தமான JSON உரையை இப்போது லோடு செய்கிறோம்
        result_data = json.loads(ai_response_text)
        return jsonify(result_data)
        
    except Exception as e:
        print("API or JSON Parsing Error:", e)
        error_text = "ஆன்லைனில் கணக்கிடுவதில் பிழை ஏற்பட்டது." if lang == 'ta' else "An error occurred during online calculation."
        return jsonify({"error": error_text}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
