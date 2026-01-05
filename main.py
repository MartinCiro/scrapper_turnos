# ===========================================================================
# Importaciones de clases y librerías necesarias para EcoDigital
# ===========================================================================
from controller.Ejecucion import Ejecuciones
from controller.utils.Helpers import Helpers
import time
import sys

def mostrar_menu():
    """Muestra el menú de opciones disponibles"""
    print("\n" + "="*60)
    print("🎯 MENÚ PRINCIPAL - ECODIGITAL AUTOMATION")
    print("="*60)
    print("1. 🚀 Flujo completo (Login + Click botón + Verificación)")
    print("2. 🔐 Solo login y click en botón principal")
    print("3. ⚡ Prueba rápida del botón (asume login previo)")
    print("4. 🖼️  Tomar capturas de evidencia")
    print("5. 🚪 Cerrar sesión")
    print("6. 📊 Ver estado actual")
    print("7. ❌ Salir")
    print("="*60)

def ejecutar_flujo_completo(ejecutor):
    """Ejecuta el flujo completo de pruebas"""
    print("\n🔁 EJECUTANDO FLUJO COMPLETO...")
    resultado = ejecutor.ejecutar_flujo_completo()
    
    if resultado:
        print("\n🎊 ¡FLUJO COMPLETADO CON ÉXITO!")
    else:
        print("\n💀 ¡ALGUNOS PASOS FALLARON!")
    
    return resultado

def solo_login_y_boton(ejecutor):
    """Ejecuta solo login y click en el botón"""
    print("\n🔐 EJECUTANDO LOGIN Y CLICK EN BOTÓN...")
    resultado = ejecutor.ejecuta_login_y_boton()
    
    if resultado:
        print("\n✅ Login y click exitosos")
    else:
        print("\n❌ Falló el login o el click")
    
    return resultado

def prueba_rapida_boton(ejecutor):
    """Prueba rápida del botón (asume sesión activa)"""
    print("\n⚡ EJECUTANDO PRUEBA RÁPIDA DEL BOTÓN...")
    resultado = ejecutor.prueba_rapida_boton()
    
    if resultado:
        print("\n✅ Prueba rápida exitosa")
    else:
        print("\n❌ Prueba rápida fallida")
    
    return resultado


def tomar_capturas(ejecutor):
    """Toma capturas de pantalla"""
    print("\n🖼️  TOMANDO CAPTURAS DE EVIDENCIA...")
    resultado = ejecutor.tomar_captura_evidencia()
    
    if resultado:
        print("\n✅ Capturas guardadas exitosamente")
    else:
        print("\n❌ Error al tomar capturas")
    
    return resultado

def cerrar_sesion(ejecutor):
    """Cierra la sesión actual"""
    print("\n🚪 CERRANDO SESIÓN...")
    resultado = ejecutor.ejecutar_logout()
    
    if resultado:
        print("\n✅ Sesión cerrada exitosamente")
    else:
        print("\n❌ No se pudo cerrar la sesión")
    
    return resultado

def ver_estado_actual(ejecutor):
    """Muestra el estado actual del sistema"""
    print("\n📊 VERIFICANDO ESTADO ACTUAL...")
    
    if ejecutor.login_instance:
        estado = ejecutor.login_instance.get_login_status()
        print(f"\n📋 Estado del login:")
        for key, value in estado.items():
            print(f"   • {key}: {value}")
        
        # Verificar sesión activa
        if ejecutor.login_instance.is_logged_in():
            print("   • Estado sesión: ✅ ACTIVA")
        else:
            print("   • Estado sesión: ❌ INACTIVA")
    else:
        print("ℹ️  No hay instancia de login activa")
    
    return True

def main():
    """Función principal del programa"""
    print("\n" + "="*60)
    print("🚀 INICIANDO AUTOMATIZACIÓN ECODIGITAL")
    print("="*60)
    
    # Inicializar helper para logging
    helper = Helpers()
    
    try:
        # Crear instancia del ejecutor
        print("\n🔧 Inicializando sistema...")
        ejecutor = Ejecuciones()
        
        while True:
            mostrar_menu()
            
            try:
                opcion = input("\n📋 Selecciona una opción (1-8): ").strip()
                
                if opcion == "1":
                    ejecutar_flujo_completo(ejecutor)
                    
                elif opcion == "2":
                    solo_login_y_boton(ejecutor)
                    
                elif opcion == "3":
                    prueba_rapida_boton(ejecutor)
                    
                elif opcion == "4":
                    tomar_capturas(ejecutor)
                    
                elif opcion == "5":
                    cerrar_sesion(ejecutor)
                    
                elif opcion == "6":
                    ver_estado_actual(ejecutor)
                    
                elif opcion == "7":
                    print("\n👋 Saliendo del programa...")
                    time.sleep(1)
                    break
                    
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                
                # Pausa entre operaciones
                if opcion != "7":
                    input("\n⏎ Presiona Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Operación interrumpida por el usuario")
                continuar = input("¿Deseas salir? (s/n): ").lower()
                if continuar == 's':
                    break
            
            except Exception as e:
                print(f"\n💥 Error inesperado: {e}")
                helper.human_like_delay(2, 3)
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
        print("El programa no pudo inicializarse correctamente.")
        
    finally:
        print("\n" + "="*60)
        print("🏁 PROGRAMA FINALIZADO")
        print("="*60)
        time.sleep(2)

# Ejemplo de uso directo (sin menú)
if __name__ == "__main__":
    print("\n🧪 INICIANDO AUTOMATIZACIÓN ECODIGITAL")
    print("="*50)
    
    # Opción 1: Ejecutar directamente (descomenta la que necesites)
    
    # 1. Modo interactivo con menú
    main()
    
    # 2. Ejecución directa sin menú (descomenta para usar)
    """
    ejecutor = Ejecuciones()
    resultado = ejecutor.ejecutar_flujo_completo()
    
    if resultado:
        print("\n🎉 ¡EJECUCIÓN EXITOSA!")
    else:
        print("\n💀 ¡EJECUCIÓN FALLIDA!")
    """
    
    # 3. Solo login y click
    """
    ejecutor = Ejecuciones()
    resultado = ejecutor.ejecuta_login_y_boton()
    """
    
    print("\n" + "="*50)
    print("🏁 EJECUCIÓN COMPLETADA")