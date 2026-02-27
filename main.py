# main.py
from controller.Config import Config
from controller.Ejecuciones import Ejecuciones
from time import sleep
from random import uniform

def main():
    # 1. Cargar configuración base
    config = Config()
    
    # 2. Verificar usuarios
    if not config.users_eco:
        print("❌ No hay usuarios configurados")
        return
    
    total_usuarios = len(config.users_eco)
    print(f"\n{'='*60}")
    print(f"🚀 INICIANDO EJECUCIÓN PARA {total_usuarios} USUARIO(S)")
    print(f"{'='*60}")
    
    # 3. Iterar sobre cada usuario
    for i in range(total_usuarios):
        # Obtener credenciales de este usuario
        usuario = config.users_eco[i]
        password = config.passwds_eco[i]
        
        print(f"\n{'='*50}")
        print(f"👤 USUARIO {i+1}/{total_usuarios}: {usuario}")
        print(f"{'='*50}")
        
        try:
            # ASIGNAR ESTE USUARIO COMO ACTUAL
            config.user_eco = usuario
            config.ps_eco = password
            
            # Mostrar rutas para este usuario
            print(f"📁 Cookies: {config._get_user_cookies_path()}")
            print(f"📁 Datos: {config.get_user_data_path()}")
            print(f"📄 JSON: {config.get_user_json_path()}")
            
            # Ejecutar el flujo para ESTE usuario
            ejecutor = Ejecuciones(config)
            resultado = ejecutor.ejecutar_flujo_completo()
            
            if resultado and resultado.get("exito"):
                print(f"✅ Usuario {usuario}: EXITOSO")
            else:
                print(f"❌ Usuario {usuario}: FALLIDO")
                
        except Exception as e:
            print(f"💥 Error procesando {usuario}: {e}")
            import traceback
            traceback.print_exc()
        
        # Pausa entre usuarios
        if i < total_usuarios - 1:
            pausa = uniform(3, 6)
            print(f"⏳ Esperando {pausa:.1f}s antes del siguiente usuario...")
            sleep(pausa)
    
    print(f"\n{'='*60}")
    print("✅ PROCESO COMPLETADO PARA TODOS LOS USUARIOS")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()