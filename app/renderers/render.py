# -*- coding: utf-8 -*-
"""
Osmanlica (Arap harfli) metni ciktiya render eder.
PDF icin WeasyPrint kullanilir: Pango/HarfBuzz tabanli gercek bir
metin motoru oldugu icin Arapca harflerin baglamsal birlesimini
(bas/orta/son/tek basina formlari) ve sagdan-sola siralamayi
OTOMATIK ve DOGRU yapar - reportlab'in aksine manuel reshaping/bidi
gerektirmez.
"""
import os
from ebooklib import epub

FONT_PATH = os.environ.get("OTTOMAN_FONT_PATH", "/app/fonts/ScheherazadeNew-Regular.ttf")

EASTERN_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_pdf(ottoman_text: str, out_path: str, font_size: int = 16):
    from weasyprint import HTML

    lines = [l for l in ottoman_text.split("\n") if l.strip()]
    paragraphs = "".join(
        f"<p>{_html_escape(line).translate(EASTERN_DIGITS)}</p>" for line in lines
    )

    html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @font-face {{
            font-family: "ScheherazadeNew";
            src: url("file://{FONT_PATH}");
        }}
        @page {{
            margin: 2.5cm;
        }}
        body {{
            font-family: "ScheherazadeNew", serif;
            direction: rtl;
            font-size: {font_size}pt;
            line-height: 1.7;
            text-align: right;
        }}
        p {{
            margin: 0.3em 0;
        }}
    </style>
    </head>
    <body>{paragraphs}</body>
    </html>
    """
    HTML(string=html).write_pdf(out_path)


def render_txt(ottoman_text: str, out_path: str):
    converted = ottoman_text.translate(EASTERN_DIGITS)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(converted)


def render_epub(ottoman_text: str, out_path: str, title: str = "Osmanlica Ceviri"):
    book = epub.EpubBook()
    book.set_identifier("osmanlica-ceviri-" + os.urandom(4).hex())
    book.set_title(title)
    book.set_language("ota")

    with open(FONT_PATH, "rb") as f:
        font_data = f.read()
    font_item = epub.EpubItem(
        uid="font1", file_name="fonts/ScheherazadeNew-Regular.ttf",
        media_type="font/ttf", content=font_data,
    )
    book.add_item(font_item)

    css_content = """
    @font-face {
        font-family: "ScheherazadeNew";
        src: url("fonts/ScheherazadeNew-Regular.ttf");
    }
    body { font-family: "ScheherazadeNew", serif; direction: rtl; font-size: 1.3em;
            line-height: 2; text-align: right; }
    """
    css_item = epub.EpubItem(
        uid="style1", file_name="style/main.css", media_type="text/css", content=css_content,
    )
    book.add_item(css_item)

    paragraphs = "".join(
        f"<p>{_html_escape(line).translate(EASTERN_DIGITS)}</p>"
        for line in ottoman_text.split("\n") if line.strip()
    )
    chapter = epub.EpubHtml(title=title, file_name="chap_1.xhtml", lang="ota")
    chapter.content = f"<html><body dir='rtl'>{paragraphs}</body></html>"
    chapter.add_item(css_item)
    chapter.add_item(font_item)
    book.add_item(chapter)

    book.toc = (epub.Link("chap_1.xhtml", title, "chap1"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    epub.write_epub(out_path, book)


def render_for_format(ottoman_text: str, output_ext: str, out_path: str):
    ext = output_ext.lower()
    if ext == ".pdf":
        render_pdf(ottoman_text, out_path)
    elif ext == ".txt":
        render_txt(ottoman_text, out_path)
    elif ext == ".epub":
        render_epub(ottoman_text, out_path)
    elif ext in (".jpg", ".jpeg", ".png"):
        render_pdf(ottoman_text, out_path.rsplit(".", 1)[0] + ".pdf")
    else:
        raise ValueError(f"Desteklenmeyen cikti formati: {ext}")
