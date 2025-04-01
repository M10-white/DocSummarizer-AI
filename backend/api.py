from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
from extractor import extract_text_from_pdf, extract_text_from_docx
from summarizer import summarize_text_full

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename.lower()

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(contents)
        else:
            return {"summary": "❌ Format non pris en charge."}
    except Exception as e:
        return {"summary": f"❌ Erreur pendant l'extraction du texte : {str(e)}"}

    summary = summarize_text_full(text)
    return {"summary": summary}


@app.post("/extract")
async def extract_text(file: UploadFile = File(...)):
    filename = file.filename.lower()
    contents = await file.read()

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(contents)
        else:
            return {"text": "[⛔ Format non supporté pour l’aperçu]"}
    except Exception as e:
        return {"text": f"[❌ Erreur lors de l’extraction : {str(e)}]"}

    return {"text": text[:3000]}


translator_en_fr = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
translator_fr_en = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")

class TranslationRequest(BaseModel):
    summary: str
    target_lang: str

@app.post("/translate")
def translate(req: TranslationRequest):
    if req.target_lang == "fr":
        translated = translator_en_fr(req.summary)[0]["translation_text"]
    elif req.target_lang == "en":
        translated = translator_fr_en(req.summary)[0]["translation_text"]
    else:
        return {"translation": "❌ Langue cible non supportée."}
    
    return {"translation": translated}
