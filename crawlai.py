import os
import sys
import platform
from pydantic import BaseModel
from Extraer import LinkExtractor
from Scraping import Scraping
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


class Url(BaseModel):
    url: str


__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")
result_counter = 0

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

ADMINS_ESPECIALES = [
    # "Progresion",
    # "Banco de Occidente Fiduoccidente"
]

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import os

def expandir_acordeon_documentacion(driver):
    """Expande el acordeón 'Documentación' dentro del Shadow DOM del iframe BBVA."""
    try:
        print(" Buscando acordeón de 'Documentación' dentro del shadow DOM...")
        driver.execute_script("""
        const getDeepShadow = (root, selectors) => {
        let el = root;
        for (const sel of selectors) {
        el = el.shadowRoot ? el.shadowRoot.querySelector(sel) : el.querySelector(sel);
        if (!el) return null;
        }
        return el;
        };

        ```
                // Navegar hasta el accordion de Documentación
                const page = document.querySelector('fichaco-page');
                const info = page.shadowRoot.querySelector('fichaco-info');
                const main = info.shadowRoot.querySelector('main');
                const accordion = main.querySelector('accordion-component');
                const titulo = accordion.shadowRoot.querySelectorAll('div.accordion-titulo');

                // Buscar el acordeón que diga 'Documentación'
                let target = null;
                titulo.forEach(t => {
                    if (t.textContent.toLowerCase().includes('documentación')) target = t;
                });

                if (target) {
                    const btn = target.querySelector('bbva-button-action');
                    if (btn) btn.click();
                    return true;
                } else {
                    return false;
                }
            """)
        print(" ✅ Acordeón 'Documentación' expandido correctamente.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f" ⚠️ Error expandiendo el acordeón 'Documentación': {e}")
        return False

def handle_bbva_case(driver, fondo, admin, year, month):
    """Manejo especial para fondos BBVA con shadow DOM e iframe."""
    print(f" {fondo} ({admin}) - Iniciando caso especial BBVA con Shadow DOM...")

    wait = WebDriverWait(driver, 30)
    scraping = Scraping()

    try:
        # --- Esperar el iframe ---
        print(" Esperando iframe del fondo...")
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeIsin")))
        print(" ✅ Cambiado al iframe principal.")

        # --- Esperar el host del shadow root ---
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "fichaco-page")))
        print(" Esperando el host del shadow DOM (<fichaco-page>)...")

        # --- Expandir el acordeón de 'Documentación' ---
        if not expandir_acordeon_documentacion(driver):
            print(" ⚠️ No se pudo expandir el acordeón de 'Documentación'.")
            return

        time.sleep(3)

        # --- Buscar y hacer clic en “Ficha técnica (fecha)” ---
        print(" Buscando botón 'Ficha técnica' dentro del shadow DOM...")
        clicked = driver.execute_script("""
            const page = document.querySelector('fichaco-page');
            const info = page.shadowRoot.querySelector('fichaco-info');
            const main = info.shadowRoot.querySelector('main');
            const accordion = main.querySelector('accordion-component');
            const content = accordion.shadowRoot.querySelector('div.accordion-contenido');
            const blocks = content.querySelectorAll('div.icono-documento');
            let clicked = false;

            blocks.forEach(block => {
                if (block.textContent.toLowerCase().includes('ficha técnica')) {
                    const btn = block.querySelector('bbva-button-action');
                    if (btn) {
                        btn.click();
                        clicked = true;
                    }
                }
            });
            return clicked;
        """)

        if clicked:
            print(" ✅ Click en 'Ficha técnica' realizado correctamente.")
        else:
            print(" ⚠️ No se encontró el botón 'Ficha técnica' para hacer clic.")
            return

        # --- Esperar y detectar el PDF ---
        print(" Esperando apertura/redirección al PDF...")
        time.sleep(5)
        pdf_url = driver.current_url

        if pdf_url.lower().endswith(".pdf"):
            print(f" ✅ PDF detectado: {pdf_url}")
            output_dir = create_output_dir(admin, year, month, scraping)
            safe_fondo = "".join(c for c in fondo if c.isalnum() or c in (" ", "_", "-")).rstrip()
            filename = f"{safe_fondo}.pdf"
            scraping.download_pdf(pdf_url, output_dir=output_dir, filename=filename)
        else:
            print(" ⚠️ No se detectó una URL directa al PDF. Verifica si se abre en nueva pestaña.")

    except Exception as e:
        print(f" ⚠️ Error manejando caso especial BBVA en {fondo}: {type(e).__name__} - {e}")
    finally:
        # Volver al contexto principal
        try:
            driver.switch_to.default_content()
        except:
            pass


def process_result(links, admin, fondo, year, month):
    scraping = Scraping()
    if admin in ADMINS_ESPECIALES:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month, adelantar=True)
    else:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month)


def get_chrome_options():
    """Configura las opciones de Chrome dependiendo del entorno."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    system = platform.system().lower()
    if system == "windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
        else:
            print(" No se encontró Chrome en la ruta esperada, Selenium usará el predeterminado.")
    else:
        options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium-browser")

    return options


def create_output_dir(admin, year, month, scraping_instance):
    admin_clean = "".join(c for c in admin if c.isalnum() or c.isspace())
    admin_words = admin_clean.title().split()
    admin_formatted = "".join(admin_words)

    month_variations = scraping_instance.find_month_variations(month)
    month_numeric = next((m for m in month_variations if m.isdigit() and len(m) == 2), None)
    month_final = month_numeric or month

    output_dir = os.path.join("Fichas tecnicas", f"{admin_formatted}_{year}", month_final)
    os.makedirs(output_dir, exist_ok=True)

    return output_dir


def crawl_with_selenium(url, admin, fondo, year, month):
    options = get_chrome_options()

    if platform.system().lower() == "windows":
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=Service(driver_path), options=options)

    try:
        print(f" Intentando abrir: {url}")
        driver.get(url)

        if "bbva" in admin.lower():
            handle_bbva_case(driver, admin, fondo, year, month)
            return
        
        elements = driver.find_elements(By.TAG_NAME, "a")

        all_links = []
        for el in elements:
            href = el.get_attribute("href")
            text = el.text
            title = el.get_attribute("title")
            if href and ".pdf" in href.lower():
                all_links.append({"href": href, "text": text, "title": title})

        if not all_links:
            print(f" {fondo} ({admin}) - No se encontraron enlaces .pdf en la página")
            return

        links = process_result(all_links, admin, fondo, year, month)

        if links:
            best_link = links[-1]
            print(f" {fondo} ({admin}) - Links PDF encontrados: {len(links)}")
            print("   → Mejor opción:", best_link)

            scraping = Scraping()
            output_dir = create_output_dir(admin, year, month, scraping)

            safe_fondo = "".join(c for c in fondo if c.isalnum() or c in (" ", "_", "-")).rstrip()
            filename = f"{safe_fondo}.pdf"

            scraping.download_pdf(best_link, output_dir=output_dir, filename=filename)
        else:
            print(f" {fondo} ({admin}) - No se encontraron links PDF válidos tras el filtrado AI")

    except Exception as e:
        print(f" Error en {fondo} ({admin}) - {str(e)}")

    finally:
        driver.quit()


def main():
    # --- Leer argumentos desde la consola ---
    if len(sys.argv) < 3:
        print(" Uso: python nombre_archivo.py <mes> <año>")
        print("   Ejemplo: python crawler.py agosto 2025")
        sys.exit(1)

    month = sys.argv[1]
    year = sys.argv[2]

    print(f" Parámetros recibidos → Mes: {month}, Año: {year}")

    extraer = LinkExtractor("bbva.json")
    resultados = extraer.extract_links()

    if resultados:
        print(f" Se encontraron {len(resultados)} fondos para rastrear")
        for admin, fondo, link in resultados:
            crawl_with_selenium(link, admin, fondo, year, month)
    else:
        print(" No se encontraron URLs para rastrear")


if __name__ == "__main__":
    main()