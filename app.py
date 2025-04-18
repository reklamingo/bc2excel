
from flask import Flask, request, send_file
import requests
import pandas as pd
import base64
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

GOOGLE_VISION_API_KEY = "AIzaSyBhn6CJiR0fN_RvsPKoCuOL3m04IKtNbF0"

def extract_text_from_image(img_bytes):
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "requests": [{
            "image": {"content": base64_image},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    try:
        return result['responses'][0]['fullTextAnnotation']['text']
    except KeyError:
        return "OCR başarısız oldu. Kartvizit metni tespit edilemedi."

def parse_info(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    info = {
        "İsim": "",
        "Ünvan": "",
        "Telefon": "",
        "E-posta": "",
        "Web": "",
        "Şirket": "",
        "Adres": ""
    }

    for i, line in enumerate(lines):
        l = line.lower()
        if i == 0:
            info["İsim"] = line
        elif i == 1:
            info["Ünvan"] = line
        elif '@' in line:
            info["E-posta"] = line
        elif 'www' in l or '.com' in l:
            info["Web"] = line
        elif '+' in line and any(c.isdigit() for c in line):
            info["Telefon"] += line + " / "
        elif any(word in l for word in ['san', 'tic', 'a.ş', 'ltd', 'hold', 'matbaa', 'a.s', 'company']):
            info["Şirket"] = line
        elif info["Şirket"] == "" and 2 <= i <= 5:
            info["Şirket"] = line
        else:
            info["Adres"] += line + " "
    return info

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('files')
        records = []
        for file in files:
            img_bytes = file.read()
            text = extract_text_from_image(img_bytes)
            record = parse_info(text)
            records.append(record)
        df = pd.DataFrame(records)
        output = os.path.join(app.config['UPLOAD_FOLDER'], 'kartvizitler.xlsx')
        df.to_excel(output, index=False)
        return send_file(output, as_attachment=True)
    return '''
        <!doctype html>
        <html>
        <head>
            <title>Karttan Excel</title>
            <style>
                body { font-family: Arial; text-align: center; margin-top: 50px; }
                h1 { color: #003e92; }
                input[type=file] {
                    padding: 10px;
                    margin: 10px;
                }
                input[type=submit] {
                    padding: 10px 20px;
                    background: #003e92;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                .container {
                    border: 1px solid #ccc;
                    padding: 30px;
                    max-width: 600px;
                    margin: auto;
                    border-radius: 10px;
                    background-color: #f5f5f5;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Kartvizit Fotoğraflarını Yükle</h1>
                <form method=post enctype=multipart/form-data>
                    <input type=file name=files multiple><br>
                    <input type=submit value="Excel'e Dönüştür">
                </form>
            </div>
        </body>
        </html>
    '''
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
