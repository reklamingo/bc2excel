
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
    lines = text.split('\n')
    info = {
        "İsim": "",
        "Ünvan": "",
        "Telefon": "",
        "E-posta": "",
        "Web": "",
        "Şirket": "",
        "Adres": ""
    }

    for line in lines:
        parts = [p.strip() for p in line.split("/") if p.strip()]
        for part in parts:
            lower = part.lower()
            if '@' in part and info["E-posta"] == "":
                info["E-posta"] = part
            elif ('www' in part or '.com' in part) and info["Web"] == "":
                info["Web"] = part
            elif '+' in part and any(c.isdigit() for c in part):
                info["Telefon"] += part + ' / '
            elif any(keyword in lower for keyword in ["san", "tic", "a.ş", "ltd", "hold", "matbaa", "as", "a.s"]):
                info["Şirket"] = part
            elif info["İsim"] == "" and len(part.split()) <= 3:
                info["İsim"] = part
            elif info["Ünvan"] == "" and any(keyword in lower for keyword in ["müdür", "uzmanı", "yöneticisi", "analist", "tasarımcı", "sorumlu", "direktör", "koordinatör", "geliştirici", "danışman", "ceo"]):
                info["Ünvan"] = part
            else:
                info["Adres"] += part + ' '
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
        <title>Karttan Excel (Google OCR)</title>
        <h1>Kartvizit Fotoğraflarını Yükle</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=files multiple>
          <input type=submit value="Excel'e Dönüştür">
        </form>
    '''
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
