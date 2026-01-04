# region importando librerias necesarias
from re import sub, search
from os import getcwd, makedirs, path
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from requests import request, exceptions
from json import load, dump, JSONDecodeError
from base64 import b64decode
from random import uniform, choice
from time import sleep, time
# endregion importando librerias necesarias

relativePath = getcwd()
KEYENCRYPT = "DE7nxz_qCeUGqvBgHxyaiqtFtCheTnk00AsPCcmSVzU="
f = Fernet(KEYENCRYPT)

class Helpers:
    # Contructores e inicializadores
    def __init__(self):
        self.__routeConfig = relativePath + "/config.json"

    # region Metodos base
    def get_routes(self, key, value = None):
        data = self.get_value(key, value)        
        fullpath = relativePath + data
        return fullpath
    
    def clean_val(self, valor):
        clean = sub(r"[^0-9,]", "", valor)
        return clean
    
    def get_current_time(self):
        now = datetime.now()
        formatted_time = now.strftime("%d/%m/%y %I:%M:%S %p")
        return formatted_time
    
    def calculate_elapsed_time(self, start_time, end_time):
        elapsed = end_time - start_time
        elapsed_str = str(timedelta(seconds=elapsed))
        return elapsed_str
    
    def encriptar_data(self, valor: str):
        token = f.encrypt(str.encode(valor)).decode("utf-8")
        return token
        
    def desencriptar_data(self, valor: str):
        texto = f.decrypt(valor)
        return texto.decode("utf-8")
    
    def decode_image_base64(self, data_uri: str) -> bytes:
        if data_uri.startswith("data:"):
            data_uri = data_uri.split(",", 1)[1]
        data_uri = data_uri.strip().replace("\n", "").replace(" ", "")
        missing_padding = len(data_uri) % 4
        if missing_padding:
            data_uri += "=" * (4 - missing_padding)
        return b64decode(data_uri)

    def get_value(self, key, value=None):
        with open(self.__routeConfig, "r", encoding="utf-8") as file:
            config = load(file)

        data = config.get(key, {})

        if value is None:
            return data

        if isinstance(value, str):
            return str(data.get(value, ""))

        if isinstance(value, (list, tuple)):
            for subkey in value:
                if isinstance(data, dict):
                    data = data.get(subkey, "")
                else:
                    return ""
            return str(data)

        return ""
        
    def get_json(self, ruta_archivo):
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                return load(archivo)
        except JSONDecodeError:
            print(f"❌ Error: El archivo '{ruta_archivo}' no tiene un formato JSON válido.")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        return None
    
    def save_json(self, ruta_archivo, datos, append=False):
        try:
            if append:
                datos_existentes = self.get_json(ruta_archivo) or {}
                if isinstance(datos_existentes, dict) and isinstance(datos, dict):
                    datos_actualizados = {**datos_existentes, **datos}
                elif isinstance(datos_existentes, list) and isinstance(datos, list):
                    datos_actualizados = datos_existentes + datos
                else:
                    raise ValueError("❌ Los tipos de datos no coinciden o no son válidos para hacer append.")
            else:
                datos_actualizados = datos

            with open(ruta_archivo, "w", encoding="utf-8") as archivo:
                dump(datos_actualizados, archivo, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"❌ Error al guardar el archivo '{ruta_archivo}': {e}")

    def request_api(self, method, endpoint, data=None, token=None):
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        try:
            response = request(
                method=method,
                url=endpoint,
                headers=headers,
                json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                params=data if method == 'GET' else None
            )
            return response.json() if response.status_code in (200, 201) else None
        except exceptions.RequestException as e:
            print(f"Error en la solicitud {method}: {e}")
            return None
    
    def check_response(self, response) -> bool:
        if response and (response.get("status_code") == 200 or response.get("status_code") == 201):
            return True
        return False
    # endregion Metodos base

    # region METODOS PARA FCK
    def create_directories(self):
        """Crea los directorios necesarios para el proyecto Facebook"""
        directories = [
            "./screenshots",
            "./data", 
            "./logs",
            "./cookies"
        ]
        
        for directory in directories:
            try:
                makedirs(directory, exist_ok=True)
                print(f"✅ Directorio creado/existe: {directory}")
            except Exception as e:
                print(f"❌ Error creando directorio {directory}: {e}")

    def get_random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> float:
        """Genera un delay aleatorio para simular comportamiento humano"""
        return uniform(min_seconds, max_seconds)

    def human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Espera un tiempo aleatorio entre acciones"""
        delay = self.get_random_delay(min_seconds, max_seconds)
        sleep(delay)

    def get_random_user_agent(self) -> str:
        """Retorna un User-Agent aleatorio para evitar detección"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        return choice(user_agents)

    def validate_facebook_url(self, url: str) -> bool:
        """Valida si una URL es de Facebook - CORREGIDO"""
        if not url or not isinstance(url, str):
            return False
            
        facebook_domains = [
            'facebook.com',
            'www.facebook.com', 
            'm.facebook.com',
            'web.facebook.com',
            'fb.com',
            'www.fb.com'
        ]
        
        # Usar 'search' en lugar de 'sub' - ESTA ERA LA CAUSA DEL ERROR
        return any(domain in url.lower() for domain in facebook_domains)

    def extract_facebook_group_id(self, group_url: str) -> str:
        """Extrae el ID de un grupo de Facebook desde la URL - CORREGIDO"""
        try:
            if not group_url:
                return ""
                
            # Diferentes formatos de URLs de grupos
            patterns = [
                r'facebook\.com/groups/([^/?]+)',
                r'fb\.com/groups/([^/?]+)',
                r'groups/([^/?]+)'
            ]
            
            for pattern in patterns:
                match = search(pattern, group_url)
                if match:
                    return match.group(1)
            
            return ""
        except Exception as e:
            print(f"❌ Error extrayendo group ID: {e}")
            return ""

    def save_facebook_data(self, data: dict, filename: str):
        """Guarda datos de Facebook en JSON con timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = sub(r'[^\w\-_.]', '_', filename)  # Aquí 'sub' está bien usado
            filepath = f"./data/fb_{safe_filename}_{timestamp}.json"
            
            # Agregar metadata
            data_with_meta = {
                "metadata": {
                    "scraped_at": self.get_current_time(),
                    "source": "facebook", 
                    "version": "1.0"
                },
                "data": data
            }
            
            self.save_json(filepath, data_with_meta)
            return filepath
        except Exception as e:
            print(f"❌ Error guardando datos Facebook: {e}")
            return None

    def load_facebook_config(self) -> dict:
        """Carga configuración específica para Facebook"""
        try:
            config = self.get_value("facebook")
            if not config:
                # Configuración por defecto
                config = {
                    "max_posts_per_group": 10,
                    "scroll_attempts": 3,
                    "request_delay": 2,
                    "headless": False,
                    "enable_screenshots": True
                }
            return config
        except Exception as e:
            print(f"❌ Error cargando configuración Facebook: {e}")
            return {}

    def clean_facebook_text(self, text: str) -> str:
        """Limpia texto extraído de Facebook"""
        if not text:
            return ""
        
        # Remover emojis y caracteres especiales - 'sub' usado correctamente
        cleaned = sub(r'[^\w\sáéíóúÁÉÍÓÚñÑ.,!?;:()\-]', '', text)
        # Remover espacios múltiples
        cleaned = sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def format_facebook_post_data(self, post_data: dict) -> dict:
        """Formatea y estructura datos de un post de Facebook"""
        return {
            "post_id": post_data.get("id", ""),
            "author": self.clean_facebook_text(post_data.get("author", "")),
            "content": self.clean_facebook_text(post_data.get("content", "")),
            "timestamp": post_data.get("timestamp", ""),
            "likes": int(post_data.get("likes", 0)),
            "comments": int(post_data.get("comments", 0)),
            "shares": int(post_data.get("shares", 0)),
            "media_attached": post_data.get("has_media", False),
            "url": post_data.get("url", ""),
            "scraped_at": self.get_current_time()
        }

    def check_rate_limit(self, last_request_time: float, min_interval: float = 2.0) -> bool:
        """Verifica si se debe esperar por rate limiting"""
        current_time = time()
        time_since_last = current_time - last_request_time
        return time_since_last >= min_interval

    def get_timestamp_filename(self, prefix: str = "screenshot") -> str:
        """Genera un nombre de archivo con timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"./screenshots/{prefix}_{timestamp}.png"

    def validate_credentials(self, email: str, password: str) -> bool:
        """Valida formato básico de credenciales - CORREGIDO"""
        print(f"Validando credenciales para email: {email}")
        print(f"Validando credenciales para password: {'*' * len(password) if password else ''}")
        if not email or not password:
            return False
            
        return True

    def backup_cookies(self, cookies: list, filename: str = None):
        """Guarda cookies de sesión para reutilizar - CORREGIDO"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"./cookies/fb_cookies_{timestamp}.json"
            
            # Asegurar que el directorio existe
            directory = path.dirname(filename)
            if directory and not path.exists(directory):
                makedirs(directory, exist_ok=True)
                print(f"✅ Directorio creado: {directory}")
            
            # Guardar cookies
            with open(filename, 'w', encoding='utf-8') as f:
                dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Cookies guardadas: {filename} ({len(cookies)} cookies)")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando cookies en {filename}: {e}")
            return False

    def load_cookies(self, filename: str) -> list:
        """Carga cookies de sesión guardadas"""
        try:
            return self.get_json(filename) or []
        except Exception as e:
            print(f"❌ Error cargando cookies: {e}")
            return []
    # endregion METODOS PARA FCK