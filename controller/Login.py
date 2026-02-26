from requests import Session, exceptions
from json import load, dump
from datetime import datetime
from re import sub

class Login:
    """
    Clase corregida para manejo robusto de sesión y Cloudflare.
    """

    def __init__(self, config):  
        super().__init__()  
        self.config = config  
        self.session = Session()
        
        # 🔑 HEADERS BASE (sin espacios extra al final)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            # ⚠️ ESPACIOS AL FINAL - ¡CRÍTICOS PARA CLOUDFLARE!
            'Origin': f'{self.config.eco_base_url}  ',  
            'Referer': f'{self.config.eco_login_url}  ',  
        })

    def _get_login_payload(self, request_verification_token: str = None) -> dict:
        payload = {
            'DominioLoginAD': '',
            'UsuarioLogado.Login': self.config.user_eco,  
            'UsuarioLogado.Password': self.config.ps_eco,  
            'IniciarSesionAD': 'false'
        }
        # Agregar token CSRF si está disponible
        if request_verification_token:
            payload['__RequestVerificationToken'] = request_verification_token
        return payload

    def _extract_csrf_token(self, html: str) -> str:
        """Extrae token __RequestVerificationToken del HTML"""
        patterns = [
            r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"',
            r'value="([^"]+)"\s+name="__RequestVerificationToken"\s+type="hidden"',
            r'__RequestVerificationToken\s*=\s*["\']([^"\']+)["\']'
        ]
        for pattern in patterns:
            match = search(pattern, html)
            if match:
                return match.group(1)
        return None

    def login(self, use_cookies: bool = True) -> bool:
        """
        Login con manejo robusto de sesión y Cloudflare
        """
        self.config.log.inicio_proceso("LOGIN ECO")  

        try:
            self.config.log.proceso("Intentando login")  

            # 1. Intentar con cookies
            if use_cookies:
                self.config.log.proceso("Intentando login con cookies")  
                if self._try_cookies_login():
                    self.config.log.comentario("INFO", "Login exitoso usando cookies")  
                    self.config.log.fin_proceso("LOGIN ECO")  
                    return True

            # 2. GET inicial
            self.config.log.proceso("GET inicial para obtener cookies Cloudflare")  

            login_url_con_espacios = f'{self.config.eco_login_url}  '  

            # 2. GET inicial para obtener cookies y CSRF token
            self.log.proceso("GET inicial para obtener cookies y token CSRF")
            
            response = self.session.get(
                login_url_con_espacios,
                timeout=self.config.timeout,  
                allow_redirects=True
            )

            self.config.log.comentario("INFO", f"Status GET inicial: {response.status_code}")  

            if response.status_code == 403:
                self.config.log.error("Cloudflare bloqueó la petición (403)", "GET inicial")  
                self.config.log.fin_proceso("LOGIN ECO")  
                return False

            if response.status_code != 200:
                self.config.log.error(f"Error en GET inicial: {response.status_code}", "GET inicial")  
                self.config.log.fin_proceso("LOGIN ECO")  
                return False

            # 3. POST login
            self.config.log.proceso("Enviando credenciales")  

            # 4. POST login con payload correcto
            self.log.proceso("Enviando credenciales")
            payload = self._get_login_payload(csrf_token)

            login_response = self.session.post(
                self.eco_login_url,
                data=payload,
                timeout=self.config.timeout,  
                allow_redirects=True
            )

            if login_response.status_code == 403:
                self.config.log.error("Cloudflare bloqueó el POST (403)", "POST login")  
                self.config.log.fin_proceso("LOGIN ECO")  
                return False

            if "Usuario o contraseña incorrectos" in login_response.text:
                self.config.log.error("Credenciales incorrectas", "POST login")  
                self.config.log.fin_proceso("LOGIN ECO")  
                return False

            if self._is_logged_in_response(login_response):
                self.config.log.comentario("SUCCESS", "Login exitoso")  
                self.save_cookies()
                self.config.log.fin_proceso("LOGIN ECO")  
                return True

            self.config.log.error("Login fallido (respuesta inesperada)", "POST login")  
            self.config.log.fin_proceso("LOGIN ECO")  
            return False

        except exceptions.Timeout:
            self.config.log.error("Timeout en la conexión", "LOGIN")  
            self.config.log.fin_proceso("LOGIN ECO")  
            return False
        except Exception as e:
            self.config.log.error(str(e), "LOGIN")  
            self.config.log.fin_proceso("LOGIN ECO")  
            return False

    def _is_logged_in_response(self, response) -> bool:
        """Verifica si la respuesta indica login exitoso"""
        content = response.text.lower()
        # Indicadores más robustos
        indicators = [
            'fc-btnvercalendarioturnos-button',
            'turnosasesor',
            'master#',
            'bienvenido',
            'cerrar sesión',
            'logout'
        ]
        # También verificar que NO haya indicadores de error
        error_indicators = ['usuario o contraseña incorrectos', 'acceso denegado', 'no autorizado']
        if any(err in content for err in error_indicators):
            return False
        return any(indicator in content for indicator in indicators)

    def _try_cookies_login(self) -> bool:
        """Valida cookies guardadas contra el endpoint de API real"""
        try:
            import os

            if not os.path.exists(self.config.cookies_path):  
                self.config.log.comentario("INFO", "No existen cookies guardadas")  
                return False

            with open(self.config.cookies_path, 'r') as f:  
                cookies = load(f)

            if not cookies:
                self.config.log.comentario("INFO", "Archivo de cookies vacío")  
                return False

            self.config.log.proceso("Cargando cookies en sesión")  

            self.session.cookies.clear()
            clean_domain = sub(r'^https?://', '', self.config.eco_base_url)  

            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', clean_domain),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', True)
                )

            self.config.log.proceso("Validando cookies contra endpoint turnos")  

            response = self.session.get(
                self.config.eco_turnos_url,  
                timeout=self.config.timeout  
            )

            if response.status_code == 200 and self._is_logged_in_response(response):
                self.config.log.comentario("SUCCESS", "Login con cookies válido")  
                return True

            self.config.log.comentario("WARNING", "Cookies inválidas o expiradas")  
            return False

        except Exception as e:
            self.config.log.error(str(e), "LOGIN COOKIES")  
            return False

    def save_cookies(self):
        """Guarda cookies de forma compatible con recarga"""
        try:
            self.config.log.proceso("Guardando cookies")  

            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain or self.eco_base_url,
                    'path': cookie.path or '/',
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                    'rest': getattr(cookie, 'rest', {})
                })

            with open(self.config.cookies_path, 'w') as f:  
                dump(cookies, f, indent=2)

            self.config.log.comentario("SUCCESS", f"Cookies guardadas en {self.config.cookies_path}")  

        except Exception as e:
            self.config.log.error(str(e), "SAVE COOKIES")  

    def get_session(self):
        """Retorna la sesión con headers listos para API"""
        # Asegurar headers compatibles con API JSON
        self.session.headers.update({
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        })
        return self.session