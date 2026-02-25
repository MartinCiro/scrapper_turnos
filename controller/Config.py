from re import sub
from dotenv import load_dotenv
from os import path as pt, makedirs, getenv
from controller.Log import Log

class Config:
    """
    Clase encargada de generar variables globales desde .env para EcoDigital - Versión HTTP
    """

    def __init__(self) -> None:
        """Constructor de la clase"""
        load_dotenv()
        self.log = Log()
        
        # 🔐 CREDENCIALES ECODIGITAL
        self.user_eco = self._get_env_variable("USER_ECO")
        self.ps_eco = self._get_env_variable("PASSWD_ECO")
        
        # 🌐 URLs ECODIGITAL
        self.eco_base_url = "https://ecodigital.emergiacc.com"
        self.eco_login_url = f"{self.eco_base_url}/WebEcoPresencia/"
        self.eco_turnos_url = f"{self.eco_login_url}Master#/TurnosAsesor"
        self.eco_api_turnos = f"{self.eco_base_url}/WebEcoPresencia/Asesor/ObtenerTurnos"
        
        # 📁 CONFIGURACIÓN DE ALMACENAMIENTO
        self.cookies_base_path = "./cookies"
        self.cookies_path = self._get_user_cookies_path()
        self.logs_path = self._get_env_variable("LOGS_PATH", "./logs")
        self.data_path = self._get_env_variable("DATA_PATH", "./data")
        
        # 🔄 CONFIGURACIÓN DE REINTENTOS
        self.max_retries = int(self._get_env_variable("MAX_RETRIES", "3"))
        self.retry_delay = float(self._get_env_variable("RETRY_DELAY", "5.0"))
        self.timeout = int(self._get_env_variable("TIMEOUT", "30"))
        
        # Validar configuración
        self.validate_config()

    def _get_env_variable(self, key: str, default: str = None):
        """Obtiene variable de entorno de forma segura"""
        value = getenv(key, default)
        if value is None and default is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        return value

    def _get_user_cookies_path(self) -> str:
        """
        Genera una ruta de cookies única para el usuario actual.
        Ejemplo: ./cookies/usuario123_cookies.json
        """
        try:
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
            print(f"⚠️ Error generando ruta de cookies específica: {e}")
            # Fallback: ruta genérica
            return pt.join(self.cookies_base_path, "cookies.json")

    def validate_config(self):
        """Valida que la configuración sea correcta"""
        # Validar credenciales básicas
        if not self.user_eco or not self.ps_eco:
            raise ValueError("Credenciales de EcoDigital inválidas")
        
        # Validar rutas
        required_paths = [self.logs_path, self.cookies_base_path, self.data_path]
        for path_dir in required_paths:
            if not pt.exists(path_dir):
                makedirs(path_dir, exist_ok=True)
        
        return True