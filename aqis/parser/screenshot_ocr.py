from typing import Any, Dict


def extract_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract OCR text from a screenshot using Tesseract and OpenCV preprocessing.

    Args:
        image_bytes (bytes): The content of the screenshot file.

    Returns:
        dict: Extracted OCR text and preprocessed image data.
    """
    try:
        import cv2
        import numpy as np
        import pytesseract

        # Decode image bytes
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Preprocess image (grayscale and thresholding)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Extract text using Tesseract
        ocr_text = pytesseract.image_to_string(thresh)

        return {"ocrText": ocr_text}
    except Exception as e:
        # Gracefully handle OCR errors
        return {"error": f"Failed to extract OCR: {str(e)}"}
