from controller.BasePlaywright import BasePlaywright
from controller.utils.Helpers import Helpers
from dotenv import load_dotenv
from os import path as pt, makedirs, getenv

class Config(BasePlaywright):
    """
    Clase encargada de generar variables globales desde .env para Facebook
    """

    def __init__(self) -> None:
        """Constructor de la clase. Hereda de BasePlaywright"""
        load_dotenv()
        super().__init__()

        self.selectors = {
            # FORMULARIO DE LOGIN
            "username_input": [
                "//input[@id='UsuarioLogado_Login']",
            ],
            
            "password_input": [
                "//input[@id='UsuarioLogado_Password']",
            ],
            
            "login_button": [
                "//input[@id='btnIniciar']",
            ],
            
            # VERIFICAR SESIÓN ACTIVA
            "logged_in_indicators": [
                "//button[starts-with(@class, 'fc-btnVerCalendarioTurnos-button')]",
            ],

            "btn_turnos": [
                "//a[@href='#TurnosAsesor']",
            ],
            
            # ERRORES DE LOGIN
            "error_messages": [
                "//div[contains(text(), 'Usuario o contraseña incorrectos')]",
            ]
        }
        
        # Inicializar Helpers
        self.helper = Helpers()
        
        # Crear directorios necesarios
        self.helper.create_directories()
        
        # 🔐 CREDENCIALES FACEBOOK
        self.user_eco = self._get_env_variable("USER")
        self.ps_eco = self._get_env_variable("PASSWD")
        

        self.eco_base_url = "https://ecodigital.emergiacc.com"
        self.eco_login_url = f"{self.eco_base_url}/WebEcoPresencia"
        self.eco_turnos_url = f"{self.eco_login_url}/Master#/TurnosAsesor"
        
        # ⚙️ CONFIGURACIÓN DE SCRAPING
        self.max_posts_per_group = int(self._get_env_variable("MAX_POSTS", "20"))
        self.scroll_attempts = int(self._get_env_variable("SCROLL_ATTEMPTS", "3"))
        self.request_delay = float(self._get_env_variable("REQUEST_DELAY", "2.0"))
        self.max_scroll_wait = int(self._get_env_variable("MAX_SCROLL_WAIT", "30"))
        
        # 🕵️ CONFIGURACIÓN STEALTH
        self.headless = self._get_env_variable("HEADLESS", "False").lower() == "true"
        self.user_agent_rotation = self._get_env_variable("ROTATE_UA", "True").lower() == "true"
        self.enable_stealth = self._get_env_variable("ENABLE_STEALTH", "True").lower() == "true"
        self.random_delays = self._get_env_variable("RANDOM_DELAYS", "True").lower() == "true"
        
        # 📁 CONFIGURACIÓN DE ALMACENAMIENTO
        self.screenshots_path = self._get_env_variable("SCREENSHOTS_PATH", "./screenshots")
        self.data_path = self._get_env_variable("DATA_PATH", "./data")
        self.cookies_path = self._get_env_variable("COOKIES_PATH", "./cookies/cookies.json")
        self.logs_path = self._get_env_variable("LOGS_PATH", "./logs")
        
        # 🖼️ CONFIGURACIÓN DE MEDIA
        self.save_screenshots = self._get_env_variable("SAVE_SCREENSHOTS", "True").lower() == "true"
        self.screenshot_quality = int(self._get_env_variable("SCREENSHOT_QUALITY", "80"))
        self.max_screenshots = int(self._get_env_variable("MAX_SCREENSHOTS", "50"))
        
        # 🔄 CONFIGURACIÓN DE REINTENTOS
        self.max_retries = int(self._get_env_variable("MAX_RETRIES", "3"))
        self.retry_delay = float(self._get_env_variable("RETRY_DELAY", "5.0"))
        self.timeout = int(self._get_env_variable("TIMEOUT", "30000"))
        
        # 🧠 CONFIGURACIÓN IA/ML (para comparación de imágenes)
        self.enable_ai = self._get_env_variable("ENABLE_AI", "False").lower() == "true"
        self.ai_model_path = self._get_env_variable("AI_MODEL_PATH", "./models")
        self.similarity_threshold = float(self._get_env_variable("SIMILARITY_THRESHOLD", "0.8"))
        
        # Validar configuración
        self.validate_config()

    def _get_env_variable(self, key: str, default: str = None):
        """Obtiene variable de entorno de forma segura usando Helpers"""
        value = getenv(key, default)
        if value is None and default is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        return value

    def validate_config(self):
        """Valida que la configuración sea correcta usando Helpers"""
        # Validar credenciales
        if not self.helper.validate_credentials(self.user_eco, self.ps_eco):
            print("Este es el resultado de la validación de credenciales: ", self.helper.validate_credentials(self.user_eco, self.ps_eco), "FB_EMAIL:", self.user_eco, "FB_PASSWORD:", self.ps_eco)
            raise ValueError("Credenciales de Facebook inválidas")
        
        # Validar rutas
        required_paths = [self.screenshots_path, self.data_path, self.logs_path]
        for path in required_paths:
            if not pt.exists(path):
                makedirs(path, exist_ok=True)
        
        # Validar límites
        if self.max_posts_per_group > 100:
            print("⚠️  Advertencia: MAX_POSTS muy alto, puede causar detección")
        
        if self.request_delay < 1.0:
            print("⚠️  Advertencia: REQUEST_DELAY muy bajo, puede causar bloqueo")
        return True

    def get_scraping_config(self) -> dict:
        """Retorna configuración de scraping para fácil acceso"""
        return {
            "max_posts": self.max_posts_per_group,
            "scroll_attempts": self.scroll_attempts,
            "request_delay": self.request_delay,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "headless": self.headless
        }

    def get_stealth_config(self) -> dict:
        """Retorna configuración stealth para fácil acceso"""
        return {
            "user_agent_rotation": self.user_agent_rotation,
            "random_delays": self.random_delays,
            "enable_stealth": self.enable_stealth,
            "headless": self.headless
        }

    def get_storage_config(self) -> dict:
        """Retorna configuración de almacenamiento para fácil acceso"""
        return {
            "screenshots_path": self.screenshots_path,
            "data_path": self.data_path,
            "cookies_path": self.cookies_path,
            "logs_path": self.logs_path,
            "save_screenshots": self.save_screenshots
        }

    def update_config(self, key: str, value):
        """Actualiza una configuración dinámicamente"""
        if hasattr(self, key):
            setattr(self, key, value)
            print(f"✅ Configuración actualizada: {key} = {value}")
        else:
            print(f"❌ Configuración no encontrada: {key}")