from controller.Ejecucion import Ejecuciones

if __name__ == "__main__":
    ejecutor = Ejecuciones()
    
    # Ejecutar flujo completo (login + extracción + guardado)
    exito = ejecutor.ejecutar_flujo_completo()
    
    if exito:
        print("\n✅ ✅ ✅ EJECUCIÓN EXITOSA ✅ ✅ ✅")
    else:
        print("\n❌ ❌ ❌ EJECUCIÓN FALLIDA ❌ ❌ ❌")