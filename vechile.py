import os
import json
from flask import Flask, request, jsonify, send_from_directory
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/estimate', methods=['POST'])
def estimate():
    try:
        v = request.form.get('vehicle', 'Car')
        # மிகச் சுருக்கமான கட்டளை
        prompt = f"Return JSON only for vehicle {v}. Use keys: name, price."
        
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        # பதில் வந்தவுடன் அதை JSON ஆக மாற்றுகிறது
        text = response.text.replace('```json', '').replace('```', '').strip()
        return jsonify(json.loads(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
