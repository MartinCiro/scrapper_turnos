# main.py - VERSIÓN FINAL SIMPLE
from controller.Config import Config
from controller.Ejecuciones import Ejecuciones
from time import sleep
from random import uniform

def main():
    # 1. Cargar configuración
    config = Config()
    
    # 2. Verificar usuarios
    if not config.users_eco:
        print("❌ No hay usuarios en USERS_ECO")
        return
    
    print(f"\n🚀 Ejecutando {len(config.users_eco)} usuario(s)")
    
    # 3. Iterar
    for i in range(len(config.users_eco)):
        print(f"\n📌 Usuario {i+1}/{len(config.users_eco)}")
        print(f"   Email: {config.users_eco[i]}")
        
        # Asignar credenciales actuales al config
        config.user_eco = config.users_eco[i]
        config.ps_eco = config.passwds_eco[i]
        
        # Ejecutar
        ejecutor = Ejecuciones(config)
        ejecutor.ejecutar_flujo_completo()
        
        # Pausa
        if i < len(config.users_eco) - 1:
            sleep(uniform(3, 6))

if __name__ == "__main__":
    main()