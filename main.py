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
    print("3. ❌ Salir")
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
                opcion = input("\n📋 Selecciona una opción (1-3): ").strip()
                
                if opcion == "1":
                    ejecutar_flujo_completo(ejecutor)
                    
                elif opcion == "2":
                    solo_login_y_boton(ejecutor)

                elif opcion == "3":
                    print("\n👋 Saliendo del programa...")
                    time.sleep(1)
                    break
                    
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                
                # Pausa entre operaciones
                if opcion != "6":
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
    print("="*50)

    ejecutor = Ejecuciones()
    resultado = ejecutor.ejecuta_login_y_boton()
    
    if resultado:
        print("\n🎉 ¡EJECUCIÓN EXITOSA!")
    else:
        print("\n💀 ¡EJECUCIÓN FALLIDA!")
    
    print("\n" + "="*50)
    print("🏁 EJECUCIÓN COMPLETADA")