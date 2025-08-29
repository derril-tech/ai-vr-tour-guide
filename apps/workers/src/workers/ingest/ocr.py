"""
OCR (Optical Character Recognition) processor for extracting text from images and scanned documents.
"""

import io
import logging
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logging.warning("Tesseract OCR not available. Install pytesseract and tesseract-ocr.")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    logging.warning("EasyOCR not available. Install easyocr for better OCR results.")

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Processor for extracting text from images using OCR."""
    
    def __init__(self):
        self.tesseract_available = HAS_TESSERACT
        self.easyocr_available = HAS_EASYOCR
        self.easyocr_reader = None
        
        if self.easyocr_available:
            try:
                # Initialize EasyOCR reader with common languages
                self.easyocr_reader = easyocr.Reader(['en', 'es', 'fr', 'de', 'it'])
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False
    
    async def extract_text(self, content: bytes, content_type: str) -> str:
        """Extract text from image content using OCR."""
        try:
            if not self.tesseract_available and not self.easyocr_available:
                logger.error("No OCR engines available")
                return ""
            
            # Convert content to PIL Image
            image = Image.open(io.BytesIO(content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Try EasyOCR first (generally better results)
            if self.easyocr_available and self.easyocr_reader:
                try:
                    text = await self._extract_with_easyocr(image)
                    if text.strip():
                        logger.info("Successfully extracted text using EasyOCR")
                        return text
                except Exception as e:
                    logger.warning(f"EasyOCR failed: {e}")
            
            # Fallback to Tesseract
            if self.tesseract_available:
                try:
                    text = await self._extract_with_tesseract(image)
                    if text.strip():
                        logger.info("Successfully extracted text using Tesseract")
                        return text
                except Exception as e:
                    logger.warning(f"Tesseract failed: {e}")
            
            logger.warning("No OCR engine could extract text")
            return ""
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return ""
    
    async def _extract_with_easyocr(self, image: Image.Image) -> str:
        """Extract text using EasyOCR."""
        # Convert PIL Image to numpy array for EasyOCR
        import numpy as np
        image_array = np.array(image)
        
        # Extract text
        results = self.easyocr_reader.readtext(image_array)
        
        # Combine all detected text
        text_parts = []
        for (bbox, text, confidence) in results:
            # Only include text with reasonable confidence
            if confidence > 0.5:
                text_parts.append(text)
        
        return ' '.join(text_parts)
    
    async def _extract_with_tesseract(self, image: Image.Image) -> str:
        """Extract text using Tesseract OCR."""
        # Configure Tesseract for better results
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?;:-()[]{}"\''
        
        # Extract text
        text = pytesseract.image_to_string(image, config=custom_config)
        
        # Clean up the text
        text = self._clean_ocr_text(text)
        
        return text
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean up OCR-extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        # Join lines with proper spacing
        cleaned_text = ' '.join(lines)
        
        # Remove multiple spaces
        import re
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    async def extract_text_with_coordinates(self, content: bytes, content_type: str) -> list:
        """Extract text with bounding box coordinates (useful for layout analysis)."""
        try:
            if not self.easyocr_available:
                logger.warning("Coordinate extraction requires EasyOCR")
                return []
            
            image = Image.open(io.BytesIO(content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            import numpy as np
            image_array = np.array(image)
            
            # Extract text with coordinates
            results = self.easyocr_reader.readtext(image_array)
            
            # Format results
            text_regions = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:
                    text_regions.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox,  # List of 4 (x, y) coordinates
                    })
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Error extracting text with coordinates: {str(e)}")
            return []
    
    def is_available(self) -> bool:
        """Check if OCR functionality is available."""
        return self.tesseract_available or self.easyocr_available
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        languages = []
        
        if self.tesseract_available:
            try:
                # Get Tesseract languages
                tesseract_langs = pytesseract.get_languages()
                languages.extend(tesseract_langs)
            except Exception:
                pass
        
        if self.easyocr_available:
            # EasyOCR supported languages
            easyocr_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
            languages.extend(easyocr_langs)
        
        return list(set(languages))  # Remove duplicates
