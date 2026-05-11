from typing import Any, Dict


def extract_ocr(image_bytes: bytes) -> Dict[str, Any]:
    try:
        import pytesseract

        try:
            import cv2
            import numpy as np

            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            ocr_text = pytesseract.image_to_string(thresh)
        except (ImportError, Exception):
            # cv2 unavailable — fall back to PIL
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_bytes)).convert("L")
            ocr_text = pytesseract.image_to_string(image)

        return {"ocrText": ocr_text.strip()}
    except Exception as e:
        return {"error": f"Failed to extract OCR: {str(e)}"}
