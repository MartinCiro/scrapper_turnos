from controller.Config import Config
from controller.utils.Helpers import Helpers
from random import uniform
from os import path, makedirs

class Login(Config):
    """
    Clase encargada de ejecutar el login en EcoDigital usando Playwright.
    Versión específica para ecodigital.emergiacc.com
    """

    def __init__(self) -> None:
        """Constructor de la clase. Hereda de Config e inicializa el navegador."""
        super().__init__()
        self.helper = Helpers()
        self.login_attempts = 0 
        self.max_login_attempts = 3
        
        # URLs específicas de EcoDigital
        self.eco_base_url = "https://ecodigital.emergiacc.com"
        self.eco_login_url = f"{self.eco_base_url}/WebEcoPresencia/Master#/TurnosAsesor"
        
        # DICCIONARIO DE SELECTORES PARA ECODIGITAL
        self.selectors = {
            # =============================================
            # SELECTORES PARA FORMULARIO DE LOGIN
            # =============================================
            "username_input": [
                "//input[@id='UsuarioLogado_Login']",         # Input usuario
                "//input[@name='UsuarioLogado.Login']",       # Input name alternativo
                "//input[contains(@placeholder, 'usuario') or contains(@placeholder, 'Usuario')]", # Placeholder
                "//input[@type='text' and contains(@class, 'usuario')]", # Por clase
            ],
            
            "password_input": [
                "//input[@id='UsuarioLogado_Password']",      # Input password
                "//input[@name='UsuarioLogado.Password']",    # Input name alternativo
                "//input[@type='password']",                  # Input tipo password genérico
                "//input[contains(@placeholder, 'contraseña') or contains(@placeholder, 'password')]", # Placeholder
            ],
            
            "login_button": [
                "//input[@id='btnIniciar']",                  # Botón iniciar sesión
                "//button[@id='btnIniciar']",                 # Botón alternativo
                "//button[contains(@onclick, 'IniciarSesion')]", # Por onclick
                "//button[contains(text(), 'Iniciar Sesión')]", # Por texto
                "//input[@type='submit']",                    # Submit genérico
                "//button[@type='submit']",                   # Submit tipo button
            ],
            
            # =============================================
            # SELECTORES PARA VERIFICAR SESIÓN ACTIVA
            # =============================================
            "logged_in_indicators": [
                "//button[starts-with(@class, 'fc-btnVerCalendarioTurnos-button')]", # Botón principal logueado
                "//div[contains(@class, 'panel-asignacion')]", # Panel de asignación
                "//div[contains(@class, 'turnos-asesor')]",    # Panel de turnos
                "//h3[contains(text(), 'Turnos')]",           # Título Turnos
                "//div[contains(@class, 'user-info')]",       # Información de usuario
                "//span[contains(@class, 'nombre-usuario')]", # Nombre de usuario
                "//a[contains(@href, 'CerrarSesion')]",       # Enlace cerrar sesión
            ],
            
            # =============================================
            # SELECTORES PARA VERIFICAR NO LOGUEADO
            # =============================================
            "not_logged_indicators": [
                "//input[@id='UsuarioLogado_Login']",         # Campo usuario visible
                "//input[@id='UsuarioLogado_Password']",      # Campo password visible
                "//form[contains(@action, 'Login')]",         # Formulario de login
                "//div[contains(@class, 'login-container')]", # Contenedor login
                "//h2[contains(text(), 'Iniciar Sesión')]",   # Título login
            ],
            
            # =============================================
            # SELECTORES PARA LOGOUT
            # =============================================
            "logout_selectors": [
                "//a[contains(@href, 'CerrarSesion')]",       # Enlace cerrar sesión
                "//button[contains(text(), 'Cerrar Sesión')]", # Botón cerrar sesión
                "//button[contains(@onclick, 'Logout')]",     # Por onclick
                "//li[contains(text(), 'Salir')]",            # Opción salir
            ],
            
            # =============================================
            # SELECTORES PARA ERRORES DE LOGIN
            # =============================================
            "error_messages": [
                "//div[contains(text(), 'Usuario o contraseña incorrectos')]", # Error credenciales
                "//div[contains(text(), 'Error al iniciar sesión')]",         # Error genérico
                "//div[@class='alert alert-danger']",                         # Alertas de error
                "//span[contains(@class, 'error-message')]",                  # Mensajes error
                "//div[contains(@class, 'validation-summary-errors')]",       # Errores validación
            ],
            
            # =============================================
            # SELECTORES PARA ELEMENTOS DESPUÉS DEL LOGIN
            # =============================================
            "post_login_elements": [
                "//div[@id='main-container']",                # Contenedor principal
                "//nav[@role='navigation']",                  # Navegación
                "//div[contains(@class, 'main-content')]",    # Contenido principal
            ]
        }

    def _log(self, message: str, type: str = "info"):
        """Método de logging unificado"""
        timestamp = self.helper.get_current_time()
        log_message = f"[{timestamp}] {message}"
        
        if type == "error":
            print(f"❌ {log_message}")
        elif type == "warning":
            print(f"⚠️  {log_message}")
        elif type == "success":
            print(f"✅ {log_message}")
        else:
            print(f"🔧 {log_message}")

    def _find_element_by_xpath_list(self, xpath_list: list, timeout: int = 5000, state: str = "visible"):
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

    def _check_any_xpath_exists(self, xpath_list: list, timeout: int = 3000) -> bool:
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

    def is_logged_in(self, timeout: int = 8000) -> bool:
        """
        Verifica si ya estamos logueados en EcoDigital
        """
        try:
            # Verificar el botón principal de calendario de turnos
            if self._check_any_xpath_exists([self.selectors["logged_in_indicators"][0]], 3000):
                self._log("✅ Detectado botón de calendario de turnos - SESIÓN ACTIVA", "success")
                return True
            
            # Verificar otros indicadores de sesión activa
            elements_found = 0
            required_elements = 2
            
            for xpath in self.selectors["logged_in_indicators"][1:5]:  # Primeros 5 indicadores
                try:
                    element = self.page.wait_for_selector(f"xpath={xpath}", timeout=2000, state="visible")
                    if element:
                        elements_found += 1
                        if elements_found >= required_elements:
                            self._log(f"✅ Sesión activa confirmada ({elements_found} indicadores)", "success")
                            return True
                except:
                    continue
            
            # Verificar si hay formulario de login visible (NO logueado)
            if self._check_any_xpath_exists(self.selectors["not_logged_indicators"], 2000):
                self._log("❌ Formulario de login visible - NO LOGUEADO", "info")
                return False
            
            # Verificar URL actual
            current_url = self.page.url.lower()
            if "loginsesion" in current_url or "login" in current_url:
                self._log("❌ URL indica página de login", "info")
                return False
            
            # Última verificación: presencia de elementos post-login
            if elements_found >= 1 and self._check_any_xpath_exists(self.selectors["post_login_elements"], 2000):
                self._log("✅ Confirmado por elementos post-login", "success")
                return True
            
            self._log("❌ No se pudo determinar estado de sesión", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando sesión: {str(e)}", "error")
            return False

    def fill_login_form(self) -> bool:
        """
        Llena el formulario de login de EcoDigital
        """
        try:
            self._log("📝 Buscando formulario de login...")
            
            # Esperar a que cargue la página
            self.page.wait_for_load_state("domcontentloaded")
            self.helper.human_like_delay(1, 2)
            
            # BUSCAR Y LLENAR CAMPO USUARIO
            username_input = self._find_element_by_xpath_list(
                self.selectors["username_input"], 
                timeout=8000
            )
            if not username_input:
                self._log("❌ No se pudo encontrar el campo de usuario", "error")
                return False
            
            # Limpiar y escribir usuario
            username_input.click(click_count=3)
            username_input.press("Backspace")
            self.helper.human_like_delay(0.5, 1)
            
            for char in self.fb_email:  # Reutilizamos la variable de email como usuario
                username_input.type(char, delay=uniform(50, 150))
            self.helper.human_like_delay(1, 2)
            
            # BUSCAR Y LLENAR CAMPO CONTRASEÑA
            password_input = self._find_element_by_xpath_list(
                self.selectors["password_input"], 
                timeout=5000
            )
            if not password_input:
                self._log("❌ No se pudo encontrar el campo de contraseña", "error")
                return False
            
            # Escribir contraseña
            password_input.click()
            self.helper.human_like_delay(0.5, 1)
            
            for char in self.fb_password:  # Reutilizamos la variable de password
                password_input.type(char, delay=uniform(80, 200))
            self.helper.human_like_delay(1, 2)
            
            # BUSCAR Y HACER CLIC EN BOTÓN LOGIN
            login_button = self._find_element_by_xpath_list(
                self.selectors["login_button"], 
                timeout=5000
            )
            if not login_button:
                self._log("❌ No se pudo encontrar el botón de login", "error")
                return False
            
            self._log("🔑 Enviando credenciales...")
            login_button.click()
            
            return True
            
        except Exception as e:
            self._log(f"❌ Error llenando formulario: {str(e)}", "error")
            return False

    def _try_cookies_login(self) -> bool:
        """
        Intenta hacer login usando cookies guardadas
        """
        try:
            if not path.exists(self.cookies_path):
                self._log("📁 No hay archivo de cookies guardadas", "info")
                return False
                
            cookies = self.helper.load_cookies(self.cookies_path)
            if not cookies:
                self._log("📁 Archivo de cookies vacío o inválido", "info")
                return False
                
            self._log(f"🍪 Intentando login con {len(cookies)} cookies...")
            
            # Limpiar cookies existentes y agregar las guardadas
            self.context.clear_cookies()
            self.context.add_cookies(cookies)
            
            # Navegar a EcoDigital
            self.open_url(self.eco_login_url)
            self.page.wait_for_load_state("domcontentloaded")
            self.helper.human_like_delay(3, 5)
            
            # Verificar si el login fue exitoso
            if self.is_logged_in(timeout=8000):
                self._log("✅ Login con cookies exitoso", "success")
                return True
            else:
                self._log("❌ Cookies no válidas o expiradas", "warning")
                return False
            
        except Exception as e:
            self._log(f"❌ Error en login con cookies: {str(e)}", "error")
            return False

    def _save_cookies(self):
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

    def login(self, use_cookies: bool = True) -> bool:
        """
        Login en EcoDigital
        """
        if self.login_attempts >= self.max_login_attempts:
            self._log("🚫 Límite de intentos de login alcanzado", "error")
            return False
            
        self.login_attempts += 1
        self._log(f"🔄 Intentando login ({self.login_attempts}/{self.max_login_attempts})...")
        
        # 1. INTENTAR CON COOKIES
        if use_cookies and self._try_cookies_login():
            return True
        
        # 2. VERIFICAR SI YA ESTAMOS LOGUEADOS
        if self.is_logged_in():
            self._log("✅ Ya hay una sesión activa", "success")
            self._save_cookies()
            return True
        
        # 3. NAVEGAR A ECODIGITAL
        try:
            self._log("🌐 Navegando a EcoDigital...")
            self.open_url(self.eco_login_url)
            self.page.wait_for_load_state("domcontentloaded")
            self.helper.human_like_delay(2, 4)
            
            if self.is_logged_in():
                self._log("✅ Login automático detectado", "success")
                self._save_cookies()
                return True
                
        except Exception as e:
            self._log(f"❌ Error navegando a EcoDigital: {str(e)}", "error")
            return self.login(use_cookies=False)
        
        # 4. LLENAR FORMULARIO
        if not self.fill_login_form():
            return self.login(use_cookies=False)
        
        # 5. ESPERAR RESPUESTA
        self._log("⏳ Esperando respuesta del login...")
        self.page.wait_for_load_state("networkidle", timeout=10000)
        self.helper.human_like_delay(3, 6)
        
        # 6. VERIFICAR ERRORES
        if self._check_any_xpath_exists(self.selectors["error_messages"], 3000):
            self._log("❌ Error de credenciales detectado", "error")
            return False
        
        # 7. VERIFICAR LOGIN EXITOSO
        if self.is_logged_in(timeout=10000):
            self._log("✅ Login exitoso", "success")
            self._save_cookies()
            self.login_attempts = 0
            return True
        else:
            self._log("❌ Login fallido", "error")
            self.helper.human_like_delay(5, 10)
            return self.login(use_cookies=False)

    def logout(self) -> bool:
        """
        Cierra sesión de EcoDigital
        """
        try:
            self._log("🚪 Cerrando sesión de EcoDigital...")
            
            # Buscar elemento de logout
            logout_element = self._find_element_by_xpath_list(
                self.selectors["logout_selectors"], 
                timeout=8000
            )
            
            if logout_element:
                logout_element.click()
                self.helper.human_like_delay(2, 4)
                
                # Verificar logout exitoso
                if self._check_any_xpath_exists(self.selectors["not_logged_indicators"], 5000):
                    self._log("✅ Logout exitoso", "success")
                    return True
            
            self._log("❌ No se pudo completar el logout", "error")
            return False
                
        except Exception as e:
            self._log(f"❌ Error durante logout: {str(e)}", "error")
            return False

    def get_login_status(self) -> dict:
        """
        Obtiene el estado actual del login.
        """
        return {
            "logged_in": self.is_logged_in(),
            "login_attempts": self.login_attempts,
            "max_attempts": self.max_login_attempts,
            "current_url": self.page.url,
            "cookies_available": bool(self.helper.load_cookies(self.cookies_path))
        }

    def debug_selectors(self):
        """
        Debug de los selectores actuales
        """
        try:
            self._log("🔍 Debug de selectores...")
            
            current_url = self.open_url(self.eco_login_url)
            self.page.wait_for_load_state("domcontentloaded")
            
            for category, selectors in self.selectors.items():
                self._log(f"\n📋 {category}:")
                found_count = 0
                for xpath in selectors[:3]:  # Probar solo primeros 3
                    try:
                        element = self.page.wait_for_selector(f"xpath={xpath}", timeout=1000, state="visible")
                        if element:
                            print(f"   ✅ {xpath[:70]}...")
                            found_count += 1
                        else:
                            print(f"   ❌ {xpath[:70]}...")
                    except:
                        print(f"   ❌ {xpath[:70]}...")
                
                self._log(f"   📊 Encontrados: {found_count}/{len(selectors[:3])}")
            
            # Screenshot para referencia
            self.page.screenshot(path="./debug_ecodigital_selectors.png", full_page=False)
            self._log("📸 Screenshot guardado: debug_ecodigital_selectors.png")
            
        except Exception as e:
            self._log(f"❌ Error en debug: {e}", "error")