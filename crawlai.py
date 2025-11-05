import os
import sys
import requests
import platform
import time
from pydantic import BaseModel
from Extraer import LinkExtractor
from Scraping import Scraping
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from itau_scraper import get_itau_links
from playwright.sync_api import sync_playwright

class Url(BaseModel):
    url: str

location = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(location, "output")
result_counter = 0

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

ADMINS_ESPECIALES = []


def process_result(links, admin, fondo, year, month):
    scraping = Scraping()
    if admin in ADMINS_ESPECIALES:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month, adelantar=True)
    else:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month)


def get_chrome_options(download_dir=None):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    if download_dir:
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }
        options.add_experimental_option("prefs", prefs)

    system = platform.system().lower()
    if system == "windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
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
    is_itau = admin.lower().strip() == "itau"
    headless_mode = not is_itau
    options = get_chrome_options()

    if not headless_mode:
        print(" Ejecutando sin modo headless (Itau detectado).")
        try:
            options.arguments.remove("--headless=new")
        except ValueError:
            pass

    if not is_itau:
        if platform.system().lower() == "windows":
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        else:
            driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=Service(driver_path), options=options)
    else:
        driver = None

    try:
        print(f" Intentando abrir: {url}")

        all_links = []

        if is_itau:
            print("[INFO] Activando scraper especial para Itau...")
            itau_links = get_itau_links(url)
            for href in itau_links:
                all_links.append({"href": href, "text": "Fichas técnicas Itau", "title": "Ficha Itau"})
        else:
            driver.get(url)
            elements = driver.find_elements(By.TAG_NAME, "a")
            for el in elements:
                href = el.get_attribute("href")
                text = el.text
                title = el.get_attribute("title")
                if href and ".pdf" in href.lower():
                    all_links.append({"href": href, "text": text, "title": title})

        if not all_links:
            print(f" {fondo} ({admin}) - No se encontraron enlaces en la página")
            return

        links = process_result(all_links, admin, fondo, year, month)
        if not links:
            print(f" {fondo} ({admin}) - No se encontraron links válidos tras el filtrado AI")
            return

        best_link = links[-1]
        print(f" {fondo} ({admin}) - Links encontrados: {len(links)}")
        print("   → Mejor opción:", best_link)

        scraping = Scraping()
        output_dir = create_output_dir(admin, year, month, scraping)
        safe_fondo = "".join(c for c in fondo if c.isalnum() or c in (" ", "_", "-")).rstrip()
        filename = f"{safe_fondo}.pdf"
        filepath = os.path.join(output_dir, filename)

        # --- Descargar PDF ---
        if is_itau:
            print("[INFO] Descargando PDF (Itaú) usando Playwright...")

            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(accept_downloads=True)
                    page = context.new_page()

                    page.goto(best_link, wait_until="networkidle")
                    print(f" Abriendo PDF: {best_link}")

                    with page.expect_download() as download_info:
                        # Forzar impresión (algunos visores generan descarga)
                        page.evaluate("window.print()")

                    download = download_info.value
                    download.save_as(filepath)

                    print(f" ✅ Archivo guardado correctamente en: {filepath}")
                    browser.close()

            except Exception as e:
                print(f" Error al descargar con Playwright (Itaú): {e}")

        else:
            scraping.download_pdf(best_link, output_dir=output_dir, filename=filename)

    except Exception as e:
        print(f" Error en {fondo} ({admin}) - {str(e)}")

    finally:
        if driver:
            driver.quit()


def main():
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