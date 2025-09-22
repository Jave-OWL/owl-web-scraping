import requests
from bs4 import BeautifulSoup
import os
import urllib3
import re
import unidecode
import urllib
from urllib.parse import urljoin

#SELENIUM
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Scraping:

    def fetch_content(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        response = requests.get(self.url, headers=headers, verify=False)
        
        if response.status_code == 200:
            print(f" Acceso exitoso a {self.url}")
            return response.text
        else:
            print(f" Error {response.status_code}: No se pudo acceder a {self.url}")
            return None
    '''
    def parse_links(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True) + soup.find_all('link', href=True)

        pdf_links = []
        for link in links:
            href = link['href'].strip()

            # Convertir enlaces relativos a absolutos
            absolute_url = urljoin(self.url, href)
            
            if absolute_url.lower().endswith('.pdf'):
                pdf_links.append(absolute_url)
        
        return pdf_links'''
    
    def get_pdf_links(self):
        content = self.fetch_content()
        if content:
            return self.parse_links(content)
        else:
            return []
        
    def get_pdf_links(self):
        content = self.fetch_content()
        
        if content:
            pdf_links = self.parse_links(content)
            print(f" BeautifulSoup encontró {len(pdf_links)} PDFs.")
            
            if len(pdf_links) >= 10:
                print("Suficientes links con BeautifulSoup.")
                return pdf_links
            else:
                print("Menos de 10 PDFs con BeautifulSoup. Probando con Selenium...")
        
        return self.get_pdf_links_selenium()

    def download_pdf(self, pdf_url, output_dir='Fichas tecnicas', filename='FichaTecnica.pdf'):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            }

            response = requests.get(pdf_url, headers=headers, verify=False, timeout=10)

            if response.status_code == 200:
                if not filename:
                    filename = pdf_url.split('/')[-1]
                
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f'Descargado: {filepath}')
            else:
                raise Exception(f"Error {response.status_code}: No se pudo descargar {pdf_url}")

        except requests.exceptions.Timeout:
            raise Exception(f"Timeout: La descarga de {pdf_url} tardó demasiado y fue cancelada.")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en la solicitud: {e}")

        except Exception as e:
            raise Exception(f"Otro error en la descarga: {e}")


    def get_pdf_links_selenium(self):
        # Ruta del Edge WebDriver
        driver_path = "msedgedriver.exe"

        # Configuración del navegador Edge en modo headless (sin ventana)
        edge_options = Options()
        edge_options.add_argument("--headless")  # Opcional, ejecuta en segundo plano
        edge_options.add_argument("--disable-gpu")  # Evita problemas gráficos

        # Inicializar Edge WebDriver
        service = Service(driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)

        # URL objetivo
        url = self.url
        driver.get(url)

        # Esperar a que la página cargue completamente
        driver.implicitly_wait(10)

        # Buscar todos los enlaces <a> con href
        links = driver.find_elements(By.TAG_NAME, "a")

        # Filtrar solo los enlaces que contienen '.pdf'
        pdf_links = [link.get_attribute("href") for link in links if link.get_attribute("href") and '.pdf' in link.get_attribute("href").lower()]

        # Cerrar el navegador
        driver.quit()

        return pdf_links


#
# filtrar links
#

    def normalize_text(self, text):
        
        if not isinstance(text, str):
            text = str(text)
        
        # URL decoding
        try:
            text = urllib.parse.unquote(text)
        except:
            pass
        
        # Remove accents and convert to lowercase
        text = unidecode.unidecode(text).lower()
        
        # Replace URL-specific characters and encodings
        text = re.sub(r'[_/%+\-\.,:;]', ' ', text)
        
        # Remove file path and domain
        text = re.sub(r'https?://[^/]+/', '', text)
        text = re.sub(r'sites/default/files/[^/]+/', '', text)
        
        # Remove file extensions
        text = re.sub(r'\.(pdf|doc|xlsx?)$', '', text)
        
        # Replace multiple spaces and trim
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Add boundary spaces
        return f' {text} '

    def find_fund_variations(self, base_fund_name):
        
        normalized_base = self.normalize_text(base_fund_name)
        
        # List of words to remove from fund name
        words_to_remove = [
            'fondo',
            'fondo de inversion colectiva',
            'inversion',
            'colectiva',
            'abierto',
            'unica',
            'tipo',
            'clase',
            'renta fija'
        ]
        
        # Remove all specified words from the base name
        cleaned_name = normalized_base
        for word in words_to_remove:
            cleaned_name = re.sub(rf'\b{re.escape(word)}\b', '', cleaned_name)
        
        # Clean up extra spaces
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        variations = [
            cleaned_name.replace('fic', ''),  # Remove only 'fic'
            cleaned_name                  # Name with all common words removed
        ]
        
        # Add first/last word variations if there are multiple words
        words = cleaned_name.split()
        if len(words) > 1:
            variations.extend([
                ' '.join(words[:2]),      # First two words
                ' '.join(words[-2:])      # Last two words
            ])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variations))

    def find_month_variations(self, month):
        
        month_map = {
            'enero': ['01', 'ene'],
            'febrero': ['02', 'feb'],
            'marzo': ['03', 'mar'],
            'abril': ['04', 'abr'],
            'mayo': ['05', 'may'],
            'junio': ['06', 'jun'],
            'julio': ['07', 'jul'],
            'agosto': ['08', 'ago'],
            'septiembre': ['09', 'sep'],
            'octubre': ['10', 'oct'],
            'noviembre': ['11', 'nov'],
            'diciembre': ['12', 'dic']
        }
        
        if not month:
            return []
    
        normalized_month = self.normalize_text(month).strip()
        return [normalized_month] + month_map.get(normalized_month.lower(), [])

    def find_year_variations(self, year):
        
        year_str = str(year)
        return [
            f' {year_str} ',  # Year with spaces around
            f'/{year_str}/',  # Year between slashes
            f'-{year_str}-',  # Year between hyphens
            year_str,         # Full year
            year_str[-2:]
        ]
        
    
    def is_month_match(self, normalized_link, variations):
        
        weight = 0
        for variation in variations:
            if variation.isdigit():
                # Numeric month: lower weight
                pattern = rf'(^|[^\d])({re.escape(variation)})($|[^\d])'
                if re.search(pattern, normalized_link):
                    weight = max(weight, 1.5)
            else:
                # Text month: higher weight
                pattern = rf'(^|[^\w]|\d)({re.escape(variation)})($|[^\w]|\d)'
                if re.search(pattern, normalized_link):
                    weight = max(weight, 2)
                    # textual match is strongest, can break early
                    break
        return weight

    def is_year_match(self, normalized_link, variations):
        
        weight = 0
        for variation in variations:
            # Allow year to be between word chars or at boundaries
            pattern = rf'(^|[^\d]|[a-zA-Z])({re.escape(variation)})($|[^\d]|[a-zA-Z])'
            if re.search(pattern, normalized_link):
                weight = max(weight, 1.5)             
                break
        return weight
    
    def find_date_match(self, normalized_link, month_variations, year_variations):
        
        # get individual weights
        month_weight = self.is_month_match(normalized_link, month_variations)
        year_weight = self.is_year_match(normalized_link, year_variations)

        total_weight = month_weight + year_weight
        description_parts = []
        if month_weight >= 3:
            description_parts.append("Text month match")
        elif month_weight > 0:
            description_parts.append("Numeric month match")
        if year_weight > 0:
            description_parts.append("Year match")

        # If no direct month/year, try numeric combined patterns
        if total_weight == 0:
            numeric_patterns = self.find_numeric_date_patterns(month_variations, year_variations)
            for pattern in numeric_patterns:
                if re.search(rf'(^|[^\d])({re.escape(pattern)})($|[^\d])', normalized_link):
                    total_weight = 3
                    description_parts = ["Numeric date pattern match"]
                    break

        if total_weight == 0:
            description = "No date match"
        else:
            description = ", ".join(description_parts)
        return total_weight, description
    
    def get_last_day_of_month(self, month, year):
        
        # Handle months with 31 days
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        # Handle months with 30 days
        elif month in [4, 6, 9, 11]:
            return 30
        # Handle February
        else:
            # Check for leap year
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28

    def find_numeric_date_patterns(self, month_variations, year_variations):
        
        numeric_patterns = []
        
        # Get only numeric months
        numeric_months = [month for month in month_variations if month.isdigit()]
        
        # Get full year variation (e.g., '2024')
        full_year = next((year for year in year_variations if len(year.strip()) == 4), None)
        
        if numeric_months and full_year:
            month = numeric_months[0]  # Take first numeric month
            year = full_year.strip()
            
            # Get last day of the month
            last_day = self.get_last_day_of_month(int(month), int(year))
            
            # Generate patterns
            numeric_patterns.extend([
                f"{month}{year}",          # MMYYYY (122024)
                f"{year}{month}",          # YYYYMM (202412)
                f"{last_day}{month}{year}" # DDMMYYYY (31122024)
                f"{year}{month}{last_day}" # YYYYMMDD (20241231)
            ])
        
        return numeric_patterns
    
    def clean_fund_name_with_admin(self, admin, fondo):
        
        # Normalize both strings
        admin_normalized = self.normalize_text(admin).strip()
        fondo_normalized = self.normalize_text(fondo).strip()
        
        # Create a list of special terms to preserve
        special_terms = ['s.a.', 'sa', 's.a', 'a.s', 'a.s.']
        
        # Remove special terms from admin name before splitting
        for term in special_terms:
            admin_normalized = admin_normalized.replace(term, '')
        
        # Split admin into words and filter out empty strings
        admin_words = [word for word in admin_normalized.split() if word.strip()]
        
        # Sort admin words by length (longest first) to avoid partial matches
        admin_words.sort(key=len, reverse=True)
        
        # Remove each admin word if it appears as a complete word
        for word in admin_words:
            # Use word boundaries to avoid partial matches
            fondo_normalized = re.sub(rf'\b{re.escape(word)}\b', '', fondo_normalized)
        
        # Clean up extra spaces
        fondo_normalized = re.sub(r'\s+', ' ', fondo_normalized).strip()
        
        return fondo_normalized
            
    def is_fund_match(self, normalized_link, fund_variations):
        """
        Fund name matching that matches:
        - Any word from multi-word fund names
        - Single-word fund names when they appear as complete words or surrounded by numbers
        """
        for variation in fund_variations:
            # Clean up the variation
            variation = variation.strip()
            
            # Extract words from the variation and filter out empty strings
            variation_words = [w for w in variation.split() if w]
            
            # For single-word fund names
            if len(variation_words) == 1:
                word = variation_words[0]
                # Match patterns: word alone, or word surrounded by numbers
                patterns = [
                    rf'\b{re.escape(word)}\b',  # Exact word match
                    rf'\d+{re.escape(word)}\b',  # Numbers before
                    rf'\b{re.escape(word)}\d+',  # Numbers after
                    rf'\d+{re.escape(word)}\d+'  # Numbers both sides
                ]
                if any(re.search(pattern, normalized_link) for pattern in patterns):
                    return True
            # For multi-word fund names, match if any complete word is found
            else:
                if any(
                    re.search(rf'\b{re.escape(word)}\b', normalized_link)
                    for word in variation_words
                ):
                    return True
                    
        return False

    def remove_uuid_and_random_ids(self, normalized_link):
        """
        Remove UUIDs and random IDs with more precise matching
        """
        # UUID pattern matching 8-4-4-4-12 hex format
        uuid_pattern = r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b'
        
        # Remove query parameters with long values
        query_pattern = r'\?.*$'
        
        # Remove UUIDs 
        cleaned_link = re.sub(uuid_pattern, '', normalized_link)
        
        # Remove query string
        cleaned_link = re.sub(query_pattern, '', cleaned_link)
        
        # Clean up extra spaces
        cleaned_link = re.sub(r'\s+', ' ', cleaned_link).strip()
        
        return cleaned_link



    
    def filter_links_with_ai(self, links, admin, fondo, year, month, ficha_tecnica=True):
        cleaned_fondo = self.clean_fund_name_with_admin(admin, fondo)
        print(f'Fondo: {fondo}')
        print(f"Cleaned fund name: {cleaned_fondo}")

        fund_variations = [
            self.normalize_text(var) for var in 
            self.find_fund_variations(cleaned_fondo)
        ]
        print(f"Fund variations: {fund_variations}")

        month_variations = self.find_month_variations(month)
        year_variations = self.find_year_variations(year)

        ficha_tecnica_variations = [
            self.normalize_text(var) for var in 
            ['fichatecnica', 'ficha tecnica', 'fichastecnicas', 'fichas tecnicas', 'fichas tecnica', 'ficha tecnicas', ' ficha tecnica', ' ficha tecnica ', 'fichas técnicas', 'ficha']
        ] if ficha_tecnica else []

        filtered_links = []
        max_matches = 0

        for link_obj in links:
            # Extraer href, text y title
            href = link_obj.get('href', '')
            text = link_obj.get('text', '')
            title = link_obj.get('title', '')

            # Unir todo para analizar: href + text + title
            combined_content = f"{href} {text} {title}"

            # Limpiar, normalizar
            cleaned_link = self.remove_uuid_and_random_ids(combined_content)
            normalized_link = self.normalize_text(cleaned_link)

            matches = 0
            match_details = []

            # Fund match
            fund_match = self.is_fund_match(normalized_link, fund_variations)
            if fund_match:
                matches += 1
                match_details.append("Fund match")

            # Date match
            date_match_count, date_match_desc = self.find_date_match(normalized_link, month_variations, year_variations)
            if date_match_count > 0:
                matches += date_match_count
                match_details.append(date_match_desc)

            # Ficha Tecnica match
            if ficha_tecnica:
                ficha_match = any(
                    var.strip() in normalized_link 
                    for var in ficha_tecnica_variations
                )
                if ficha_match:
                    matches += 1.5
                    match_details.append(f"Ficha Tecnica match")

            if matches >= max_matches:
                max_matches = matches
                filtered_links.append(href)  # Solo devolver el href

        return filtered_links
