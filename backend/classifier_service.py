# backend/classifier_service.py
import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "classifier.joblib")
VECTORIZER_PATH = os.path.join(BASE_DIR, "ml", "models", "vectorizer.joblib")

_classifier = joblib.load(MODEL_PATH)
_vectorizer = joblib.load(VECTORIZER_PATH)

def predict_document_type(cleaned_text: str) -> tuple[str, float]:
    X = _vectorizer.transform([cleaned_text])
    probs = _classifier.predict_proba(X)[0]
    classes = _classifier.classes_
    best_idx = probs.argmax()
    return classes[best_idx], float(probs[best_idx])