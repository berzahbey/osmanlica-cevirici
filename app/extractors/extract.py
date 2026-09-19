# -*- coding: utf-8 -*-
"""Girdi dosyalarından ham metni çıkarır: pdf, epub, txt, jpg/png (OCR)."""
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup


def extract_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = []
    for page in doc:
        text.append(page.get_text())
    doc.close()
    return "\n".join(text)


def extract_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_from_image(path: str, ocr_lang: str = "tur+eng") -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang=ocr_lang)


def extract_from_epub(path: str) -> str:
    book = epub.read_epub(path)
    parts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            parts.append(soup.get_text(separator="\n"))
    return "\n".join(parts)


EXTRACTORS = {
    ".pdf": extract_from_pdf,
    ".txt": extract_from_txt,
    ".jpg": extract_from_image,
    ".jpeg": extract_from_image,
    ".png": extract_from_image,
    ".epub": extract_from_epub,
}


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext not in EXTRACTORS:
        raise ValueError(f"Desteklenmeyen dosya türü: {ext}")
    return EXTRACTORS[ext](path)
