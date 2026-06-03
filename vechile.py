import os
import json
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client()

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate_with_ai():
    # டேட்டாவை பெறுதல்
    v_name = request.form.get('vehicle', 'Unknown')
    km = request.form.get('km', '0')
    
    # ஜெமினிக்கான கறாரான கட்டளை
    prompt = f"""
    Act as a vehicle valuer. Output ONLY raw JSON. No markdown, no intro, no explanation.
    Details: {v_name}, {km}km.
    JSON format:
    {{
        "vehicle_name": "{v_name}",
        "kilometers": "{km}",
        "condition": "Good",
        "fuel_type": "Petrol",
        "owners": "1st Owner",
        "new_price": 500000,
        "estimated_price": 300000,
        "depreciation_percent": 40,
        "ai_advice": "Vehicle is in good condition."
    }}
    """
    
    # மீண்டும் முயற்சிக்கும் லூப்
    for i in range(3):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            
            # JSON பகுதி மட்டும் எடுக்கும் முயற்சி
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end != -1:
                final_json = raw_text[start:end]
                return jsonify(json.loads(final_json))
        except:
            time.sleep(1)
            continue
            
    return jsonify({"error": "Failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
