# itau_scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def get_itau_links(url: str):
    """Abre el fondo de Itau, entra a 'Fichas técnicas' y recorre todas las páginas para extraer los links."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    wait = WebDriverWait(driver, 15)
    todos_los_enlaces = set()

    try:
        print("[INFO] Cargando página:", url)
        driver.get(url)

        # Esperar y hacer clic en “Fichas técnicas”
        print("[INFO] Abriendo la sección de Fichas técnicas...")
        fichas_link = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@title, 'Fichas técnicas')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", fichas_link)
        
        driver.execute_script("arguments[0].click();", fichas_link)
        

        def extraer_enlaces_actuales():
            soup = BeautifulSoup(driver.page_source, "html.parser")
            enlaces = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                
                if href.startswith("/"):
                    href = "https://banco.itau.co" + href
                enlaces.append(href)
            return enlaces

        # Extraer los de la primera página
        todos_los_enlaces.update(extraer_enlaces_actuales())

        # Recorrer las páginas con botón “Siguiente”
        while True:
            try:
                siguiente_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.paginate_button.next")
                ))
                driver.execute_script("arguments[0].scrollIntoView(true);", siguiente_btn)
                driver.execute_script("arguments[0].click();", siguiente_btn)
                
                nuevos = extraer_enlaces_actuales()
                nuevos_enlaces = [e for e in nuevos if e not in todos_los_enlaces]
                if nuevos_enlaces:
                    todos_los_enlaces.update(nuevos_enlaces)
                else:
                    break
            except Exception:
                break

        print(f"[INFO] Total enlaces Itau encontrados: {len(todos_los_enlaces)}")
        return list(sorted(todos_los_enlaces))

    except Exception as e:
        print(f"[ERROR] Ocurrió un problema con Itau: {e}")
        return []
    finally:
        driver.quit()
