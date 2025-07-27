# PO Translator Web App

A web application for translating and editing PO files, built with Flask and MarianMT (Helsinki-NLP) models.

## Features
- Upload a PO file and select the target language
- Line-by-line translation with real-time progress bar
- Edit translated strings in a user-friendly table
- Download translated `.po` and compiled `.mo` files
- Supports multiple language pairs (dynamic model selection)

## Usage
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the app**
   ```bash
   python main.py
   ```
3. **Open in browser**
   Visit [http://localhost:5000](http://localhost:5000)

## Workflow
- Upload your `.po` file and choose the target language
- The app translates each entry and shows a progress bar
- After translation, you can review and edit each string
- Save your changes, then download the `.po` or `.mo` file

## Technologies
- **Flask**: Web framework
- **polib**: PO/MO file handling
- **transformers**: MarianMT translation models
- **huggingface_hub**: Dynamic model listing
- **HTML/CSS/JS**: Modern, responsive frontend

## Folder Structure
```
python/sandbox/wordpress-translator/po-translator/
├── main.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── progress.html
│   └── edit.html
├── static/
│   └── style.css
├── uploads/
├── translated/
├── progress/
```

## Customization
- Add new language pairs by extending the model list
- UI and workflow can be customized via the templates and CSS

## License
MIT
