# Config.py
from re import sub
from dotenv import load_dotenv
from os import path as pt, makedirs, getenv
from typing import List
from controller.Log import Log

class Config:
    """
    Clase encargada de generar variables globales desde .env para EcoDigital - Versión HTTP
    SOPORTA LISTAS DE USUARIOS Y USUARIO ACTUAL
    """

    def __init__(self) -> None:
        """Constructor"""
        load_dotenv()
        self.log = Log()
        
        # 📋 LISTAS DE TODOS LOS USUARIOS
        self.users_eco: List[str] = []
        self.passwds_eco: List[str] = []
        
        # 👤 USUARIO ACTUAL (se actualizará en cada iteración)
        self.user_eco: str = None
        self.ps_eco: str = None
        
        # Cargar listas de usuarios
        self._cargar_listas_usuarios()
        
        # 🌐 URLs ECODIGITAL
        self.eco_base_url = "https://ecodigital.emergiacc.com"
        self.eco_login_url = f"{self.eco_base_url}/WebEcoPresencia/"
        self.eco_turnos_url = f"{self.eco_login_url}Master#/TurnosAsesor"
        self.eco_api_turnos = f"{self.eco_base_url}/WebEcoPresencia/Asesor/ObtenerTurnos"
        
        # 📁 CONFIGURACIÓN DE ALMACENAMIENTO
        self.cookies_base_path = "./cookies"
        self.logs_path = self._get_env_variable("LOGS_PATH", "./logs")
        self.data_path = self._get_env_variable("DATA_PATH", "./data")
        
        # 🔄 CONFIGURACIÓN DE REINTENTOS
        self.max_retries = int(self._get_env_variable("MAX_RETRIES", "3"))
        self.retry_delay = float(self._get_env_variable("RETRY_DELAY", "5.0"))
        self.timeout = int(self._get_env_variable("TIMEOUT", "30"))
        
        # Telegram
        self.telegram_token = self._get_env_variable("TELEGRAM_TOKEN", "")
        self.telegram_chat = self._get_env_variable("TELEGRAM_CHAT", "")
        
        # Validar configuración
        self.validate_config()

    def _get_env_variable(self, key: str, default: str = None):
        """Obtiene variable de entorno de forma segura"""
        value = getenv(key, default)
        if value is None and default is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        return value

    def _cargar_listas_usuarios(self):
        """Carga las listas de usuarios desde el .env"""
        if not self.users_eco:
            user = getenv("USER_ECO")
            pwd = getenv("PASSWD_ECO")
            if user and pwd:
                self.users_eco = [user]
                self.passwds_eco = [pwd]
        
        # Establecer el primer usuario como actual por defecto
        if self.users_eco:
            self.user_eco = self.users_eco[0]
            self.ps_eco = self.passwds_eco[0]

    def _get_user_cookies_path(self) -> str:
        """
        Genera una ruta de cookies única para el usuario ACTUAL.
        Ejemplo: ./cookies/usuario123_cookies.json
        """
        try:
            if not self.user_eco:
                raise ValueError("No hay usuario actual configurado")
            
            # Crear directorio base de cookies si no existe
            if not pt.exists(self.cookies_base_path):
                makedirs(self.cookies_base_path, exist_ok=True)
            
            # Extraer nombre de usuario del email
            username = self.user_eco.split('@')[0] if '@' in self.user_eco else self.user_eco
            
            # Limpiar caracteres no válidos para nombres de archivo
            safe_username = sub(r'[^\w\-_\. ]', '_', username)
            
            # Crear ruta específica
            cookies_file = f"{safe_username}_cookies.json"
            return pt.join(self.cookies_base_path, cookies_file)
            
        except Exception as e:
            print(f"⚠️ Error generando ruta de cookies: {e}")
            return pt.join(self.cookies_base_path, "cookies.json")

    def get_user_data_path(self) -> str:
        """
        Genera la ruta de datos específica para el usuario ACTUAL.
        Ejemplo: ./data/usuarios/usuario123/
        """
        try:
            if not self.user_eco:
                raise ValueError("No hay usuario actual configurado")
            
            # Extraer nombre de usuario del email
            username = self.user_eco.split('@')[0] if '@' in self.user_eco else self.user_eco
            safe_username = sub(r'[^\w\-_\. ]', '_', username)
            
            # Ruta: ./data/usuarios/NOMBRE_USUARIO/
            user_data_path = pt.join(self.data_path, "usuarios", safe_username)
            
            # Crear directorio si no existe
            if not pt.exists(user_data_path):
                makedirs(user_data_path, exist_ok=True)
            
            return user_data_path
            
        except Exception as e:
            print(f"⚠️ Error generando ruta de datos: {e}")
            return self.data_path

    def get_user_json_path(self) -> str:
        """
        Genera la ruta completa del archivo JSON para el usuario ACTUAL.
        Ejemplo: ./data/usuarios/usuario123/calendario.json
        """
        user_data_path = self.get_user_data_path()
        return pt.join(user_data_path, "calendario.json")

    def validate_config(self):
        """Valida que la configuración sea correcta"""
        # Validar listas de usuarios
        if not self.users_eco:
            raise ValueError("No hay usuarios configurados en USERS_ECO")
        
        if len(self.users_eco) != len(self.passwds_eco):
            raise ValueError(f"Número de usuarios ({len(self.users_eco)}) no coincide con número de contraseñas ({len(self.passwds_eco)})")
        
        # Validar que hay un usuario actual (aunque sea el primero)
        if not self.user_eco or not self.ps_eco:
            raise ValueError("No se pudo establecer un usuario actual")
        
        # Validar rutas base
        required_paths = [self.logs_path, self.cookies_base_path, self.data_path]
        for path_dir in required_paths:
            if not pt.exists(path_dir):
                makedirs(path_dir, exist_ok=True)
                print(f"📁 Directorio creado: {path_dir}")
        
        print(f"✅ Configuración válida: {len(self.users_eco)} usuario(s) cargados")
        print(f"👤 Usuario actual por defecto: {self.user_eco}")
        
        return True