from requests import Session, exceptions
from json import load, dump
from time import sleep
from datetime import datetime
from controller.Config import Config
from random import uniform

class Login(Config):
    """
    Clase encargada de ejecutar el login en EcoDigital usando HTTP requests.
    Versión específica para ecodigital.emergiacc.com
    """

    def __init__(self) -> None:
        """Constructor de la clase. Hereda de Config"""
        super().__init__()
        self.session = Session()
        self.login_attempts = 0 
        self.max_login_attempts = 3
        
        # Configurar headers base similares al curl
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        })

    def _log(self, message: str, type: str = "info"):
        """Método de logging unificado"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if type == "error":
            print(f"❌ {log_message}")
        elif type == "warning":
            print(f"⚠️  {log_message}")
        elif type == "success":
            print(f"✅ {log_message}")
        else:
            print(f"🔧 {log_message}")

    def _human_like_delay(self, min_seconds: float, max_seconds: float):
        """Simula delay humano entre requests"""
        delay = uniform(min_seconds, max_seconds)
        sleep(delay)

    def _get_login_payload(self) -> dict:
        """Genera el payload para el login"""
        return {
            'DominioLoginAD': '',
            'UsuarioLogado.Login': self.user_eco,
            'UsuarioLogado.Password': self.ps_eco,
            'IniciarSesionAD': 'false'
        }

    def _try_cookies_login(self) -> bool:
        """
        Intenta hacer login usando cookies guardadas específicas del usuario
        """
        try:
            from os import path
            if not path.exists(self.cookies_path):
                self._log(f"📁 No hay cookies guardadas para usuario: {self.user_eco}", "info")
                return False
                
            with open(self.cookies_path, 'r') as f:
                cookies = load(f)
            
            if not cookies:
                self._log("📁 Archivo de cookies vacío o inválido", "info")
                return False
            
            # Cargar cookies en la sesión
            self.session.cookies.clear()
            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'],
                    domain=cookie.get('domain', ''),
                    path=cookie.get('path', '/')
                )
            
            # Verificar si las cookies son válidas haciendo un request
            response = self.session.get(self.eco_turnos_url, timeout=self.timeout)
            
            if response.status_code == 200 and self._is_logged_in_response(response):
                self._log(f"✅ Login con cookies exitoso para {self.user_eco}", "success")
                return True
            else:
                self._log("❌ Cookies no válidas o expiradas", "warning")
                return False
            
        except Exception as e:
            self._log(f"❌ Error en login con cookies: {str(e)}", "error")
            return False

    def _is_logged_in_response(self, response) -> bool:
        """
        Verifica si la respuesta indica que estamos logueados
        """
        try:
            content = response.text.lower()
            
            # Indicadores de sesión activa
            logged_in_indicators = [
                'fc-btnvercalendarioturnos-button',
                'turnosasesor',
                'master#'
            ]
            
            # Indicadores de NO estar logueado
            logged_out_indicators = [
                'usuariologado_login',
                'usuariologado_password',
                'iniciarsesion'
            ]
            
            # Verificar si hay indicadores de sesión activa
            login_count = sum(1 for indicator in logged_in_indicators if indicator in content)
            
            # Verificar si hay formulario de login
            logout_count = sum(1 for indicator in logged_out_indicators if indicator in content)
            
            # Si hay más indicadores de login que logout, estamos logueados
            return login_count > logout_count
            
        except Exception as e:
            self._log(f"❌ Error verificando respuesta: {str(e)}", "error")
            return False

    def login(self, use_cookies: bool = True) -> bool:
        """
        Login en EcoDigital mediante HTTP requests
        """
        if self.login_attempts >= self.max_login_attempts:
            self._log("🚫 Límite de intentos de login alcanzado", "error")
            return False
            
        self.login_attempts += 1
        
        # 1. INTENTAR CON COOKIES
        if use_cookies and self._try_cookies_login():
            return True
        
        try:
            # 2. HACER GET INICIAL PARA OBTENER COOKIES DE SESIÓN
            self._log("🌐 Obteniendo cookies de sesión...")
            initial_response = self.session.get(
                self.eco_login_url, 
                timeout=self.timeout
            )
            
            if initial_response.status_code != 200:
                self._log(f"❌ Error en GET inicial: {initial_response.status_code}", "error")
                return False
            
            self._human_like_delay(1, 2)
            
            # 3. VERIFICAR SI YA ESTAMOS LOGUEADOS
            if self._is_logged_in_response(initial_response):
                self._log("✅ Ya hay una sesión activa", "success")
                self.save_cookies()
                return True
            
            # 4. PREPARAR Y ENVIAR DATOS DE LOGIN
            self._log("🔑 Enviando credenciales...")
            
            payload = self._get_login_payload()
            
            # Headers específicos para el POST
            post_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self.eco_base_url,
                'Referer': self.eco_login_url,
                'Cache-Control': 'max-age=0'
            }
            
            login_response = self.session.post(
                self.eco_login_url,
                data=payload,
                headers=post_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            self._human_like_delay(2, 4)
            
            # 5. VERIFICAR RESPUESTA DEL LOGIN
            if login_response.status_code != 200:
                self._log(f"❌ Error en POST de login: {login_response.status_code}", "error")
                return False
            
            # 6. VERIFICAR SI EL LOGIN FUE EXITOSO
            if self._is_logged_in_response(login_response):
                self._log("✅ Login exitoso", "success")
                self.save_cookies()
                self.login_attempts = 0
                return True
            else:
                # Buscar mensaje de error específico
                if 'usuario o contraseña incorrectos' in login_response.text.lower():
                    self._log("❌ Credenciales incorrectas", "error")
                    return False
                
                self._log("❌ Login fallido - Respuesta inesperada", "error")
                self._log(f"   Status Code: {login_response.status_code}", "info")
                self._log(f"   URL final: {login_response.url}", "info")
                return False
                
        except exceptions.Timeout:
            self._log("❌ Timeout en la conexión", "error")
            return self.login(use_cookies=False)
        except exceptions.ConnectionError:
            self._log("❌ Error de conexión", "error")
            return self.login(use_cookies=False)
        except Exception as e:
            self._log(f"❌ Error en login: {str(e)}", "error")
            return False

    def save_cookies(self):
        """Guarda las cookies de la sesión actual"""
        try:
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                    'httponly': cookie.has_nonstandard_attr('HttpOnly')
                })
            
            with open(self.cookies_path, 'w') as f:
                dump(cookies, f, indent=2)
            
            self._log(f"💾 Cookies guardadas en: {self.cookies_path}", "success")
            
        except Exception as e:
            self._log(f"❌ Error guardando cookies: {str(e)}", "error")

    def get_session(self):
        """Retorna la sesión actual para hacer requests adicionales"""
        return self.session