import re
import unicodedata

SHORT_WORD_WHITELIST = {
    "de", "du", "le", "la", "un", "une", "en", "et", "ne", "ce", "se",
    "on", "il", "tu", "ou", "si", "au", "aux", "des", "les", "ma", "ta",
    "sa", "mon", "ton", "son", "ces", "nos", "vos", "et",
}

def clean_text(text: str) -> str:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # drop punctuation entirely now — tokenizer ignores it anyway
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    kept = []
    for tok in tokens:
        if tok.isdigit():
            if len(tok) >= 2:          # keep real numbers (contract nos, amounts, plate digits)
                kept.append(tok)
            continue
        if len(tok) < 3 and tok not in SHORT_WORD_WHITELIST:
            continue                    # drop 1-2 char garbage like "dh", "dn", "pa"
        kept.append(tok)
    return " ".join(kept)