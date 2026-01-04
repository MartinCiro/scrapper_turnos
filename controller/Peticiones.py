from dotenv import load_dotenv
from os import getenv

load_dotenv()

class Peticiones(APIClient):
    """
    Peticiones
    ==========
    Esta clase se encargará de realizar las peticiones
    correspondientes a la API de BOT
    """

    def __init__(self) -> None:
        super().__init__()
        self.username = getenv("USER_API")
        self.pass_wd = getenv("PASS_API")
    
    def obtener_origenes(self) -> dict:
        """
        Método encargado de consultar los los origenes desde la API.
        Puede consultar uno en específico si se pasa un ID.
        """
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                if not self.auth_token:
                    self.login_api()

                res = self.request(self.dict_endpoints['origenes'], body=None)
                
                if res and 'result' in res:
                    return res['result']
                return res 

            except Exception as e:
                print(f"[Intento {intento}/{max_intentos}] Error al consultar los origenes: {e}")
        
        print("❌ Se excedió el número máximo de intentos para obtener los origenes.")
        return None

    def login_api(self) -> str | None:
        """
        Inicia sesión en la API y retorna el token de acceso si es exitoso.
        """
        try:
            res = self.request(self.dict_endpoints['login'], {"username": f"{self.username}", "enpass": f"{self.pass_wd}"}, 'POST')

            # Validamos que la estructura esperada exista
            if res['token']:
                self.auth_token = res['token']
                return self.auth_token
            else:
                print("La estructura de la respuesta del login no es válida.")
            
        except Exception as e:
            print(f"Falló al hacer login en la API: {e}")

        return None  # Retorno explícito si algo falla
  
    def carga_data_api(self, data: dict) -> str | None:
        """
        Este metodo se encargará de enviar los datos a la base de
        datos de mysql, endpoint de productos.
        """
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                if not self.auth_token:
                    self.login_api()

                res = self.request(self.dict_endpoints['productos'], body=data, method='POST')
                
                if res and 'result' in res:
                    return res['result']
                return res 

            except Exception as e:
                print(f"[Intento {intento}/{max_intentos}] Error en la carga de datos: {e}")
        
        print("❌ Se excedió el número máximo de intentos para obtener los origenes.")
        return None