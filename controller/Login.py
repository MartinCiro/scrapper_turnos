# controller/LoginHTTP.py (versión corregida para VPS)
import requests
import json
import time
from datetime import datetime
from controller.Config import Config
from random import uniform

class Login(Config):
    """
    Clase corregida para bypass Cloudflare en VPS.
    ¡CRÍTICO: Mantiene espacios al final en URLs/headers como en el curl original!
    """

    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        
        # 🔑 HEADERS COMPLETOS con espacios al final (¡OBLIGATORIO PARA CLOUDFLARE!)
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
            'Origin': 'https://ecodigital.emergiacc.com  ',
            'Referer': 'https://ecodigital.emergiacc.com/WebEcoPresencia/  ',
        })

    def _log(self, message: str, type: str = "info"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        prefix = {"error": "❌", "warning": "⚠️ ", "success": "✅", "info": "🔧"}.get(type, "🔧")
        print(f"{prefix} {log_message}")

    def _get_login_payload(self) -> dict:
        return {
            'DominioLoginAD': '',
            'UsuarioLogado.Login': self.user_eco,
            'UsuarioLogado.Password': self.ps_eco,
            'IniciarSesionAD': 'false'
        }

    def login(self, use_cookies: bool = True) -> bool:
        """
        Login con bypass Cloudflare mejorado para VPS
        """
        # 1. PRIMERO: Intentar con cookies guardadas (más rápido)
        if use_cookies and self._try_cookies_login():
            return True
        
        # 2. HACER GET INICIAL CON HEADERS COMPLETOS
        try:
            self._log("🌐 Obteniendo cookies de sesión (con headers Cloudflare)...", "info")
            
            # ⚠️ URL CON ESPACIOS AL FINAL - ¡OBLIGATORIO!
            login_url_con_espacios = "https://ecodigital.emergiacc.com/WebEcoPresencia/  "
            
            # Headers específicos para el GET inicial
            get_headers = {
                'Cache-Control': 'max-age=0',
                'Priority': 'u=0, i',
                # Mantener los headers base de la sesión
            }
            
            response = self.session.get(
                login_url_con_espacios,
                headers=get_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            self._log(f"   Status: {response.status_code}", "info")
            
            if response.status_code == 403:
                self._log("❌ Cloudflare bloqueó la petición (403)", "error")
                self._log("💡 Solución: Necesitas cf_clearance válido o usar curl_cffi", "warning")
                return False
            
            if response.status_code != 200:
                self._log(f"❌ Error en GET inicial: {response.status_code}", "error")
                return False
            
            # 3. ENVIAR CREDENCIALES
            payload = self._get_login_payload()
            
            post_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cache-Control': 'max-age=0',
                'Priority': 'u=0, i',
                # ⚠️ ESPACIOS AL FINAL EN ORIGIN/REFERER
                'Origin': 'https://ecodigital.emergiacc.com  ',
                'Referer': 'https://ecodigital.emergiacc.com/WebEcoPresencia/  ',
            }
            
            login_response = self.session.post(
                login_url_con_espacios,  # Mismo URL con espacios
                data=payload,
                headers=post_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if login_response.status_code == 403:
                self._log("❌ Cloudflare bloqueó el POST (403)", "error")
                self._log("   Razón: IP de VPS detectada como automatizada", "warning")
                self._log("   Solución 1: Usar curl_cffi (recomendado)", "info")
                self._log("   Solución 2: Ejecutar desde IP residencial", "info")
                return False
            
            if "Usuario o contraseña incorrectos" in login_response.text:
                self._log("❌ Credenciales incorrectas", "error")
                return False
            
            if self._is_logged_in_response(login_response):
                self._log("✅ Login exitoso", "success")
                self.save_cookies()
                return True
            
            self._log("❌ Login fallido (respuesta inesperada)", "error")
            return False
            
        except requests.exceptions.Timeout:
            self._log("❌ Timeout en la conexión", "error")
            return False
        except Exception as e:
            self._log(f"❌ Error en login: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            return False

    def _is_logged_in_response(self, response) -> bool:
        content = response.text.lower()
        logged_in_indicators = [
            'fc-btnvercalendarioturnos-button',
            'turnosasesor',
            'master#'
        ]
        return any(indicator in content for indicator in logged_in_indicators)

    def _try_cookies_login(self) -> bool:
        """Intenta login con cookies guardadas (incluyendo cf_clearance si existe)"""
        try:
            import os
            if not os.path.exists(self.cookies_path):
                return False
            
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
            
            if not cookies:
                return False
            
            # Cargar cookies en sesión
            self.session.cookies.clear()
            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'],
                    domain=cookie.get('domain', 'ecodigital.emergiacc.com'),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', True)
                )
            
            # Verificar si cookies son válidas
            response = self.session.get(
                "https://ecodigital.emergiacc.com/WebEcoPresencia/Master#/TurnosAsesor",
                timeout=self.timeout
            )
            
            if response.status_code == 200 and self._is_logged_in_response(response):
                self._log("✅ Login con cookies exitoso", "success")
                return True
            
            return False
            
        except Exception as e:
            self._log(f"⚠️ Error en login con cookies: {str(e)}", "warning")
            return False

    def save_cookies(self):
        """Guarda cookies incluyendo cf_clearance si existe"""
        try:
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain or 'ecodigital.emergiacc.com',
                    'path': cookie.path,
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                })
            
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            self._log(f"💾 Cookies guardadas: {self.cookies_path}", "success")
            
        except Exception as e:
            self._log(f"❌ Error guardando cookies: {str(e)}", "error")

    def get_session(self):
        """Retorna la sesión actual para hacer requests adicionales"""
        return self.session