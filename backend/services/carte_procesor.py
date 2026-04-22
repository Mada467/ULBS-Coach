import fitz
import pytesseract
from PIL import Image
import io
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Total pagini: {total_pages}")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            
            page_text = page.get_text()
            
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
            else:
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(img, lang='ron+eng')
                text += ocr_text + "\n"
        
        doc.close()
        print("PDF procesat cu succes!")
        return text
    except Exception as e:
        print(f"Eroare la procesare PDF: {e}")
        return None

def save_text_to_file(text, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Text salvat in: {output_path}")
        return True
    except Exception as e:
        print(f"Eroare la salvare: {e}")
        return False