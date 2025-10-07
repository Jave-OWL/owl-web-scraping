import os
import argparse
from pathlib import Path
import json
import pandas as pd


import pdfplumber
import PyPDF2


try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class PDFExplorer:
    def __init__(self, ocr_fallback=False):
        
        self.ocr_fallback = ocr_fallback and OCR_AVAILABLE
        
    def explore_pdf(self, pdf_path):
        
        result = {
            'filename': Path(pdf_path).name,
            'full_text': '',
            'tables': [],
            'metadata': {}
        }
        
        
        self._extract_metadata(pdf_path, result)
        
        
        text_extracted = self._extract_with_pdfplumber(pdf_path, result)
        
        
        if not text_extracted and self.ocr_fallback:
            self._extract_with_ocr(pdf_path, result)
            
        return result
    
    def _extract_metadata(self, pdf_path, result):
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata = reader.metadata
                if metadata:
                    for key, value in metadata.items():
                        clean_key = key.strip('/').lower()
                        result['metadata'][clean_key] = value
                result['num_pages'] = len(reader.pages)
        except Exception as e:
            print(f"Error extrayendo metadatos: {e}")
    
    def _extract_with_pdfplumber(self, pdf_path, result):
        """Extraer texto y tablas"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                
                for page_num, page in enumerate(pdf.pages, 1):
                    
                    page_text = page.extract_text() or ""
                    if page_text:
                        result['full_text'] += f"\n--- Page {page_num} ---\n{page_text}\n"
                    
                    
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables, 1):
                        if table:
                            
                            headers = [str(cell).strip() if cell else f"Col{i}" 
                                      for i, cell in enumerate(table[0])]
                            
                            rows = table[1:] if len(table) > 1 else []
                            clean_rows = []
                            for row in rows:
                                clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                                clean_rows.append(clean_row)
                            
                            
                            if clean_rows:
                                df = pd.DataFrame(clean_rows, columns=headers)
                                table_dict = {
                                    'page': page_num,
                                    'table_num': table_num,
                                    'headers': headers,
                                    'data': df.to_dict('records')
                                }
                                result['tables'].append(table_dict)
            
            return bool(result['full_text'])
        
        except Exception as e:
            print(f"Error extrayendo con pdfplumber: {e}")
            return False
    
    def _extract_with_ocr(self, pdf_path, result):
        
        try:
            
            images = convert_from_path(pdf_path)
            
            for page_num, img in enumerate(images, 1):
                
                text = pytesseract.image_to_string(img)
                if text:
                    result['full_text'] += f"\n--- Page {page_num} (OCR) ---\n{text}\n"
            
            return bool(result['full_text'])
        
        except Exception as e:
            print(f"Error extrayendo con ocr: {e}")
            return False

def explore_directory(directory_path, output_dir, ocr_fallback=False):
    
    explorer = PDFExplorer(ocr_fallback=ocr_fallback)
    
    
    os.makedirs(output_dir, exist_ok=True)
    
    
    pdf_files = list(Path(directory_path).glob('*.pdf'))
    
    
    all_results = []
    
    for pdf_file in pdf_files:
        print(f"Procesando {pdf_file.name}...")
        result = explorer.explore_pdf(pdf_file)
        
        
        text_output = os.path.join(output_dir, f"{pdf_file.stem}_text.txt")
        with open(text_output, 'w', encoding='utf-8') as f:
            f.write(f"Archivo: {pdf_file.name}\n")
            f.write(f"Paginas: {result.get('num_pages', 'Unknown')}\n")
            f.write(f"Metadata: {json.dumps(result['metadata'], indent=2)}\n\n")
            f.write("=== TEXTO EXTRAIDO ===\n")
            f.write(result['full_text'])
        print(f"  Texto guardado en {text_output}")
        
        
        if result['tables']:
            for i, table in enumerate(result['tables'], 1):
                table_output = os.path.join(output_dir, f"{pdf_file.stem}_table_{i}.csv")
                df = pd.DataFrame(table['data'])
                df.to_csv(table_output, index=False)
                print(f"  Tabla {i} guardada en {table_output}")
        
        
        summary_record = {
            'filename': result['filename'],
            'num_pages': result.get('num_pages', 0),
            'has_text': bool(result['full_text']),
            'num_tables': len(result['tables']),
            'metadata': result['metadata']
        }
        all_results.append(summary_record)
    
    
    if all_results:
        summary_df = pd.DataFrame(all_results)
        summary_output = os.path.join(output_dir, "pdfs_summary.csv")
        summary_df.to_csv(summary_output, index=False)
        print(f"\nResumen guardado en {summary_output}")




PDF_DIRECTORY = r"Fichas prueba"

OUTPUT_DIRECTORY = r"Prueba output"

USE_OCR = True

def main():
    
    print(f"Sacando pdfs de {PDF_DIRECTORY}")
    print(f"Los resultados se guardan en {OUTPUT_DIRECTORY}")
    print(f"OCR esta {'habilitado' if USE_OCR else 'deshabilitado'}")
    
    
    summary = explore_directory(PDF_DIRECTORY, OUTPUT_DIRECTORY, USE_OCR)
    
    if summary is not None:
        print("\nProceso completo. Archivos procesados:")
        print(summary)
    else:
        print("\nProceso completo, no se pudo procesar.")

if __name__ == "__main__":
    main()