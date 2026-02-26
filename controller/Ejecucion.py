from time import sleep
from random import uniform
from json import load, dump
from datetime import datetime
from traceback import print_exc
from os import path as os_path, listdir, rmdir, remove

from controller.Login import Login
from controller.ExtractorCalendario import ExtractorCalendario
from controller.NotificadorTelegram import NotificadorTelegram 

class Ejecuciones:
    """
    Clase orquestadora para el flujo completo de login y extracción de turnos mediante HTTP.
    Versión HTTP - sin dependencia de Playwright ni interacción con UI
    """

    def __init__(self, config):  
        """Constructor"""
        self.config = config  
        self.login_instance = None
        self.extractor_instance = None
        self.json_fue_eliminado = False
        self.json_eliminado_por_mes = False
        self.notificador = NotificadorTelegram(self.config) 

    def _verificar_y_eliminar_json_por_mes(self, ruta_json):
        """
        Verifica si el JSON pertenece a un mes anterior al actual.
        Si es así, lo elimina antes de iniciar el proceso.
        Devuelve True si fue eliminado, False si no.
        """
        try:
            if not ruta_json or not os_path.exists(ruta_json):
                print(f"ℹ️  Archivo JSON no existe: {ruta_json}")
                return False
            
            print(f"📅 Verificando mes del JSON: {ruta_json}")
            
            # Leer el JSON para obtener el mes
            with open(ruta_json, 'r', encoding='utf-8') as f:
                json_data = load(f)
            
            # Obtener mes del JSON (desde periodo.mes o fecha_generacion)
            periodo = json_data.get("periodo", {})
            mes_json_str = periodo.get("mes", "")
            
            if not mes_json_str:
                # Fallback: usar fecha_generacion
                fecha_generacion_str = periodo.get("fecha_generacion")
                if fecha_generacion_str:
                    try:
                        fecha_generacion = datetime.strptime(fecha_generacion_str, "%Y-%m-%d")
                        mes_json = fecha_generacion.month
                        año_json = fecha_generacion.year
                    except:
                        print("⚠️  No se pudo determinar el mes del JSON")
                        return False
                else:
                    print("⚠️  No se encontró información de mes en el JSON")
                    return False
            else:
                # Parsear mes desde string "Febrero 2026"
                try:
                    partes = mes_json_str.split()
                    mes_nombre = partes[0]
                    año_json = int(partes[1])
                    
                    # Mapear nombre de mes a número
                    meses_es = {
                        "Enero": 1, "January": 1, 
                        "Febrero": 2, "February": 2, 
                        "Marzo": 3, "March": 3,
                        "Abril": 4, "April": 4,
                        "Mayo": 5, "May": 5,
                        "Junio": 6, "June": 6,
                        "Julio": 7, "July": 7,
                        "Agosto": 8, "August": 8,
                        "Septiembre": 9, "September": 9,
                        "Octubre": 10, "October": 10,
                        "Noviembre": 11, "November": 11,
                        "Diciembre": 12, "December": 12
                    }
                    mes_json = meses_es.get(mes_nombre, 0)
                    
                    if mes_json == 0:
                        print(f"⚠️  Mes desconocido en JSON: {mes_nombre}")
                        return False
                except Exception as e:
                    print(f"⚠️  Error parseando mes del JSON: {e}")
                    return False
            
            # Obtener mes actual
            mes_actual = datetime.now().month
            año_actual = datetime.now().year
            
            # Mostrar información para debugging
            print(f"📊 Mes del JSON: {mes_json_str} ({mes_json}/{año_json})")
            print(f"📊 Mes actual: {datetime.now().strftime('%B %Y')} ({mes_actual}/{año_actual})")
            
            # Verificar si es mes anterior (considerando cambio de año)
            es_mes_anterior = False
            if año_json < año_actual:
                es_mes_anterior = True
            elif año_json == año_actual and mes_json < mes_actual:
                es_mes_anterior = True
            
            if es_mes_anterior:
                print(f"🗑️  JSON corresponde a mes anterior ({mes_json_str}), eliminando...")
                
                # Obtener información del usuario antes de eliminar
                usuario = json_data.get("usuario", {}).get("nombre_completo", "desconocido")
                print(f"📋 JSON a eliminar: Usuario={usuario}, Mes={mes_json_str}")
                
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
                    
                    self.json_fue_eliminado = True
                    self.json_eliminado_por_mes = True
                    return True
                else:
                    print(f"❌ No se pudo eliminar el JSON: {ruta_json}")
                    return False
            else:
                print(f"✅ JSON corresponde al mes actual ({mes_json_str}), conservado")
                self.json_fue_eliminado = False
                self.json_eliminado_por_mes = False
                return False
                
        except Exception as e:
            print(f"💥 Error verificando mes del JSON: {e}")
            print_exc()
            self.json_fue_eliminado = False
            self.json_eliminado_por_mes = False
            return False

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
                    
                    self.json_fue_eliminado = True
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
            print_exc()
            self.json_fue_eliminado = False
            return False

    def extraer_y_procesar_calendario(self, user_email: str):
        """
        Ejecuta el proceso completo de extracción, comparación y guardado.
        Verifica y elimina JSON antiguo antes de proceder.
        """
        try:
            print("🔄 Iniciando proceso de extracción y procesamiento...")
            
            # Resetear banderas al inicio de cada ejecución
            self.json_fue_eliminado = False
            self.json_eliminado_por_mes = False
            
            # 1. Verificar si hay JSON que eliminar por cambio de mes (PRIORIDAD ALTA)
            # 👇 PASAR config al extractor temporal
            extractor_temp = ExtractorCalendario(None, self.config)  
            ruta_json_usuario = extractor_temp.obtener_ruta_json_usuario()
            
            if ruta_json_usuario and os_path.exists(ruta_json_usuario):
                print("\n🔍 VERIFICANDO CAMBIO DE MES...")
                json_eliminado_por_mes = self._verificar_y_eliminar_json_por_mes(ruta_json_usuario)
                
                if not json_eliminado_por_mes:
                    # Si no se eliminó por mes, verificar antigüedad (>2 días)
                    print("\n🔍 VERIFICANDO ANTIGÜEDAD (>2 días)...")
                    json_eliminado_por_antiguedad = self._verificar_y_eliminar_json_antiguo(ruta_json_usuario)
                    
                    if json_eliminado_por_antiguedad:
                        print("🔄 JSON eliminado por antigüedad (>2 días). Esta será una nueva extracción.")
                    else:
                        print("✅ JSON conservado. Se comparará con la versión anterior.")
                # Si ya se eliminó por mes, no hacer nada más
            else:
                print("ℹ️  No existe JSON previo para este usuario")
                self.json_fue_eliminado = False
            
            # 2. EXTRAER datos del API (ya tenemos sesión en self.login_instance)
            print("\n🔄 Extrayendo datos del calendario vía API...")
            # 👇 PASAR config al extractor
            self.extractor_instance = ExtractorCalendario(
                self.login_instance.get_session(), 
                self.config  
            )
            
            # 3. EJECUTAR proceso simplificado
            exito = self.extractor_instance.ejecutar_proceso_simplificado()
            
            if exito:
                print("\n🎉 Proceso completado exitosamente")
                
                # Obtener datos actualizados para mostrar resumen
                ruta_json = self.extractor_instance.obtener_ruta_json_usuario()
                if ruta_json and os_path.exists(ruta_json):
                    with open(ruta_json, 'r', encoding='utf-8') as f:
                        json_data = load(f)
                    
                    # Mostrar fecha de generación
                    fecha_generacion = json_data.get("periodo", {}).get("fecha_generacion", "desconocida")
                    mes_periodo = json_data.get("periodo", {}).get("mes", "desconocido")
                    print(f"📅 Mes del calendario: {mes_periodo}")
                    print(f"📅 Fecha de generación del JSON: {fecha_generacion}")
                    
                    # Mostrar mensaje especial si el JSON fue eliminado antes
                    if self.json_eliminado_por_mes:
                        print("📝 NOTA: Se creó nuevo JSON (el anterior correspondía a un mes anterior)")
                    elif self.json_fue_eliminado:
                        print("📝 NOTA: Se creó nuevo JSON (el anterior fue eliminado por antigüedad)")
                    
                    # Verificar cambios
                    cambios_detectados = json_data.get("resumen_cambios", {}).get("se_detectaron_cambios", False)
                    if cambios_detectados:
                        total_cambios = json_data['resumen_cambios']['total_cambios']
                        dias_con_cambios = json_data['resumen_cambios']['dias_con_cambios']
                        print(f"🔄 Cambios detectados: {total_cambios} días modificados")
                        print(f"📅 Días con cambios: {dias_con_cambios}")
                    else:
                        print(f"✅ Sin cambios detectados")
                    
                    # ===== ENVIAR NOTIFICACIÓN POR TELEGRAM =====
                    self._enviar_notificacion_telegram(
                        json_data=json_data,
                        cambios_detectados=cambios_detectados,
                        total_cambios=total_cambios,
                        dias_con_cambios=dias_con_cambios,
                        json_eliminado_por_mes=self.json_eliminado_por_mes,
                        json_fue_eliminado=self.json_fue_eliminado
                    )
                
                return {
                    "exito": True,
                    "usuario": self.extractor_instance.nombre_usuario or user_email,
                    "ruta_json": ruta_json,
                    "mes_calendario": mes_periodo if 'mes_periodo' in locals() else None,
                    "fecha_generacion": fecha_generacion if 'fecha_generacion' in locals() else None,
                    "json_eliminado": self.json_fue_eliminado,
                    "json_eliminado_por_mes": self.json_eliminado_por_mes,
                    "cambios_detectados": cambios_detectados,
                    "total_cambios": total_cambios,
                    "dias_con_cambios": dias_con_cambios
                }
            else:
                print("❌ Error en el proceso")
                self.notificador.notificar_error(
                    f"❌ Error en el proceso de extracción\n"
                    f"👤 Usuario: {user_email}\n"
                    f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                )
                return {
                    "exito": False,
                    "error": "No se pudo completar el proceso"
                }
                
        except Exception as e:
            print(f"💥 Error en ejecución: {e}")
            print_exc()
            self.notificador.notificar_error(
                f"💥 Error crítico en ejecución\n"
                f"👤 Usuario: {user_email}\n"
                f"❌ Error: {str(e)[:100]}...\n"
                f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            return {
                "exito": False,
                "error": str(e)
            }

    def _enviar_notificacion_telegram(self, json_data, cambios_detectados, total_cambios, dias_con_cambios, json_eliminado_por_mes, json_fue_eliminado):
        """
        Envía notificación por Telegram según los resultados de la ejecución
        """
        try:
            # Datos básicos
            usuario = json_data.get("usuario", {}).get("nombre_completo", "Desconocido")
            mes = json_data.get("periodo", {}).get("mes", "Desconocido")
            fecha_generacion = json_data.get("periodo", {}).get("fecha_generacion", "Desconocida")
            
            # CABECERA
            mensaje = f"📊 *REPORTE DE EXTRACCIÓN*\n"
            mensaje += f"👤 *Usuario:* {usuario}\n"
            mensaje += f"📅 *Mes:* {mes}\n"
            mensaje += f"🕐 *Fecha:* {fecha_generacion}\n"
            mensaje += "─" * 30 + "\n\n"
            
            # SECCIÓN: Estado del JSON
            if json_eliminado_por_mes:
                mensaje += f"🗑️ *JSON eliminado:* Cambio de mes\n"
                mensaje += f"📝 *Acción:* Nueva extracción\n\n"
            elif json_fue_eliminado:
                mensaje += f"🗑️ *JSON eliminado:* Por antigüedad (>2 días)\n"
                mensaje += f"📝 *Acción:* Nueva extracción\n\n"
            else:
                mensaje += f"📁 *JSON existente:* Conservado\n\n"
            
            # SECCIÓN: Cambios detectados
            if cambios_detectados:
                mensaje += f"🔄 *CAMBIOS DETECTADOS*\n"
                mensaje += f"📊 *Total:* {total_cambios} día(s) modificado(s)\n"
                
                # Detalle de días con cambios (si hay pocos, los listamos)
                if dias_con_cambios and len(dias_con_cambios) <= 10:
                    dias_str = ", ".join([str(d) for d in sorted(dias_con_cambios)])
                    mensaje += f"📅 *Días:* {dias_str}\n"
                elif dias_con_cambios:
                    mensaje += f"📅 *Días:* {len(dias_con_cambios)} días modificados\n"
                
                mensaje += "\n"
                
                # Obtener detalles de los cambios para los primeros 3 días
                if dias_con_cambios and len(dias_con_cambios) > 0:
                    mensaje += f"📋 *Detalles de cambios:*\n"
                    
                    # Limitar a 3 días para no saturar el mensaje
                    dias_a_mostrar = sorted(dias_con_cambios)[:3]
                    calendario = {d["dia"]: d for d in json_data.get("calendario", [])}
                    
                    for dia in dias_a_mostrar:
                        if dia in calendario:
                            dia_info = calendario[dia]
                            cambios_dia = dia_info.get("cambios", {})
                            campos = cambios_dia.get("campos_modificados", [])
                            
                            # Obtener valores anteriores si existen en el historial
                            historial = cambios_dia.get("historial", [])
                            valor_anterior = ""
                            valor_nuevo = ""
                            
                            if historial and len(historial) > 0:
                                detalle = historial[-1].get("detalle", {})
                                if detalle:
                                    antes = detalle.get("antes", {})
                                    despues = detalle.get("despues", {})
                                    
                                    # Formato legible de los cambios
                                    if "turno.horario" in campos:
                                        horario_antes = antes.get("turno", {}).get("horario", "N/A")
                                        horario_despues = despues.get("turno", {}).get("horario", "N/A")
                                        valor_anterior += f"Horario: {horario_antes}\n      "
                                        valor_nuevo += f"Horario: {horario_despues}\n      "
                                    
                                    if "turno.tipo" in campos:
                                        tipo_antes = antes.get("turno", {}).get("tipo", "N/A")
                                        tipo_despues = despues.get("turno", {}).get("tipo", "N/A")
                                        valor_anterior += f"Tipo: {tipo_antes}\n      "
                                        valor_nuevo += f"Tipo: {tipo_despues}\n      "
                                    
                                    if "break.horario" in campos:
                                        break_antes = antes.get("break", {}).get("horario", "N/A")
                                        break_despues = despues.get("break", {}).get("horario", "N/A")
                                        valor_anterior += f"Break: {break_antes}\n      "
                                        valor_nuevo += f"Break: {break_despues}\n      "
                            
                            mensaje += f"  • *Día {dia}*\n"
                            if valor_anterior and valor_nuevo:
                                mensaje += f"    ⬅️ *Antes:* {valor_anterior}\n"
                                mensaje += f"    ➡️ *Después:* {valor_nuevo}\n"
                            else:
                                mensaje += f"    📝 Campos: {', '.join(campos)}\n"
                    
                    if len(dias_con_cambios) > 3:
                        mensaje += f"    ... y {len(dias_con_cambios) - 3} día(s) más\n"
            else:
                mensaje += f"✅ *Sin cambios detectados*\n"
                mensaje += f"📋 El calendario no ha sido modificado desde la última ejecución.\n"
            
            # FOOTER
            mensaje += "\n" + "─" * 30 + "\n"
            mensaje += f"🤖 *Bot Notificador*"
            
            # Enviar mensaje
            self.notificador.enviar_mensaje(mensaje, formato='Markdown')
            
        except Exception as e:
            print(f"⚠️ Error enviando notificación Telegram: {e}")
            # Fallback a notificación simple
            if cambios_detectados:
                self.notificador.notificar_info(
                    f"Se detectaron {total_cambios} cambios en el calendario de {json_data.get('periodo', {}).get('mes', '')}"
                )
            else:
                self.notificador.notificar_exito(
                    f"Extracción completada - Sin cambios en {json_data.get('periodo', {}).get('mes', '')}"
                )

    def ejecuta_login_y_extraccion(self):
        """
        Ejecuta login en EcoDigital y extracción de turnos vía API HTTP.
        ¡SIN INTERACCIÓN CON UI! (no hay clicks, no hay botones)
        """
        print("🚀 Iniciando ejecución en EcoDigital (HTTP)...")
        
        # Configuración de reintentos
        intentos_login = 0
        max_intentos = self.config.max_retries  
        login_exitoso = False
        
        while intentos_login < max_intentos and not login_exitoso:
            try:
                print(f"\n🔄 Intento {intentos_login + 1}/{max_intentos}")
                
                # Inicializar login HTTP (pasando config)
                self.login_instance = Login(self.config)  
                
                # Intentar login
                resultado_login = self.login_instance.login()
                
                if resultado_login:
                    login_exitoso = True
                    print("✅ Login exitoso")
                    
                    # ✅ EXTRAER DIRECTAMENTE DEL API
                    return self.extraer_y_procesar_calendario(self.config.user_eco)  
                else:
                    intentos_login += 1
                    print(f"❌ Intento {intentos_login} fallido")
                    
                    if intentos_login < max_intentos:
                        print("⏳ Esperando antes del siguiente intento...")
                        sleep(uniform(5, 8))
                        
            except Exception as e:
                intentos_login += 1
                print(f"💥 Error en intento {intentos_login}: {str(e)}")
                print_exc()
                
                if intentos_login < max_intentos:
                    print("⏳ Reintentando después de error...")
                    sleep(uniform(5, 8))

        # Resultado final
        if login_exitoso:
            print("\n✅ LOGIN EXITOSO pero sin extracción")
            return {"exito": True, "mensaje": "Login exitoso pero sin extracción"}
        else:
            print("\n💀 EJECUCIÓN FALLIDA: No se pudo hacer login")
            return {"exito": False, "error": "No se pudo hacer login"}

    def ejecutar_flujo_completo(self):
        """
        Ejecuta un flujo completo de prueba (HTTP).
        """
        print("🔁 Iniciando flujo completo de prueba (HTTP)...")
        
        steps = [
            ("1. Login y extracción vía API", self.ejecuta_login_y_extraccion)
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
                    if resultado.get("mes_calendario"):
                        print(f"   📅 Mes del calendario: {resultado['mes_calendario']}")
                    if resultado.get("fecha_generacion"):
                        print(f"   📅 JSON generado: {resultado['fecha_generacion']}")
                    if resultado.get("json_eliminado_por_mes"):
                        print(f"   🗑️  JSON anterior eliminado por cambio de mes")
                    elif resultado.get("json_eliminado"):
                        print(f"   🗑️  JSON anterior eliminado por antigüedad")
                else:
                    print(f"❌ {step_name} - FALLIDO")
                    
            except Exception as e:
                print(f"💥 {step_name} - ERROR: {str(e)}")
                print_exc()
                resultados[step_name] = {"exito": False, "error": str(e)}
            
            # Pausa entre pasos
            sleep(uniform(1, 2))
        
        # Resumen final
        print(f"\n{'='*50}")
        print("📊 RESUMEN DE EJECUCIÓN (HTTP)")
        print(f"{'='*50}")
        
        exitosos = sum(1 for resultado in resultados.values() 
                      if isinstance(resultado, dict) and resultado.get("exito"))
        total = len(resultados)
        
        for paso, resultado in resultados.items():
            if isinstance(resultado, dict) and resultado.get("exito"):
                estado = f"✅ EXITOSO (Usuario: {resultado.get('usuario', 'N/A')})"
                if resultado.get("mes_calendario"):
                    estado += f" - Mes: {resultado['mes_calendario']}"
                if resultado.get("json_eliminado_por_mes"):
                    estado += " - [NUEVO MES]"
                elif resultado.get("json_eliminado"):
                    estado += " - [JSON RECIÉN CREADO]"
            else:
                estado = "❌ FALLIDO"
                if isinstance(resultado, dict) and resultado.get("error"):
                    estado += f" - Error: {resultado['error']}"
            print(f"{paso}: {estado}")
        
        print(f"\n🎯 RESULTADO: {exitosos}/{total} pasos exitosos")
        
        return exitosos == total

    def prueba_rapida_api(self):
        """
        Prueba rápida del endpoint API (usa cookies guardadas si existen).
        """
        print("⚡ Prueba rápida del endpoint API...")
        
        try:
            # Intentar login con cookies primero (más rápido)
            self.login_instance = Login(self.config)  
            
            if self.login_instance.login(use_cookies=True):
                print("✅ Sesión activa con cookies")
                return self.extraer_y_procesar_calendario(self.config.user_eco)  
            else:
                print("❌ No hay sesión activa, haciendo login completo...")
                return self.ejecuta_login_y_extraccion()
                
        except Exception as e:
            print(f"💥 Error en prueba rápida: {str(e)}")
            print_exc()
            return False