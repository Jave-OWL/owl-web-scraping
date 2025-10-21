import os
import sys
import platform
from pydantic import BaseModel
from Extraer import LinkExtractor
from Scraping import Scraping
from playwright.sync_api import sync_playwright

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


def process_result(links, admin, fondo, year, month):
    scraping = Scraping()
    if admin in ADMINS_ESPECIALES:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month, adelantar=True)
    else:
        return scraping.filter_links_with_ai(links, admin, fondo, year, month)


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


def crawl_with_playwright(url, admin, fondo, year, month):
    print(f"Iniciando Playwright para {fondo} ({admin})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080"
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080}
        )

        page = context.new_page()

        try:
            print("Intentando abrir:", url)
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            anchors = page.locator("a")
            all_links = []
            count = anchors.count()

            for i in range(count):
                href = anchors.nth(i).get_attribute("href")
                text = anchors.nth(i).inner_text() or ""
                title = anchors.nth(i).get_attribute("title") or ""
                if href and ".pdf" in href.lower():
                    all_links.append({"href": href, "text": text, "title": title})

            if not all_links:
                print(f" {fondo} ({admin}) - No se encontraron enlaces .pdf en la página")
                return

            links = process_result(all_links, admin, fondo, year, month)

            if links:
                best_link = links[-1]
                #print(f" {fondo} ({admin}) - Links PDF encontrados: {len(links)}")
                print("   Mejor opción:", best_link)

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
            browser.close()


def main():
    extraer = LinkExtractor("FICmanual.xlsx")
    resultados = extraer.extract_links()

    month = "agosto"
    year = "2025"

    if resultados:
        print(f"Se encontraron {len(resultados)} fondos para rastrear")
        for admin, fondo, link in resultados:
            crawl_with_playwright(link, admin, fondo, year, month)
    else:
        print("No se encontraron URLs para rastrear")


if __name__ == "__main__":
    main()