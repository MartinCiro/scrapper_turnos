from requests import Session, exceptions
from json import load, dump
from datetime import datetime
from controller.Config import Config
from re import sub, search

class Login(Config):
    """
    Clase corregida para manejo robusto de sesión y Cloudflare.
    """

    def __init__(self) -> None:
        super().__init__()
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
            # ✅ SIN espacios al final
            'Origin': self.eco_base_url.rstrip('/'),
            'Referer': self.eco_login_url.rstrip('/'),
        })

    def _get_login_payload(self, request_verification_token: str = None) -> dict:
        payload = {
            'DominioLoginAD': '',
            'UsuarioLogado.Login': self.user_eco,
            'UsuarioLogado.Password': self.ps_eco,
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
        self.log.inicio_proceso("LOGIN ECO")

        try:
            # 1. Intentar con cookies primero
            if use_cookies and self._try_cookies_login():
                self.log.comentario("INFO", "Login exitoso usando cookies")
                self.log.fin_proceso("LOGIN ECO")
                return True

            # 2. GET inicial para obtener cookies y CSRF token
            self.log.proceso("GET inicial para obtener cookies y token CSRF")
            
            response = self.session.get(
                self.eco_login_url,
                timeout=self.timeout,
                allow_redirects=True
            )

            if response.status_code == 403:
                self.log.error("Cloudflare bloqueó la petición (403)", "GET inicial")
                self.log.fin_proceso("LOGIN ECO")
                return False

            if response.status_code != 200:
                self.log.error(f"Error en GET inicial: {response.status_code}", "GET inicial")
                self.log.fin_proceso("LOGIN ECO")
                return False

            # 3. Extraer token CSRF si existe
            csrf_token = self._extract_csrf_token(response.text)
            if csrf_token:
                self.log.comentario("INFO", f"Token CSRF encontrado: {csrf_token[:20]}...")

            # 4. POST login con payload correcto
            self.log.proceso("Enviando credenciales")
            payload = self._get_login_payload(csrf_token)

            login_response = self.session.post(
                self.eco_login_url,
                data=payload,
                timeout=self.timeout,
                allow_redirects=True,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )

            if login_response.status_code == 403:
                self.log.error("Cloudflare bloqueó el POST (403)", "POST login")
                self.log.fin_proceso("LOGIN ECO")
                return False

            if "Usuario o contraseña incorrectos" in login_response.text:
                self.log.error("Credenciales incorrectas", "POST login")
                self.log.fin_proceso("LOGIN ECO")
                return False

            if self._is_logged_in_response(login_response):
                self.log.comentario("SUCCESS", "Login exitoso")
                self.save_cookies()
                self.log.fin_proceso("LOGIN ECO")
                return True

            # Debug: guardar respuesta para análisis
            self.log.comentario("DEBUG", f"Respuesta login (200 chars): {login_response.text[:200]}")
            self.log.error("Login fallido (respuesta inesperada)", "POST login")
            self.log.fin_proceso("LOGIN ECO")
            return False

        except exceptions.Timeout:
            self.log.error("Timeout en la conexión", "LOGIN")
            self.log.fin_proceso("LOGIN ECO")
            return False
        except Exception as e:
            self.log.error(str(e), "LOGIN")
            import traceback
            traceback.print_exc()
            self.log.fin_proceso("LOGIN ECO")
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
            if not os.path.exists(self.cookies_path):
                return False

            with open(self.cookies_path, 'r') as f:
                cookies = load(f)

            if not cookies:
                return False

            self.session.cookies.clear()
            clean_domain = sub(r'^https?://', '', self.eco_base_url).split('/')[0]

            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', clean_domain),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', True)
                )

            # ✅ Validar contra el endpoint de API real, no la página web
            response = self.session.get(
                self.eco_api_turnos,  # ← Endpoint correcto para API
                json={"fechaInicio": "1/1/2026", "fechaFin": "31/1/2026"},
                headers={'Content-Type': 'application/json'},
                timeout=15
            )

            # Verificar que NO devuelva "NOSESS"
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'turnos' in data:
                        return True
                    if isinstance(data, str) and data == "NOSESS":
                        self.log.comentario("WARNING", "Cookies válidas pero sesión expirada en API")
                        return False
                except:
                    pass
            
            self.log.comentario("WARNING", "Cookies inválidas o expiradas")
            return False

        except Exception as e:
            self.log.error(str(e), "LOGIN COOKIES")
            return False

    def save_cookies(self):
        """Guarda cookies de forma compatible con recarga"""
        try:
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

            with open(self.cookies_path, 'w') as f:
                dump(cookies, f, indent=2)
            self.log.comentario("SUCCESS", f"Cookies guardadas")
        except Exception as e:
            self.log.error(str(e), "SAVE COOKIES")

    def get_session(self):
        """Retorna la sesión con headers listos para API"""
        # Asegurar headers compatibles con API JSON
        self.session.headers.update({
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        })
        return self.session