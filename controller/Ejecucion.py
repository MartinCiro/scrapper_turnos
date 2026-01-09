from controller.BasePlaywright import BasePlaywright
from controller.Login import Login
from controller.utils.Helpers import Helpers
from controller.ExtractorCalendario import ExtractorCalendario

class Ejecuciones(BasePlaywright):
    """
    Clase encargada de ejecutar pruebas y acciones en EcoDigital.
    """

    def __init__(self) -> None:
        """Constructor que inicializa el navegador Playwright"""
        super().__init__()
        self.helper = Helpers()
        self.login_instance = None

    def extraer_y_procesar_calendario(self):
        """
        Extrae y procesa los datos del calendario después del login
        """
        try:
            if not self.login_instance or not self.login_instance.is_logged_in():
                print("❌ No hay sesión activa")
                return None
            
            # Crear extractor pasando la instancia de login
            extractor = ExtractorCalendario(self.login_instance)
            
            # Extraer todos los datos
            datos_calendario = extractor.extraer_todo()
            
            # Mostrar datos extraídos
            extractor.mostrar_datos_extraidos(datos_calendario)
            
            
            return {
                'datos_extraidos': datos_calendario
            }
            
        except Exception as e:
            print(f"💥 Error extrayendo calendario: {e}")
            return None

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
                resultado_login = self.login_instance.login()
                
                if resultado_login:
                    login_exitoso = True
                    print("✅ Login exitoso")
                    
                    # Pequeña pausa para que se estabilice la sesión
                    self.helper.human_like_delay(3, 5)
                    
                    # Verificar URL actual después del login
                    if self.login_instance and self.login_instance.page:
                        self.login_instance.page.url
                    
                    # Hacer click en el botón principal (con verificación de URL)
                    if self.click_boton_principal():
                        print("✅ Click en botón exitoso")
                        
                        # Esperar a que cargue la página del calendario
                        self.helper.human_like_delay(5, 7)
                        
                        # Extraer y procesar calendario
                        return self.extraer_y_procesar_calendario()
                    else:
                        print("⚠️  Login exitoso pero no se pudo hacer click en el botón")
                        
                        # Intentar extraer de todos modos (tal vez ya estamos en la página correcta)
                        print("🔄 Intentando extraer calendario sin click...")
                        resultado_extraccion = self.extraer_y_procesar_calendario()
                        
                        if resultado_extraccion:
                            print("✅ Extracción exitosa incluso sin click en botón")
                            return True
                        else:
                            print("❌ No se pudo extraer calendario")
                            return False
                else:
                    intentos_login += 1
                    print(f"❌ Intento {intentos_login} fallido")
                    
                    if intentos_login < max_intentos:
                        print("⏳ Esperando antes del siguiente intento...")
                        self.helper.human_like_delay(10, 15)
                        
            except Exception as e:
                intentos_login += 1
                print(f"💥 Error en intento {intentos_login}: {str(e)}")
                import traceback
                traceback.print_exc()
                
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
        Verifica si estamos en la URL correcta, si no, navega a ella.
        """
        try:
            if not self.login_instance:
                print("❌ No hay instancia de login")
                return False
            
            page = self.login_instance.page
            current_url = page.url
            
            # Definir la URL objetivo donde debería estar el botón
            url_objetivo = "https://ecodigital.emergiacc.com/WebEcoPresencia/Master#/TurnosAsesor"
            
            # Verificar si ya estamos en la URL correcta
            if url_objetivo in current_url:
                # Intentar hacer click en el botón
                return self._intentar_click_boton()
            else:
                try:
                    page.goto(url_objetivo, wait_until="networkidle", timeout=15000)
                    self.helper.human_like_delay(3, 5)
                    
                    # Verificar que la navegación fue exitosa
                    new_url = page.url
                    
                    if url_objetivo in new_url:
                        # Esperar a que la página cargue completamente
                        page.wait_for_load_state("networkidle")
                        self.helper.human_like_delay(2, 4)
                        
                        # Intentar hacer click en el botón
                        return self._intentar_click_boton()
                    else:
                        # Intentar de todos modos, tal vez sea una redirección válida
                        return self._intentar_click_boton()
                        
                except Exception as nav_error:
                    print(f"❌ Error navegando a la URL objetivo: {nav_error}")
                    
                    # Intentar hacer click de todos modos (tal vez ya estamos en una página válida)
                    print("🔄 Intentando click en el botón de todos modos...")
                    return self._intentar_click_boton()
            
        except Exception as e:
            print(f"💥 Error en click_boton_principal: {str(e)}")
            return False

    def _intentar_click_boton(self):
        """
        Intenta hacer click en el botón usando diferentes estrategias.
        """
        try:
            page = self.login_instance.page
            
            # Lista de posibles selectores para el botón (de más específico a más general)
            boton_selectores = [
                # Selector específico del botón de ver turnos
                "//button[starts-with(@class, 'fc-btnVerCalendarioTurnos-button')]",
                "//button[contains(@class, 'btnVerCalendarioTurnos')]",
                "//button[contains(text(), 'Ver Turnos')]",
                "//button[contains(text(), 'Turnos')]",
                
                # Selector alternativo si es un enlace
                "//a[contains(@class, 'btnVerCalendarioTurnos')]",
                "//a[contains(text(), 'Ver Turnos')]",
                
                # Selector general de botones en el calendario
                "//div[contains(@class, 'fc-toolbar')]//button",
                "//button[contains(@class, 'fc-button')]",
                
                # Selector de última opción
                "//button[not(@disabled)]",
            ]
            
            # Intentar con cada selector
            for i, selector in enumerate(boton_selectores):
                try:
                    # Buscar elemento
                    element = page.query_selector(f"xpath={selector}")
                    
                    if element:
                        # Verificar si es visible
                        if element.is_visible():
                            # Hacer scroll al elemento
                            element.scroll_into_view_if_needed()
                            self.helper.human_like_delay(1, 2)
                            
                            # Intentar click directo
                            try:
                                element.click()
                                
                                # Esperar después del click
                                self.helper.human_like_delay(2, 3)
                                return True
                                
                            except Exception as click_error:
                                print(f"⚠️  Error en click directo: {click_error}")
                                
                                # Intentar con JavaScript
                                page.evaluate("""
                                    (element) => {
                                        element.click();
                                    }
                                """, element)
                                
                                self.helper.human_like_delay(2, 3)
                                return True
                        else:
                            # Intentar hacer scroll para hacerlo visible
                            page.evaluate("""
                                (element) => {
                                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                                }
                            """, element)
                            
                            self.helper.human_like_delay(1, 2)
                            
                            # Verificar si ahora es visible
                            if element.is_visible():
                                print("✅ Botón ahora visible después del scroll")
                                
                                # Intentar click
                                try:
                                    element.click()
                                    print("✅ Click realizado después del scroll")
                                    self.helper.human_like_delay(2, 3)
                                    return True
                                except:
                                    # Click con JavaScript
                                    page.evaluate("(element) => element.click()", element)
                                    print("✅ Click con JavaScript después del scroll")
                                    self.helper.human_like_delay(2, 3)
                                    return True
                            else:
                                print("❌ Botón sigue sin estar visible después del scroll")
                    else:
                        print(f"❌ Elemento no encontrado con este selector")
                        
                except Exception as selector_error:
                    print(f"⚠️  Error con selector {selector[:50]}...: {selector_error}")
                    continue
            
            # Si llegamos aquí, no se pudo hacer click con ningún selector
            print("❌ No se pudo encontrar ni hacer click en ningún botón")
            
            return False
            
        except Exception as e:
            print(f"💥 Error en _intentar_click_boton: {str(e)}")
            return False

    def _click_playwright(self, selector: str) -> bool:
        """
        Intenta hacer click usando métodos nativos de Playwright.
        """
        try:
            # Buscar elemento directamente con Playwright
            element = self.login_instance.page.locator(f"xpath={selector}").first
            if element:
                # Verificar si es visible
                if element.is_visible():
                    # Scroll al elemento
                    element.scroll_into_view_if_needed()
                    self.helper.human_like_delay(1, 2)
                    
                    # Obtener texto
                    """ button_text = element.text_content().strip() if element.text_content() else ""
                    print(f"📝 Texto del botón: {button_text}") """
                    
                    # Hacer click
                    element.click()
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
            ("1. Login", self.ejecuta_login_y_boton)
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