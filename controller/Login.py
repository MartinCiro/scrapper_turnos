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

    def is_logged_in(self) -> bool:
        """
        Verifica si ya estamos logueados en EcoDigital
        """
        try:
            # Verificar el botón principal de calendario de turnos
            if self.check_any_xpath_exists([self.selectors["logged_in_indicators"][0]], 3000):
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
            if self.check_any_xpath_exists(self.selectors["username_input"], 2000):
                self._log("❌ Formulario de login visible - NO LOGUEADO", "info")
                return False
            
            # Verificar URL actual
            current_url = self.page.url.lower()
            if "loginsesion" in current_url or "login" in current_url:
                self._log("❌ URL indica página de login", "info")
                return False
            
            # Última verificación: presencia de elementos post-login
            if elements_found >= 1 and self.check_any_xpath_exists(self.selectors["post_login_elements"], 2000):
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
            username_input = self.find_element_by_xpath_list(
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
            
            for char in self.user_eco:  # Reutilizamos la variable de email como usuario
                username_input.type(char, delay=uniform(50, 150))
            self.helper.human_like_delay(1, 2)
            
            # BUSCAR Y LLENAR CAMPO CONTRASEÑA
            password_input = self.find_element_by_xpath_list(
                self.selectors["password_input"], 
                timeout=5000
            )
            if not password_input:
                self._log("❌ No se pudo encontrar el campo de contraseña", "error")
                return False
            
            # Escribir contraseña
            password_input.click()
            self.helper.human_like_delay(0.5, 1)
            
            for char in self.ps_eco:  # Reutilizamos la variable de password
                password_input.type(char, delay=uniform(80, 200))
            self.helper.human_like_delay(1, 2)
            
            # BUSCAR Y HACER CLIC EN BOTÓN LOGIN
            login_button = self.find_element_by_xpath_list(
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
            self.open_url(self.eco_turnos_url)
            self.page.wait_for_load_state("domcontentloaded")
            self.helper.human_like_delay(3, 5)
            
            # Verificar si el login fue exitoso
            if self.is_logged_in():
                self._log("✅ Login con cookies exitoso", "success")
                return True
            else:
                self._log("❌ Cookies no válidas o expiradas", "warning")
                return False
            
        except Exception as e:
            self._log(f"❌ Error en login con cookies: {str(e)}", "error")
            return False

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
            self.save_cookies()
            return True
        
        # 3. NAVEGAR A ECODIGITAL
        try:
            if self.is_logged_in():
                self.open_url(self.eco_turnos_url)
            else:
                self.open_url(self.eco_login_url)
            
            self.page.wait_for_load_state("domcontentloaded")
            self.helper.human_like_delay(2, 4)
            
            if self.is_logged_in():
                self.save_cookies()
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
        if self.check_any_xpath_exists(self.selectors["error_messages"], 3000):
            self._log("❌ Error de credenciales detectado", "error")
            return False
        
        # 7. VERIFICAR LOGIN EXITOSO
        if self.is_logged_in():
            self._log("✅ Login exitoso", "success")
            self.save_cookies()
            self.login_attempts = 0
            return True
        else:
            self._log("❌ Login fallido", "error")
            self.helper.human_like_delay(5, 10)
            return self.login(use_cookies=False)

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