from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import json

class BBVAFondosScraper:
    def __init__(self, headless=False):
        """
        Inicializa el scraper
        :param headless: Si True, ejecuta Chrome sin interfaz gráfica
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        self.documentos_data = []
    
    def ejecutar_javascript(self, script, *args):
        """Ejecuta JavaScript y retorna el resultado"""
        return self.driver.execute_script(script, *args)
    
    def verificar_estructura_iframe(self):
        """
        Verifica la estructura del iframe para debugging
        """
        print("\n" + "="*60)
        print("VERIFICACIÓN DE ESTRUCTURA DEL IFRAME")
        print("="*60)
        
        try:
            # Obtener el HTML del body
            body_html = self.ejecutar_javascript("return document.body.innerHTML;")
            print(f"\n✓ Longitud del HTML del body: {len(body_html)} caracteres")
            
            # Verificar si hay shadow roots
            script = """
                function findShadowRoots(element, depth = 0, maxDepth = 5) {
                    let results = [];
                    if (depth > maxDepth) return results;
                    
                    if (element.shadowRoot) {
                        results.push({
                            tag: element.tagName,
                            depth: depth
                        });
                        
                        // Buscar en el shadow root
                        let children = element.shadowRoot.querySelectorAll('*');
                        children.forEach(child => {
                            results = results.concat(findShadowRoots(child, depth + 1, maxDepth));
                        });
                    }
                    
                    // Buscar en hijos normales
                    if (element.children) {
                        Array.from(element.children).forEach(child => {
                            results = results.concat(findShadowRoots(child, depth + 1, maxDepth));
                        });
                    }
                    
                    return results;
                }
                
                return findShadowRoots(document.body);
            """
            
            shadow_roots = self.ejecutar_javascript(script)
            print(f"✓ Shadow Roots encontrados: {len(shadow_roots)}")
            
            if shadow_roots:
                print("\nElementos con Shadow DOM:")
                for sr in shadow_roots[:10]:  # Mostrar solo los primeros 10
                    print(f"   • <{sr['tag']}> (profundidad: {sr['depth']})")
            
            # Buscar elementos accordion
            print("\n" + "-"*60)
            print("Buscando elementos 'accordion'...")
            
            accordion_script = """
                let accordions = document.querySelectorAll('[class*="accordion"]');
                return Array.from(accordions).map(el => ({
                    tag: el.tagName,
                    className: el.className,
                    id: el.id,
                    text: el.textContent.substring(0, 100)
                }));
            """
            
            accordions = self.ejecutar_javascript(accordion_script)
            print(f"✓ Elementos accordion encontrados: {len(accordions)}")
            
            for acc in accordions[:5]:
                print(f"\n   <{acc['tag']}>")
                print(f"      class: {acc['className']}")
                print(f"      id: {acc['id']}")
                print(f"      texto: {acc['text'][:50]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            return False
    
    def buscar_acordeon_shadow_dom(self):
        """
        Busca el acordeón navegando específicamente por el CELLS-TEMPLATE-PAPER-DRAWER-PANEL
        """
        try:
            print("\n   Buscando en estructura específica del Shadow DOM...")
            
            script = """
            function buscarAcordeonEnEstructura() {
                try {
                    // Paso 1: Encontrar CELLS-TEMPLATE-PAPER-DRAWER-PANEL
                    const panelTemplate = document.querySelector('cells-template-paper-drawer-panel');
                    if (!panelTemplate) {
                        console.log('No se encontró el panel template');
                        return null;
                    }

                    // Paso 2: Buscar el div con clase "accordion"
                    const accordion = panelTemplate.querySelector('.accordion');
                    if (!accordion) {
                        console.log('No se encontró el contenedor accordion');
                        return null;
                    }

                    // Paso 3: Buscar el acordeón de documentación
                    const docAccordion = Array.from(accordion.querySelectorAll('.accordion-item')).find(item => {
                        const titulo = item.querySelector('.accordion-titulo p');
                        return titulo && titulo.textContent.trim() === 'Documentación';
                    });

                    if (!docAccordion) {
                        console.log('No se encontró el acordeón de documentación');
                        return null;
                    }

                    return {
                        encontrado: true,
                        elemento: docAccordion,
                        ruta: 'cells-template-paper-drawer-panel > .accordion > .accordion-item',
                        info: {
                            titulo: 'Documentación',
                            contenido: docAccordion.querySelector('.accordion-contenido')?.textContent || ''
                        }
                    };
                } catch (error) {
                    console.error('Error en búsqueda:', error);
                    return { error: error.toString() };
                }
            }
            
            return buscarAcordeonEnEstructura();
            """
            
            resultado = self.ejecutar_javascript(script)
            
            if resultado.get('error'):
                print(f"   ⚠ Error en la búsqueda: {resultado['error']}")
                return False
                
            if resultado.get('encontrado'):
                print("   ✓ Acordeón encontrado en estructura específica")
                print(f"   • Ruta: {resultado.get('ruta')}")
                info = resultado.get('info', {})
                print(f"   • Título: {info.get('titulo')}")
                return True
            
            print("   ❌ No se encontró el acordeón en la estructura esperada")
            return False
                
        except Exception as e:
            print(f"   ❌ Error buscando en estructura específica: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def expandir_acordeon_especifico(self):
        """
        Expande el acordeón específico de documentación
        """
        try:
            print("\n   Intentando expandir acordeón específico...")
            
            script = """
            function expandirAcordeonDocumentacion() {
                try {
                    // Encontrar el panel template
                    const panelTemplate = document.querySelector('cells-template-paper-drawer-panel');
                    if (!panelTemplate) return false;
                    
                    // Buscar el acordeón de documentación
                    const accordion = panelTemplate.querySelector('.accordion');
                    if (!accordion) return false;
                    
                    const docAccordion = Array.from(accordion.querySelectorAll('.accordion-item')).find(item => {
                        const titulo = item.querySelector('.accordion-titulo p');
                        return titulo && titulo.textContent.trim() === 'Documentación';
                    });
                    
                    if (!docAccordion) return false;
                    
                    // Verificar si ya está expandido
                    const contenido = docAccordion.querySelector('.accordion-contenido');
                    if (contenido && contenido.style.display !== 'none') {
                        console.log('El acordeón ya está expandido');
                        return true;
                    }
                    
                    // Buscar y hacer clic en el botón
                    const boton = docAccordion.querySelector('.accordion-titulo bbva-button-action');
                    if (boton) {
                        boton.click();
                        return true;
                    }
                    
                    return false;
                } catch (error) {
                    console.error('Error expandiendo acordeón:', error);
                    return false;
                }
            }
            
            return expandirAcordeonDocumentacion();
            """
            
            resultado = self.ejecutar_javascript(script)
            
            if resultado:
                print("   ✓ Acordeón expandido correctamente")
                time.sleep(3)  # Dar tiempo para que se expanda
                return True
            else:
                print("   ❌ No se pudo expandir el acordeón específico")
                return False
                
        except Exception as e:
            print(f"   ❌ Error expandiendo acordeón específico: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape_fondo(self, url):
        """
        Extrae información del fondo desde la página con iframe
        """
        try:
            print("=" * 60)
            print("INICIANDO SCRAPING DE BBVA FONDOS")
            print("=" * 60)
            
            # Navegar a la página principal
            print("\n[1/7] Cargando página principal...")
            self.driver.get(url)
            time.sleep(5)  # Mantenemos el tiempo original
            
            # Esperar a que el iframe esté presente
            print("[2/7] Esperando que cargue el iframe...")
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "iframeIsin"))
            )
            print("✓ Iframe encontrado")
            
            # Obtener el src del iframe
            iframe_src = iframe.get_attribute('src')
            print(f"   URL del iframe: {iframe_src}")
            
            # Cambiar al contexto del iframe (esto funcionaba en el código original)
            print("\n[3/7] Cambiando al contexto del iframe...")
            self.driver.switch_to.frame(iframe)
            time.sleep(5)  # Tiempo de espera después de cambiar al iframe
            
            # NUEVO: Verificar estructura
            print("[4/7] Verificando estructura del iframe...")
            self.verificar_estructura_iframe()
            
            # Esperar a que cargue el contenido
            print("\n[5/7] Esperando que cargue el contenido...")
            time.sleep(5)
            
            # Buscar acordeón
            print("[6/7] Buscando acordeón de Documentación...")
            success = self.buscar_acordeon_shadow_dom()
            
            if not success:
                print("\n⚠ No se pudo encontrar el acordeón")
                print("❌ No se pudo acceder al acordeón")
                self.driver.save_screenshot("debug_iframe.png")
                print("✓ Screenshot guardado como 'debug_iframe.png'")
                return None
            
            # Extraer información
            print("\n[7/7] Extrayendo documentos...")
            documentos = self.extraer_documentos()
            
            # Volver al contexto principal
            self.driver.switch_to.default_content()
            
            return documentos
            
        except Exception as e:
            print(f"\n❌ Error general: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("error_general.png")
            return None
    
    def extraer_documentos(self):
        """
        Extrae los documentos usando JavaScript para manejar Shadow DOM profundo
        """
        try:
            print("\n   Extrayendo documentos desde Shadow DOM...")
            
            script = """
                function extraerDocumentosProfundo() {
                    let documentos = [];
                    
                    try {
                        // Paso 1: Navegar a la estructura correcta
                        const panelTemplate = document.querySelector('cells-template-paper-drawer-panel');
                        if (!panelTemplate || !panelTemplate.shadowRoot) return documentos;
                        
                        let entityFunds = panelTemplate.shadowRoot.querySelector('entity-funds-dm');
                        if (!entityFunds) {
                            entityFunds = document.querySelector('entity-funds-dm');
                        }
                        
                        if (!entityFunds || !entityFunds.shadowRoot) return documentos;
                        
                        const docSection = entityFunds.shadowRoot.querySelector('#documentacion') ||
                                         entityFunds.shadowRoot.querySelector('[class*="documentacion"]');
                                         
                        if (!docSection) return documentos;
                        
                        // Paso 2: Buscar categorías de documentos
                        const categorias = docSection.querySelectorAll('.titulos-documentacion');
                        
                        categorias.forEach(categoria => {
                            const nombreCategoria = categoria.textContent.trim();
                            const contenedorDocs = categoria.nextElementSibling;
                            
                            if (contenedorDocs && contenedorDocs.classList.contains('documentos-todos')) {
                                const documentosElements = contenedorDocs.querySelectorAll('.icono-documento');
                                
                                documentosElements.forEach(docElement => {
                                    const docInfo = docElement.querySelector('.documento');
                                    if (docInfo) {
                                        const textoCompleto = docInfo.textContent || '';
                                        const fechaElement = docInfo.querySelector('.letras-grises');
                                        const fecha = fechaElement ? 
                                            fechaElement.textContent.replace(/[()]/g, '').trim() : 
                                            'Sin fecha';
                                        const nombre = textoCompleto.split('(')[0].trim();
                                        
                                        const botonDescarga = docElement.querySelector('bbva-button-action');
                                        const tieneBoton = !!botonDescarga;
                                        
                                        documentos.push({
                                            categoria: nombreCategoria,
                                            nombre: nombre,
                                            fecha: fecha,
                                            descargable: tieneBoton
                                        });
                                    }
                                });
                            }
                        });
                        
                    } catch (error) {
                        console.error('Error extrayendo documentos:', error);
                    }
                    
                    return documentos;
                }
                
                return extraerDocumentosProfundo();
            """
            
            documentos = self.ejecutar_javascript(script)
            
            if documentos and len(documentos) > 0:
                print(f"\n   ✓ Total de documentos encontrados: {len(documentos)}")
                
                # Mostrar resumen por categoría
                categorias = {}
                for doc in documentos:
                    cat = doc['categoria']
                    if cat not in categorias:
                        categorias[cat] = []
                    categorias[cat].append(doc)
                
                print("\n" + "="*60)
                print("DOCUMENTOS EXTRAÍDOS")
                print("="*60)
                
                for cat, docs in categorias.items():
                    print(f"\n📁 {cat} ({len(docs)} documentos)")
                    for doc in docs:
                        icono = "📄" if doc.get('descargable') else "📃"
                        print(f"   {icono} {doc['nombre']} - {doc['fecha']}")
                
                return documentos
            else:
                print("   ⚠ No se encontraron documentos")
                return []
            
        except Exception as e:
            print(f"   ❌ Error extrayendo documentos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def guardar_json(self, documentos, filename="documentos.json"):
        """Guarda la información de los documentos en un archivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documentos, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Información guardada en {filename}")
    
    def cerrar(self):
        """Cierra el navegador"""
        print("\n" + "=" * 60)
        print("Cerrando navegador...")
        self.driver.quit()
        print("✓ Proceso finalizado")
        print("=" * 60)


# Ejemplo de uso
if __name__ == "__main__":
    url = "https://www.bbvaassetmanagement.com/co/fondos/?BBVFDIGCB/Fondo-de-Inversión-Colectiva-Abierto-FONDO-BBVA-DIGITAL"
    
    scraper = BBVAFondosScraper(headless=False)
    
    try:
        documentos = scraper.scrape_fondo(url)
        
        if documentos:
            print("\n" + "=" * 60)
            print("EXTRACCIÓN COMPLETADA CON ÉXITO")
            print("=" * 60)
            
            # Guardar en JSON
            scraper.guardar_json(documentos)
            
            print(f"\n✓ Total: {len(documentos)} documentos extraídos")
            
        else:
            print("\n❌ No se pudieron extraer documentos")
            print("Revisa los screenshots generados para debugging")
            
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en la ejecución: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPresiona Enter para cerrar el navegador...")
        scraper.cerrar()