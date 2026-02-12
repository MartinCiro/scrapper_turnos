from controller.BasePlaywright import BasePlaywright
from controller.Login import Login
from controller.utils.Helpers import Helpers
from controller.ExtractorCalendario import ExtractorCalendario

import datetime 

from os import path as os_path, listdir, rmdir, remove
from json import load


class Ejecuciones(BasePlaywright):
    """
    Clase encargada de ejecutar pruebas y acciones en EcoDigital.
    """

    def __init__(self) -> None:
        """Constructor que inicializa el navegador Playwright"""
        super().__init__()
        self.helper = Helpers()
        self.login_instance = None
        self.json_fue_eliminado = False

    def _verificar_y_eliminar_json_antiguo(self, ruta_json):
        """
        Verifica si el JSON tiene más de 2 días usando fecha_generacion y lo elimina.
        Devuelve True si fue eliminado, False si no.
        """
        try:
            if not ruta_json or not os_path.exists(ruta_json):
                print(f"ℹ️  Archivo JSON no existe: {ruta_json}")
                return False
            
            print(f"📁 Verificando antigüedad del JSON: {ruta_json}")
            
            # Leer el JSON para obtener fecha_generacion
            with open(ruta_json, 'r', encoding='utf-8') as f:
                json_data = load(f)
            
            # Obtener fecha_generacion del JSON
            fecha_generacion_str = json_data.get("periodo", {}).get("fecha_generacion")
            
            if not fecha_generacion_str:
                print("⚠️  No se encontró 'fecha_generacion' en el JSON, usando fecha de modificación del archivo")
                # Fallback a fecha de modificación del archivo
                fecha_generacion = datetime.fromtimestamp(os_path.getmtime(ruta_json))
            else:
                try:
                    # Parsear fecha_generacion (formato: YYYY-MM-DD)
                    fecha_generacion = datetime.strptime(fecha_generacion_str, "%Y-%m-%d")
                except ValueError:
                    print(f"⚠️  Formato de fecha_generacion inválido: {fecha_generacion_str}")
                    return False
            
            # Fecha actual
            fecha_actual = datetime.now()
            
            # Calcular diferencia en días
            diferencia_dias = (fecha_actual - fecha_generacion).days
            
            # Mostrar información de fechas
            print(f"📅 Fecha de generación del JSON: {fecha_generacion.strftime('%d/%b/%Y')}")
            print(f"📅 Día actual: {fecha_actual.strftime('%d/%b/%Y')}")
            print(f"📊 Diferencia: {diferencia_dias} días")
            
            # Si han pasado más de 2 días, eliminar
            if diferencia_dias > 2:
                print(f"🗑️  Han pasado {diferencia_dias} días (>2), eliminando JSON...")
                
                # Obtener información del usuario antes de eliminar
                usuario = json_data.get("usuario", {}).get("nombre_completo", "desconocido")
                print(f"📋 JSON a eliminar: Usuario={usuario}, Fecha={fecha_generacion_str}")
                
                # Eliminar el archivo
                remove(ruta_json)
                
                # Verificar que se eliminó
                if not os_path.exists(ruta_json):
                    print(f"✅ JSON eliminado exitosamente: {os_path.basename(ruta_json)}")
                    
                    # Intentar eliminar también el directorio si está vacío
                    try:
                        directorio = os_path.dirname(ruta_json)
                        if os_path.exists(directorio) and not listdir(directorio):
                            rmdir(directorio) 
                            print(f"🗂️  Directorio vacío eliminado: {os_path.basename(directorio)}")
                    except Exception as dir_error:
                        print(f"ℹ️  No se pudo eliminar directorio: {dir_error}")
                    
                    self.json_fue_eliminado = True  # Marcar que eliminamos el JSON
                    return True
                else:
                    print(f"❌ No se pudo eliminar el JSON: {ruta_json}")
                    return False
            else:
                print(f"✅ JSON conservado (diferencia: {diferencia_dias} días ≤ 2)")
                self.json_fue_eliminado = False
                return False
                
        except Exception as e:
            print(f"💥 Error verificando JSON antiguo: {e}")
            import traceback
            traceback.print_exc()
            self.json_fue_eliminado = False
            return False

    def extraer_y_procesar_calendario(self):
        """
        Ejecuta el proceso completo de extracción, comparación y guardado.
        Verifica y elimina JSON antiguo antes de proceder.
        """
        try:
            print("🔄 Iniciando proceso de extracción y procesamiento...")
            
            # Resetear bandera al inicio de cada ejecución
            self.json_fue_eliminado = False
            
            # 1. Verificar si hay JSON antiguo que eliminar
            # Primero necesitamos obtener el nombre del usuario para saber la ruta
            # Creamos una instancia temporal para obtener la ruta
            ruta_json_usuario = None
            if self.login_instance:
                try:
                    extractor_temp = ExtractorCalendario(self.login_instance)
                    
                    # Intentar extraer nombre de usuario si aún no está disponible
                    if not hasattr(extractor_temp, 'nombre_usuario') or not extractor_temp.nombre_usuario:
                        # Intentar extraer desde la página
                        extractor_temp.extraer_nombre_usuario()
                    
                    # Obtener ruta del JSON del usuario
                    ruta_json_usuario = extractor_temp.obtener_ruta_json_usuario()
                    
                    if ruta_json_usuario and os_path.exists(ruta_json_usuario):
                        print("🔍 Verificando antigüedad del JSON existente...")
                        json_eliminado = self._verificar_y_eliminar_json_antiguo(ruta_json_usuario)
                        
                        if json_eliminado:
                            print("🔄 JSON eliminado. Esta será una nueva extracción sin comparación.")
                        else:
                            print("✅ JSON conservado. Se comparará con la versión anterior.")
                    else:
                        print("ℹ️  No existe JSON previo para este usuario")
                        self.json_fue_eliminado = False
                except Exception as e:
                    print(f"⚠️  Error verificando JSON antiguo: {e}")
                    self.json_fue_eliminado = False
            
            # 2. EXTRAER datos del portal
            print("🔄 Extrayendo datos del calendario...")
            extractor = ExtractorCalendario(self.login_instance)
            
            # 3. EJECUTAR proceso simplificado - Pasar información si el JSON fue eliminado
            # Modificamos ExtractorCalendario para aceptar este parámetro
            # Si no podemos modificar ExtractorCalendario, usaremos un workaround
            exito = extractor.ejecutar_proceso_simplificado()
            
            if exito:  # Devuelve True/False
                print("\n🎉 Proceso completado exitosamente")
                
                # Obtener datos actualizados para mostrar resumen
                ruta_json = extractor.obtener_ruta_json_usuario()
                if ruta_json and os_path.exists(ruta_json):
                    with open(ruta_json, 'r', encoding='utf-8') as f:
                        json_data = load(f)
                    
                    # Mostrar fecha de generación
                    fecha_generacion = json_data.get("periodo", {}).get("fecha_generacion", "desconocida")
                    print(f"📅 Fecha de generación del JSON: {fecha_generacion}")
                    
                    # Mostrar mensaje especial si el JSON fue eliminado antes
                    if self.json_fue_eliminado:
                        print("📝 NOTA: Se creó nuevo JSON (el anterior fue eliminado por antigüedad)")
                    
                    if json_data.get("resumen_cambios", {}).get("se_detectaron_cambios", False):
                        print(f"🔄 Cambios detectados: {json_data['resumen_cambios']['total_cambios']} días modificados")
                        print(f"📅 Días con cambios: {json_data['resumen_cambios']['dias_con_cambios']}")
                    else:
                        print(f"✅ Sin cambios detectados")
                
                return {
                    "exito": True,
                    "usuario": extractor.nombre_usuario,
                    "ruta_json": ruta_json,
                    "fecha_generacion": fecha_generacion if 'fecha_generacion' in locals() else None,
                    "json_eliminado": self.json_fue_eliminado
                }
            else:
                print("❌ Error en el proceso")
                return {
                    "exito": False,
                    "error": "No se pudo completar el proceso"
                }
                
        except Exception as e:
            print(f"💥 Error en ejecución: {e}")
            import traceback
            traceback.print_exc()
            return {
                "exito": False,
                "error": str(e)
            }

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
                        
                        if resultado_extraccion and resultado_extraccion.get("exito"):
                            print("✅ Extracción exitosa incluso sin click en botón")
                            return resultado_extraccion
                        else:
                            print("❌ No se pudo extraer calendario")
                            return {
                                "exito": False,
                                "error": "No se pudo extraer calendario"
                            }
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
            return {"exito": True, "mensaje": "Login exitoso pero sin acción del botón"}
        else:
            print("\n💀 EJECUCIÓN FALLIDA: No se pudo hacer login")
            return {"exito": False, "error": "No se pudo hacer login"}

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
            ("1. Login y extracción", self.ejecuta_login_y_boton)
        ]
        
        resultados = {}
        
        for step_name, step_function in steps:
            print(f"\n{'='*50}")
            print(f"PASO: {step_name}")
            print(f"{'='*50}")
            
            try:
                resultado = step_function()
                resultados[step_name] = resultado
                
                if resultado and resultado.get("exito"):
                    print(f"✅ {step_name} - EXITOSO")
                    if resultado.get("fecha_generacion"):
                        print(f"   📅 JSON generado: {resultado['fecha_generacion']}")
                    if resultado.get("json_eliminado"):
                        print(f"   🗑️  JSON anterior eliminado por antigüedad")
                else:
                    print(f"❌ {step_name} - FALLIDO")
                    
            except Exception as e:
                print(f"💥 {step_name} - ERROR: {str(e)}")
                resultados[step_name] = {"exito": False, "error": str(e)}
            
            # Pausa entre pasos
            self.helper.human_like_delay(2, 3)
        
        # Resumen final
        print(f"\n{'='*50}")
        print("📊 RESUMEN DE EJECUCIÓN")
        print(f"{'='*50}")
        
        exitosos = sum(1 for resultado in resultados.values() 
                      if isinstance(resultado, dict) and resultado.get("exito"))
        total = len(resultados)
        
        for paso, resultado in resultados.items():
            if isinstance(resultado, dict) and resultado.get("exito"):
                estado = f"✅ EXITOSO (Usuario: {resultado.get('usuario', 'N/A')})"
                if resultado.get("fecha_generacion"):
                    estado += f" - Fecha: {resultado['fecha_generacion']}"
                if resultado.get("json_eliminado"):
                    estado += " - [JSON RECIÉN CREADO]"
            else:
                estado = "❌ FALLIDO"
                if isinstance(resultado, dict) and resultado.get("error"):
                    estado += f" - Error: {resultado['error']}"
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