from controller.BasePlaywright import BasePlaywright
from controller.Login import Login
from controller.utils.Helpers import Helpers
import time
import random

class Ejecuciones(BasePlaywright):
    """
    Clase encargada de ejecutar pruebas y acciones en EcoDigital.
    """

    def __init__(self) -> None:
        """Constructor que inicializa el navegador Playwright"""
        super().__init__()
        self.helper = Helpers()
        self.login_instance = None

    def ejecuta_login_y_boton(self):
        """
        Ejecuta login en EcoDigital y hace click en el botón principal.
        """
        print("🚀 Iniciando ejecución en EcoDigital...")
        
        # Configuración de reintentos
        intentos_login = 0
        max_intentos = 3
        login_exitoso = False
        
        while intentos_login < max_intentos and not login_exitoso:
            try:
                print(f"\n🔄 Intento {intentos_login + 1}/{max_intentos}")
                
                # Inicializar login
                self.login_instance = Login()
                
                # Intentar login
                if self.login_instance.login():
                    login_exitoso = True
                    print(f"✅ Login exitoso en el intento {intentos_login + 1}")
                    
                    # Mostrar estado
                    estado = self.login_instance.get_login_status()
                    print(f"📊 Estado: {estado}")
                    
                    # Hacer click en el botón principal
                    if self.click_boton_principal():
                        print("🎉 EJECUCIÓN COMPLETA: Login + Click exitosos")
                        return True
                    else:
                        print("⚠️  Login exitoso pero no se pudo hacer click en el botón")
                        
                else:
                    intentos_login += 1
                    print(f"❌ Intento {intentos_login} fallido")
                    
                    if intentos_login < max_intentos:
                        print("⏳ Esperando antes del siguiente intento...")
                        self.helper.human_like_delay(10, 15)
                        
            except Exception as e:
                intentos_login += 1
                print(f"💥 Error en intento {intentos_login}: {str(e)}")
                
                if intentos_login < max_intentos:
                    print("⏳ Reintentando después de error...")
                    self.helper.human_like_delay(10, 15)

        # Resultado final
        if login_exitoso:
            print("\n✅ LOGIN EXITOSO pero sin acción del botón")
            return True
        else:
            print("\n💀 EJECUCIÓN FALLIDA: No se pudo hacer login")
            return False

    def click_boton_principal(self):
        """
        Hace click en el botón principal de calendario de turnos.
        """
        try:
            print("🖱️  Buscando botón principal...")
            
            # Selector específico del botón
            boton_selector = "//button[starts-with(@class, 'fc-btnVerCalendarioTurnos-button')]"
            
            # Intentar con Playwright directamente (sin JavaScript)
            if self._click_playwright(boton_selector):
                print("✅ Click con Playwright exitoso")
                return True
            else:
                print("❌ No se pudo hacer click con Playwright")
                return False
                    
        except Exception as e:
            print(f"💥 Error haciendo click: {str(e)}")
            return False

    def _click_playwright(self, selector: str) -> bool:
        """
        Intenta hacer click usando métodos nativos de Playwright.
        """
        try:
            # Buscar elemento directamente con Playwright
            element = self.login_instance.page.locator(f"xpath={selector}").first
            if element:
                print(f"✅ Botón encontrado con XPath: {selector}")
                
                # Verificar si es visible
                if element.is_visible():
                    print("✅ Botón visible")
                    
                    # Scroll al elemento
                    element.scroll_into_view_if_needed()
                    self.helper.human_like_delay(1, 2)
                    
                    # Obtener texto
                    button_text = element.text_content().strip() if element.text_content() else ""
                    print(f"📝 Texto del botón: {button_text}")
                    
                    # Hacer click
                    element.click()
                    print("✅ Click realizado")
                    return True
                else:
                    print("❌ Botón no visible")
                    return False
            else:
                print(f"❌ No se encontró el botón: {selector}")
                return False
                    
        except Exception as e:
            print(f"⚠️  Click Playwright falló: {e}")
            return False
        
    def ejecutar_flujo_completo(self):
        """
        Ejecuta un flujo completo de prueba.
        """
        print("🔁 Iniciando flujo completo de prueba...")
        
        steps = [
            ("1. Login", self.ejecuta_login_y_boton),
            ("2. Verificar estado", self.verificar_estado_sistema),
            ("3. Tomar captura", self.tomar_captura_evidencia),
            ("4. Logout", self.ejecutar_logout)
        ]
        
        resultados = {}
        
        for step_name, step_function in steps:
            print(f"\n{'='*50}")
            print(f"PASO: {step_name}")
            print(f"{'='*50}")
            
            try:
                resultado = step_function()
                resultados[step_name] = resultado
                
                if resultado:
                    print(f"✅ {step_name} - EXITOSO")
                else:
                    print(f"❌ {step_name} - FALLIDO")
                    
            except Exception as e:
                print(f"💥 {step_name} - ERROR: {str(e)}")
                resultados[step_name] = False
            
            # Pausa entre pasos
            if step_name != "4. Logout":
                self.helper.human_like_delay(3, 5)
        
        # Resumen final
        print(f"\n{'='*50}")
        print("📊 RESUMEN DE EJECUCIÓN")
        print(f"{'='*50}")
        
        exitosos = sum(1 for resultado in resultados.values() if resultado)
        total = len(resultados)
        
        for paso, resultado in resultados.items():
            estado = "✅ EXITOSO" if resultado else "❌ FALLIDO"
            print(f"{paso}: {estado}")
        
        print(f"\n🎯 RESULTADO: {exitosos}/{total} pasos exitosos")
        
        return exitosos == total

    def verificar_estado_sistema(self):
        """
        Verifica el estado general del sistema después del login.
        """
        try:
            if not self.login_instance:
                print("❌ No hay instancia de login activa")
                return False
            
            # Verificar si sigue logueado
            if not self.login_instance.is_logged_in():
                print("❌ Sesión perdida")
                return False
            
            # Verificar elementos importantes
            elementos_verificar = [
                "//div[contains(@class, 'panel-asignacion')]",
                "//h3[contains(text(), 'Turnos')]",
                "//div[@id='main-container']"
            ]
            
            encontrados = 0
            for selector in elementos_verificar:
                if self.login_instance._check_any_xpath_exists([selector], 2000):
                    encontrados += 1
                    print(f"✅ Elemento encontrado: {selector[:50]}...")
            
            print(f"📊 {encontrados}/{len(elementos_verificar)} elementos críticos presentes")
            
            # Tomar screenshot de estado
            self.login_instance.page.screenshot(
                path=f"./estado_sistema_{self.helper.get_current_timestamp()}.png",
                full_page=False
            )
            
            return encontrados >= 2  # Al menos 2 elementos críticos
            
        except Exception as e:
            print(f"⚠️  Error verificando estado: {e}")
            return False

    def tomar_captura_evidencia(self):
        """
        Toma capturas de pantalla como evidencia.
        """
        try:
            if not self.login_instance:
                return False
            
            timestamp = self.helper.get_current_timestamp()
            
            # Captura de pantalla completa
            self.login_instance.page.screenshot(
                path=f"./evidencia_completa_{timestamp}.png",
                full_page=True
            )
            
            # Captura del viewport
            self.login_instance.page.screenshot(
                path=f"./evidencia_viewport_{timestamp}.png",
                full_page=False
            )
            
            print(f"📸 Capturas guardadas con timestamp: {timestamp}")
            return True
            
        except Exception as e:
            print(f"⚠️  Error tomando capturas: {e}")
            return False

    def ejecutar_logout(self):
        """
        Ejecuta logout del sistema.
        """
        try:
            if not self.login_instance:
                return False
            
            print("🚪 Ejecutando logout...")
            
            if self.login_instance.logout():
                print("✅ Logout exitoso")
                return True
            else:
                print("❌ No se pudo hacer logout")
                return False
                
        except Exception as e:
            print(f"💥 Error en logout: {e}")
            return False

    def prueba_rapida_boton(self):
        """
        Prueba rápida solo del botón (asume que ya hay sesión activa).
        """
        print("⚡ Prueba rápida del botón principal...")
        
        try:
            # Verificar si hay sesión activa
            if not self.login_instance or not self.login_instance.is_logged_in():
                print("❌ No hay sesión activa, haciendo login primero...")
                if not self.ejecuta_login_y_boton():
                    return False
            
            # Probar el botón
            if self.click_boton_principal():
                print("✅ PRUEBA RÁPIDA EXITOSA")
                return True
            else:
                print("❌ PRUEBA RÁPIDA FALLIDA")
                return False
                
        except Exception as e:
            print(f"💥 Error en prueba rápida: {str(e)}")
            return False

# Función principal de ejecución
if __name__ == "__main__":
    print("🔧 Iniciando ejecutor de EcoDigital...")
    
    # Crear instancia del ejecutor
    ejecutor = Ejecuciones()
    
    # Ejecutar flujo completo
    resultado = ejecutor.ejecutar_flujo_completo()
    
    if resultado:
        print("\n🎊 ¡FLUJO COMPLETADO CON ÉXITO!")
    else:
        print("\n💀 ¡FLUJO FALLIDO!")
    
    # Pausa antes de cerrar
    time.sleep(3)