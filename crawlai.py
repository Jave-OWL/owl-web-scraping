import os
import sys
from pydantic import BaseModel
from Extraer import LinkExtractor
from Scraping import Scraping
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class Url(BaseModel):
    url: str


__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")
result_counter = 0

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)


def process_result(links, admin, fondo, year, month):
    scraping = Scraping()
    return scraping.filter_links_with_ai(links, admin, fondo, year, month)


def crawl_with_selenium(url, admin, fondo, year, month):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        print("Intentando abrir:", url)
        driver.get(url)

        elements = driver.find_elements(By.TAG_NAME, "a")

        all_links = []
        for el in elements:
            href = el.get_attribute("href")
            text = el.text
            title = el.get_attribute("title")

            if href:
                all_links.append({
                    "href": href,
                    "text": text,
                    "title": title
                })

        links = process_result(all_links, admin, fondo, year, month)
        if links:
            best_link = links[-1]
            print(f" {fondo} ({admin}) - Links encontrados: {len(links)}")
            print("   Mejor opción:", best_link)

            # ----  Descargar con Scraping ----
            scraping = Scraping()

            # Construir carpeta: Fichas tecnicas/{admin} {año}/{mes}/
            output_dir = os.path.join("Fichas tecnicas", f"{admin} {year}", month)

            # Nombre de archivo: fondo.pdf (limpiando caracteres peligrosos)
            safe_fondo = "".join(c for c in fondo if c.isalnum() or c in (" ", "_", "-")).rstrip()
            filename = f"{safe_fondo}.pdf"

            scraping.download_pdf(best_link, output_dir=output_dir, filename=filename)

        else:
            print(f" {fondo} ({admin}) - No se encontraron links en la página")

    except Exception as e:
        print(f" Error en {fondo} ({admin}) - {str(e)}")

    finally:
        driver.quit()


def main():
    extraer = LinkExtractor("FICmanual.xlsx")
    resultados = extraer.extract_links()
    # month, year = extraer.extract_month_year()

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
