from controller.Config import Config
from controller.Ejecucion import Ejecuciones

if __name__ == "__main__":
    # 1. Crear la configuración (carga variables de entorno)
    config = Config()
    
    # 2. Inyectar la configuración en Ejecuciones
    ejecutor = Ejecuciones(config)
    
    # 3. Ejecutar flujo completo (login + extracción + guardado)
    exito = ejecutor.ejecutar_flujo_completo()
    
    print("\n✅ ✅ ✅ EJECUCIÓN EXITOSA ✅ ✅ ✅" if exito else "\n❌ ❌ ❌ EJECUCIÓN FALLIDA ❌ ❌ ❌")