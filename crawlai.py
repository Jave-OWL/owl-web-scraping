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
    "Progresion",
    "Banco de Occidente Fiduoccidente"
]


def process_result(links, admin, fondo, year, month):
    scraping = Scraping()
    if admin in ADMINS_ESPECIALES:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month, adelantar=True)
    else:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month)


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
    "Progresion",
    "Banco de Occidente Fiduoccidente"
]


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
        #  Local: usar Chrome instalado
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
        else:
            print(" No se encontró Chrome en la ruta esperada, Selenium usará el predeterminado.")
    else:
        #  GitHub Actions o Linux
        options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium-browser")
    
    return options


def crawl_with_selenium(url, admin, fondo, year, month):
    options = get_chrome_options()

    # Usa ChromeDriver distinto en Windows vs GitHub Actions
    if platform.system().lower() == "windows":
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=Service(driver_path), options=options)

    try:
        print("Intentando abrir:", url)
        driver.get(url)

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
            print("   Mejor opción:", best_link)

            scraping = Scraping()
            output_dir = os.path.join("Fichas tecnicas", f"{admin} {year}", month)

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
    extraer = LinkExtractor("FICmanual.xlsx")
    resultados = extraer.extract_links()

    month = "agosto"
    year = "2025"

    if resultados:
        print(f"Se encontraron {len(resultados)} fondos para rastrear")
        for admin, fondo, link in resultados:
            crawl_with_selenium(link, admin, fondo, year, month)
    else:
        print("No se encontraron URLs para rastrear")


if __name__ == "__main__":
    main()



def crawl_with_selenium(url, admin, fondo, year, month):
    options = get_chrome_options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("Intentando abrir:", url)
        driver.get(url)

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
            print("   Mejor opción:", best_link)

            scraping = Scraping()
            output_dir = os.path.join("Fichas tecnicas", f"{admin} {year}", month)

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
    extraer = LinkExtractor("FICmanual.xlsx")
    resultados = extraer.extract_links()

    month = "agosto"
    year = "2025"

    if resultados:
        print(f"Se encontraron {len(resultados)} fondos para rastrear")
        for admin, fondo, link in resultados:
            crawl_with_selenium(link, admin, fondo, year, month)
    else:
        print("No se encontraron URLs para rastrear")


if __name__ == "__main__":
    main()
