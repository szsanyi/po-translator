from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
from huggingface_hub import list_models
from langcodes import Language, LanguageTagError
from transformers import MarianMTModel, MarianTokenizer
import os
import polib
import threading
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
TRANSLATED_FOLDER = 'translated'
PROGRESS_FOLDER = 'progress'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)
os.makedirs(PROGRESS_FOLDER, exist_ok=True)

def get_available_models():
    models = list_models(author="Helsinki-NLP")
    en_models = []
    for m in models:
        if m.modelId.startswith("Helsinki-NLP/opus-mt-en-"):
            code = m.modelId.replace("Helsinki-NLP/opus-mt-", "")
            parts = code.split('-')
            if len(parts) == 2:
                try:
                    Language.get(parts[1])
                    en_models.append(code)
                except LanguageTagError:
                    continue
    if 'en-hu' in en_models:
        en_models.remove('en-hu')
        en_models.insert(0, 'en-hu')
    return en_models

AVAILABLE_CODES = get_available_models()

MODELS = {
    code: f"Helsinki-NLP/opus-mt-{code}"
    for code in AVAILABLE_CODES
}

MODEL_LABELS = {
    code: f"English → {Language.get(code.split('-')[1]).display_name('en').capitalize()}"
    for code in AVAILABLE_CODES
}

loaded_models = {}

def get_model_pair(code):
    if code not in loaded_models:
        tokenizer = MarianTokenizer.from_pretrained(MODELS[code])
        model = MarianMTModel.from_pretrained(MODELS[code])
        loaded_models[code] = (tokenizer, model)
    return loaded_models[code]

def translate_text(text, code):
    tokenizer, model = get_model_pair(code)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def translate_po_file_async(file_id, lang_code):
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.po")
    output_path = os.path.join(TRANSLATED_FOLDER, f"{file_id}_translated.po")
    progress_path = os.path.join(PROGRESS_FOLDER, f"{file_id}.json")
    po = polib.pofile(input_path)
    total = len(po)
    done = 0
    status = {
        "total": total,
        "done": 0,
        "error": False,
        "finished": False
    }
    with open(progress_path, "w") as f:
        f.write(str(status))
    for entry in po:
        if entry.msgid and not entry.msgstr:
            try:
                entry.msgstr = translate_text(entry.msgid, lang_code)
            except Exception as e:
                entry.msgstr = f"[HIBA: {str(e)}]"
        done += 1
        status["done"] = done
        with open(progress_path, "w") as f:
            f.write(str(status))
            
    po.save(output_path)
    status["finished"] = True
    with open(progress_path, "w") as f:
        f.write(str(status))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['po_file']
        lang_code = request.form.get('lang')
        if not file or not file.filename.endswith('.po'):
            return 'Hibás fájlformátum!', 400

        file_id = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.po")
        file.save(input_path)

        t = threading.Thread(target=translate_po_file_async, args=(file_id, lang_code))
        t.start()

        return render_template('progress.html', file_id=file_id)

    return render_template('index.html', model_codes=MODEL_LABELS)

@app.route('/progress/<file_id>')
def progress(file_id):
    progress_path = os.path.join(PROGRESS_FOLDER, f"{file_id}.json")
    if not os.path.exists(progress_path):
        return jsonify({"total": 1, "done": 0, "finished": False})
    try:
        with open(progress_path) as f:
            status = eval(f.read())
        return jsonify(status)
    except Exception:
        return jsonify({"total": 1, "done": 0, "finished": False})

@app.route('/edit/<file_id>', methods=['GET', 'POST'])
def edit(file_id):
    file_path = os.path.join(TRANSLATED_FOLDER, f"{file_id}_translated.po")
    if not os.path.exists(file_path):
        return "Fájl nem található", 404

    po = polib.pofile(file_path)

    if request.method == 'POST':
        for entry in po:
            key = f"msgstr_{entry.msgid}"
            if key in request.form:
                entry.msgstr = request.form.get(key)
        po.save(file_path)
        return redirect(url_for('download', file_id=file_id))

    return render_template('edit.html', po=po, file_id=file_id)

@app.route('/download/<file_id>')
def download(file_id):
    path = os.path.join(TRANSLATED_FOLDER, f"{file_id}_translated.po")
    return send_file(path, as_attachment=True, download_name="translated.po")

@app.route('/download_mo/<file_id>')
def download_mo(file_id):
    po_path = os.path.join(TRANSLATED_FOLDER, f"{file_id}_translated.po")
    mo_path = os.path.join(TRANSLATED_FOLDER, f"{file_id}_translated.mo")
    if not os.path.exists(po_path):
        return "PO file not found", 404
    po = polib.pofile(po_path)
    po.save_as_mofile(mo_path)
    return send_file(mo_path, as_attachment=True, download_name="translated.mo")

if __name__ == '__main__':
    app.run(debug=True)
