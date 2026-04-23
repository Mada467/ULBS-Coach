import fitz
import pytesseract
from PIL import Image
import io

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"[OCR] Total pagini: {total_pages}", flush=True)
        
        for page_num in range(total_pages):
            page = doc[page_num]
            page_text = page.get_text()
            
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
            else:
                print(f"[OCR] Pagina {page_num + 1} e scanata, incerc OCR...", flush=True)
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(img, lang='ron+eng')
                text += ocr_text + "\n"
        
        doc.close()
        print(f"[OCR] PDF procesat! {len(text)} caractere extrase.", flush=True)
        return text
    except Exception as e:
        print(f"[OCR] Eroare la procesare PDF: {e}", flush=True)
        return None