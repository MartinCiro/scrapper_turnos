from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from controller.utils.Helpers import Helpers
from typing import List
from random import choice, uniform
from time import sleep
from dotenv import load_dotenv
from os import getenv, path, makedirs
load_dotenv()

class BasePlaywright:
    _instance = None  # Para implementar patrón singleton
    
    def __new__(cls, *args, **kwargs):
        """Implementa patrón singleton para evitar múltiples instancias"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.helper = Helpers()
        
        if getattr(BasePlaywright, "_initialized", False):
            self.playwright = BasePlaywright.playwright
            self.browser = BasePlaywright.browser
            self.context = BasePlaywright.context
            self.page = BasePlaywright.page
            return
        
        # Configuración inicial
        self.headless = getenv("HEADLESS", "False").lower() in ("true", "1", "yes")
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self._launch_browser()
            self.context = self._create_context()
            self.page = self.context.new_page()
            self._apply_stealth_configurations()
            
            BasePlaywright.playwright = self.playwright
            BasePlaywright.browser = self.browser
            BasePlaywright.context = self.context
            BasePlaywright.page = self.page
            BasePlaywright._initialized = True
            
        except Exception as e:
            raise Exception(f"No se pudo iniciar Playwright: {str(e)}")

    def _launch_browser(self):
        """Lanza el navegador Chromium con configuraciones stealth"""
        return self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ]
        )

    def _create_context(self):
        return self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent=choice(self.user_agents),
            locale='es-CO',
            timezone_id='America/Bogota',
            geolocation={"latitude": 4.7110, "longitude": -74.0721},
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            }
        )

    def _apply_stealth_configurations(self):
        """Aplica configuraciones anti-detección"""
        self.page.add_init_script("""
            // Eliminar webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override the plugins property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en'],
            });
            
            // Mock Chrome runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Remove automation traces
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    def open_url(self, url: str, tab_index: int = None):
        """
        Abre una URL en una pestaña específica o en la actual.
        Args:
            url: URL a abrir
            tab_index: Índice de la pestaña (0-based). Si es None, usa la actual.
        """
        if not self.is_browser_alive():
            self.__init__()  # Recrear instancia si el navegador murió
            
        if tab_index is not None:
            pages = self.context.pages
            if len(pages) <= tab_index:
                new_page = self.context.new_page()
                self._apply_stealth_to_page(new_page)
                new_page.bring_to_front()
            else:
                pages[tab_index].bring_to_front()
            self.page = self.context.pages[tab_index]
        
        self.page.goto(url, wait_until="networkidle")
        self.espera_aleatoria(2, 4)

    def _apply_stealth_to_page(self, page):
        """Aplica configuraciones stealth a una página específica"""
        page.set_extra_http_headers({
            'User-Agent': choice(self.user_agents),
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })

    def is_browser_alive(self):
        """Verifica si el navegador sigue activo"""
        try:
            return hasattr(self, 'browser') and self.browser.is_connected()
        except:
            return False

    def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Espera a que un elemento esté presente en el DOM"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def wait_for_visible(self, selector: str, timeout: int = 10000):
        """Espera a que un elemento sea visible"""
        try:
            element = self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return element
        except PlaywrightTimeoutError:
            return None

    def wait_clickable(self, selector: str, timeout: int = 10000):
        """Espera a que un elemento sea clickeable"""
        try:
            element = self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            # Verificar que no esté deshabilitado
            is_disabled = element.get_attribute("disabled")
            if is_disabled:
                raise PlaywrightTimeoutError("Element is disabled")
            return element
        except PlaywrightTimeoutError:
            return None

    def send_keys(self, selector: str, keys: str, clear: bool = True, delay: float = 0.1):
        """
        Envía texto a un elemento con comportamiento humano
        """
        try:
            element = self.wait_for_visible(selector)
            if not element:
                return False
            
            if clear:
                element.click(click_count=3)  # Selecciona todo
                self.page.keyboard.press("Backspace")
                self.espera_aleatoria(0.1, 0.3)
            
            # Escribir con delays aleatorios
            for char in keys:
                element.type(char, delay=uniform(delay, delay * 2))
                
            return True
        except Exception as e:
            print(f"Error en send_keys: {str(e)}")
            return False

    def handle_link_element(self, selector: str, action: str = "click", tab_index: int = 0):
        """
        Maneja elementos de tipo enlace de forma segura
        """
        try:
            # Cambiar a la pestaña correcta
            pages = self.context.pages
            if tab_index < len(pages):
                self.page = pages[tab_index]
                self.page.bring_to_front()
            
            element = self.wait_for_visible(selector)
            if not element:
                return False if action != "get_text" and action != "get_href" else None
            
            if action == "verify":
                return element.is_visible()
                
            elif action == "click":
                try:
                    element.click()
                    return True
                except Exception as e:
                    # Fallback con JavaScript
                    self.page.evaluate("element => element.click()", element)
                    return True
                    
            elif action == "get_text":
                try:
                    return element.text_content().strip()
                except:
                    return None
                    
            elif action == "get_href":
                try:
                    return element.get_attribute("href")
                except:
                    return None
                    
            return True
            
        except Exception as e:
            print(f"Error en handle_link_element: {str(e)}")
            return False if action != "get_text" and action != "get_href" else None

    def safe_click(self, selector: str, tab_index: int = 0):
        """Click seguro que previene comportamientos no deseados"""
        try:
            pages = self.context.pages
            if tab_index < len(pages):
                self.page = pages[tab_index]
                self.page.bring_to_front()

            element = self.wait_clickable(selector)
            if not element:
                return False

            # Scroll al elemento
            self.page.evaluate("element => element.scrollIntoView({block: 'center'})", element)
            
            # Click con JavaScript
            self.page.evaluate("""
                element => {
                    element.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                    });
                    element.click();
                }
            """, element)
            
            return True
        except Exception as e:
            print(f"Error en safe_click: {str(e)}")
            return False

    def click(self, selector: str, tab_index: int = 0) -> bool:
        """Método click robusto"""
        try:
            pages = self.context.pages
            if tab_index < len(pages):
                self.page = pages[tab_index]
                self.page.bring_to_front()

            element = self.wait_clickable(selector)
            if not element:
                return False

            # Scroll y click
            self.page.evaluate("element => element.scrollIntoView({block: 'center', behavior: 'instant'})", element)
            element.click()
            
            return True
            
        except Exception as e:
            print(f"Error en click: {str(e)}")
            return False

    def wait_for_new_tab(self, timeout: int = 10000):
        """Espera a que se abra una nueva pestaña"""
        try:
            original_pages = len(self.context.pages)
            self.page.wait_for_event("popup", timeout=timeout)
            return len(self.context.pages) > original_pages
        except PlaywrightTimeoutError:
            return False

    def switch_to_new_tab(self, selector: str, close_current_tab: bool = False):
        """Abre una nueva pestaña y cambia el foco a ella"""
        try:
            original_pages = self.context.pages.copy()
            
            # Abrir nueva pestaña
            with self.context.expect_page(timeout=10000) as new_page_info:
                self.click(selector)
            
            new_page = new_page_info.value
            self.page = new_page
            
            if close_current_tab and original_pages:
                original_pages[0].close()
                
            return original_pages[0] if original_pages else None
            
        except Exception as e:
            print(f"Error en switch_to_new_tab: {str(e)}")
            return None

    def get_text(self, selector: str, timeout: int = 5000) -> str:
        """Extrae el texto visible de un elemento"""
        try:
            element = self.page.wait_for_selector(selector, timeout=timeout)
            return element.text_content().strip() if element else ""
        except PlaywrightTimeoutError:
            return ""

    def get_elements_attribute(self, selector: str, attribute: str = "src", timeout: int = 5000) -> List[str]:
        """Obtiene una lista única de valores de atributo o texto de elementos"""
        try:
            elements = self.page.query_selector_all(selector)
            valores = []
            
            for element in elements:
                try:
                    if attribute == "text":
                        text_value = element.text_content()
                        if text_value and text_value.strip():
                            valores.append(text_value.strip())
                    else:
                        attr_value = element.get_attribute(attribute)
                        if attr_value:
                            valores.append(attr_value)
                except:
                    continue
            
            # Eliminar duplicados manteniendo orden
            seen = set()
            return [x for x in valores if not (x in seen or seen.add(x))]
                    
        except Exception:
            return []

    def switch_to_frame(self, frame_selector: str, timeout: int = 10000):
        """Cambia al iframe especificado"""
        try:
            self.page.wait_for_selector(frame_selector, timeout=timeout)
            frame = self.page.frame_locator(frame_selector)
            return frame
        except PlaywrightTimeoutError:
            print("No se pudo encontrar el frame")
            return None

    def count_elements(self, selector: str, timeout: int = 5000) -> int:
        """Cuenta cuántos elementos coinciden con el selector"""
        try:
            elements = self.page.query_selector_all(selector)
            return len(elements)
        except:
            return 0

    def espera_aleatoria(self, min_seg: float = 2, max_seg: float = 5):
        """Espera aleatoria entre acciones para simular comportamiento humano"""
        sleep(uniform(min_seg, max_seg))

    def take_screenshot(self, path: str = "screenshot.png", full_page: bool = False):
        """Toma una captura de pantalla"""
        try:
            self.page.screenshot(path=path, full_page=full_page)
            return True
        except:
            return False

    def save_cookies(self):
        """Guarda las cookies de la sesión actual"""
        try:
            cookies_dir = path.dirname(self.cookies_path)
            if not path.exists(cookies_dir):
                makedirs(cookies_dir, exist_ok=True)
            
            cookies = self.context.cookies()
            if cookies:
                self.helper.backup_cookies(cookies, self.cookies_path)
                self._log(f"✅ {len(cookies)} cookies guardadas", "success")
        except Exception as e:
            self._log(f"❌ Error guardando cookies: {str(e)}", "error")
        
    def find_element_by_xpath_list(self, xpath_list: list, timeout: int = 5000, state: str = "visible"):
        """
        Busca un elemento probando una lista de XPath en orden
        """
        for xpath in xpath_list:
            try:
                element = self.page.wait_for_selector(f"xpath={xpath}", timeout=timeout, state=state)
                if element:
                    self._log(f"✅ Elemento encontrado: {xpath[:50]}...", "info")
                    return element
            except:
                continue
        return None
    
    def check_any_xpath_exists(self, xpath_list: list, timeout: int = 3000) -> bool:
        """
        Verifica si ALGÚN XPath de la lista existe en la página
        """
        for xpath in xpath_list:
            try:
                element = self.page.wait_for_selector(f"xpath={xpath}", timeout=timeout, state="visible")
                if element:
                    return True
            except:
                continue
        return False

    def __del__(self):
        """Limpieza segura al destruir la instancia"""
        try:
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
        except:
            pass