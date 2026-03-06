# main.py
from controller.Config import Config
from controller.Ejecucion import Ejecuciones
from time import sleep
from random import uniform
from traceback import print_exc

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
        
        # ASIGNAR ESTE USUARIO COMO ACTUAL
        config.user_eco = usuario
        config.ps_eco = password
        
        try:
            # Ejecutar el flujo para ESTE usuario
            ejecutor = Ejecuciones(config)
            resultado = ejecutor.ejecutar_flujo_completo()
            # 🔥 Si falla por sesión, intentar una vez más con login fresco
            if not resultado.get("exito"):
                error_msg = str(resultado.get("error", ""))
                if "NOSESS" in error_msg or "sesión" in error_msg.lower() or "login" in error_msg.lower():
                    if hasattr(ejecutor, 'login_instance') and ejecutor.login_instance:
                        ejecutor.login_instance.session.cookies.clear()
                    resultado_reintento = ejecutor.ejecuta_login_y_extraccion()
                    # Normalizar también el reintento
                    if isinstance(resultado_reintento, bool):
                        resultado = {"exito": resultado_reintento, "error": None if resultado_reintento else "Reintento fallido"}
                    else:
                        resultado = resultado_reintento
            
            print(f"✅ {usuario}: EXITOSO" if resultado and resultado.get("exito") else f"❌ {usuario}: FALLIDO")
            
        except Exception as e:
            print(f"💥 Error procesando {usuario}: {e}")
            print_exc()
        
        # Pausa entre usuarios (excepto el último)
        if i < total_usuarios - 1:
            pausa = uniform(3, 6)
            print(f"⏳ Esperando {pausa:.1f}s antes del siguiente usuario...")
            sleep(pausa)
    
    print(f"\n{'='*60}")
    print("✅ PROCESO COMPLETADO PARA TODOS LOS USUARIOS")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
