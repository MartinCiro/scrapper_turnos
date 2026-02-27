from glob import glob
from json import dump, load
from requests import Session
from os import path as os_path, makedirs
from datetime import datetime, timedelta
from numpy import zeros, int32 as np_32, array as np_array

from traceback import print_exc

class ExtractorCalendario:
    """
    Clase encargada de extraer datos del calendario de turnos de EcoDigital usando API HTTP.
    Versión HTTP - sin dependencia de Playwright
    """
    
    def __init__(self, session: Session, config):
        """Constructor que inicializa con sesión HTTP"""
        self.session = session
        self.nombre_usuario = None
        self.config = config  # Guardar configuración inyectada

    def extraer_turnos_api(self, fecha_inicio: str = None, fecha_fin: str = None):
        """
        Extrae los turnos directamente del API JSON
        Formato de fechas: "26/1/2026" (día/mes/año)
        """
        try:
            # Calcular fechas si no se proporcionan (mes actual + buffer)
            if not fecha_inicio or not fecha_fin:
                hoy = datetime.now()
                # Inicio: último día del mes anterior
                primer_dia_mes = hoy.replace(day=1)
                fecha_inicio = (primer_dia_mes - timedelta(days=5)).strftime("%d/%m/%Y")
                # Fin: primer día del mes siguiente + buffer
                primer_dia_siguiente = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1)
                fecha_fin = (primer_dia_siguiente + timedelta(days=5)).strftime("%d/%m/%Y")
            
            # Formatear fechas al formato que espera el API (sin ceros iniciales)
            fecha_inicio_fmt = fecha_inicio.replace("/0", "/").lstrip("0")
            fecha_fin_fmt = fecha_fin.replace("/0", "/").lstrip("0")
            
            # 👇 CAMBIO: self.log → self.config.log
            self.config.log.comentario("INFO", f"📡 Consultando API de turnos: {fecha_inicio_fmt} a {fecha_fin_fmt}")
            
            # Headers para el request
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*',
                'Origin': f'{self.config.eco_base_url}',  
                'Referer': f'{self.config.eco_login_url}Master',  
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Payload
            payload = {
                "fechaInicio": fecha_inicio_fmt,
                "fechaFin": fecha_fin_fmt
            }
            
            # Hacer request al API
            response = self.session.post(
                self.config.eco_api_turnos,  
                json=payload,
                headers=headers,
                timeout=self.config.timeout  
            )
            
            if response.status_code != 200:
                self.config.log.error(f"Error en API: {response.status_code}", "GET turnos")  
                return None
            
            # Parsear respuesta JSON
            data = response.json()
            
            self.config.log.comentario("Turnos extraídos exitosamente", "Data turnos")  
            return data
            
        except Exception as e:
            self.config.log.error(f"Error extrayendo turnos del API: {str(e)}", "Extractor turnos")  
            
            print_exc()
            return None

    def procesar_datos_api(self, data_api):
        """
        Procesa la respuesta del API y genera estructuras compatibles con el código anterior
        """
        try:
            if not data_api or 'turnos' not in data_api:
                self.config.log.error("Datos del API inválidos (no contiene 'turnos')", "Sin data turnos")
                if data_api:
                    self.config.log.comentario("INFO", f"Estructura recibida: {list(data_api.keys())}")
                return None
            
            # El API devuelve directamente el objeto JSON con 'turnos' y 'eventos'
            turnos_data = data_api
            
            # Extraer información del usuario del primer turno
            if 'turnos' in turnos_data and len(turnos_data['turnos']) > 0:
                primer_turno = turnos_data['turnos'][0]
                if 'Asesor' in primer_turno and 'NombreCompleto' in primer_turno['Asesor']:
                    nombre_usuario = primer_turno['Asesor']['NombreCompleto']
                    if nombre_usuario:
                        self.config.log.comentario(f"👤 Usuario identificado: {nombre_usuario}", "Usuario identificado")
            
            # Procesar turnos por día
            turnos_por_dia = {}
            
            for turno in turnos_data.get('turnos', []):
                # Extraer fecha del turno (formato: "2026-01-27 02:00")
                fecha_hora_entrada = turno.get('FechaHoraEntradaString', '')
                if not fecha_hora_entrada or ' ' not in fecha_hora_entrada:
                    continue
                
                fecha_str = fecha_hora_entrada.split(' ')[0]
                
                # Parsear fecha
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                    dia_num = fecha.day
                    mes_num = fecha.month
                    año_num = fecha.year
                    
                    # Obtener día de la semana
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    dia_semana = dias_semana[fecha.weekday()]
                    
                    # Determinar si es día libre (Novedad con código 'LIBRE')
                    es_dia_libre = False
                    novedad = turno.get('Novedad')
                    if novedad and novedad.get('Codigo') == 'LIBRE':
                        es_dia_libre = True
                    
                    # Extraer horario del turno (usar strings directamente)
                    horario_entrada = fecha_hora_entrada.split(' ')[1] if ' ' in fecha_hora_entrada else ''
                    fecha_hora_salida = turno.get('FechaHoraSalidaString', '')
                    horario_salida = fecha_hora_salida.split(' ')[1] if ' ' in fecha_hora_salida else ''
                    
                    horario = f"{horario_entrada} - {horario_salida}" if horario_entrada and horario_salida else ''
                    
                    # Determinar tipo de turno
                    tipo = 'Día Libre' if es_dia_libre else 'Dimensionado'
                    
                    # EXTRAER BREAKS CORRECTAMENTE (formato /Date(xxx)/)
                    break_info = None
                    hora_descanso_entrada_str = turno.get('HoraDescanso1Entrada')
                    hora_descanso_salida_str = turno.get('HoraDescanso1Salida')
                    
                    if hora_descanso_entrada_str and hora_descanso_salida_str:
                        # Extraer número del formato /Date(1769491200000)/
                        import re
                        match_entrada = re.search(r'/Date\((\d+)\)/', str(hora_descanso_entrada_str))
                        match_salida = re.search(r'/Date\((\d+)\)/', str(hora_descanso_salida_str))
                        
                        if match_entrada and match_salida:
                            try:
                                # Convertir milisegundos a segundos
                                entrada_ms = int(match_entrada.group(1))
                                salida_ms = int(match_salida.group(1))
                                
                                entrada_break = datetime.fromtimestamp(entrada_ms / 1000)
                                salida_break = datetime.fromtimestamp(salida_ms / 1000)
                                
                                horario_break = f"{entrada_break.strftime('%H:%M')} - {salida_break.strftime('%H:%M')}"
                                duracion_minutos = int((salida_break - entrada_break).total_seconds() / 60)
                                
                                break_info = {
                                    'horario': horario_break,
                                    'duracion_minutos': duracion_minutos
                                }
                            except (ValueError, TypeError) as e:
                                self.config.log.comentario("WARNING", f"⚠️ Error convirtiendo timestamps de break: {e}")
                    
                    # Guardar información del día
                    turnos_por_dia[dia_num] = {
                        'fecha': fecha_str,
                        'dia': dia_num,
                        'mes': mes_num,
                        'año': año_num,
                        'dia_semana': dia_semana,
                        'turno': {
                            'horario': horario,
                            'tipo': tipo,
                            'duracion_horas': self._calcular_duracion_horas(horario)
                        },
                        'break': break_info,
                        'es_dia_libre': es_dia_libre
                    }
                    
                except Exception as e:
                    self.config.log.comentario("WARNING", f"⚠️ Error procesando turno {fecha_str}: {e}")
                    
                    print_exc()
                    continue
            
            self.config.log.comentario(f"Procesados {len(turnos_por_dia)} días con turnos", "Data turnos")
            return turnos_por_dia
            
        except Exception as e:
            self.config.log.error(f"Error procesando datos del API: {str(e)}", "Procesador de datos extraidos")
            
            print_exc()
            return None

    def _calcular_duracion_horas(self, horario: str) -> float:
        """Calcula la duración en horas a partir del string de horario"""
        try:
            if not horario:
                return 0
            
            # Ejemplo: "08:00 - 14:00"
            partes = horario.split(' - ')
            if len(partes) != 2:
                return 6  # Valor por defecto
            
            inicio = datetime.strptime(partes[0].strip(), "%H:%M")
            fin = datetime.strptime(partes[1].strip(), "%H:%M")
            
            duracion = (fin - inicio).total_seconds() / 3600
            return round(duracion, 1)
            
        except Exception:
            return 6  # Valor por defecto

    def generar_estructura_compatible(self, turnos_por_dia):
        """
        Genera estructuras de datos compatibles con el código anterior (matrices 5x7)
        """
        try:
            from datetime import datetime
            
            # Obtener mes y año actual
            hoy = datetime.now()
            mes_actual = hoy.month
            año_actual = hoy.year
            
            # Crear matrices vacías
            numeros_matriz = zeros((5, 7), dtype=np_32)
            eventos_principales = np_array([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            eventos_secundarios = np_array([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            # Mapear días al calendario
            # Primero, obtener el primer día del mes y cuántos días tiene
            import calendar
            primer_dia_mes, dias_en_mes = calendar.monthrange(año_actual, mes_actual)
            
            # Ajustar: lunes = 0 en calendar, pero necesitamos lunes = 0 para nuestra matriz
            # calendar.monthrange devuelve lunes = 0, domingo = 6 (correcto)
            
            # Calcular en qué fila y columna va cada día
            for dia_num in range(1, dias_en_mes + 1):
                # Calcular día de la semana (0=lunes, 6=domingo)
                fecha_dia = datetime(año_actual, mes_actual, dia_num)
                dia_semana = fecha_dia.weekday()  # 0=lunes, 6=domingo
                
                # Calcular fila: (dia_num + offset_del_primer_dia - 1) // 7
                fila = (dia_num + primer_dia_mes - 1) // 7
                columna = dia_semana
                
                # Verificar que la fila esté en rango (0-4)
                if fila < 5:
                    # Guardar número del día
                    numeros_matriz[fila, columna] = dia_num
                    
                    # Si hay turno para este día, guardarlo
                    if dia_num in turnos_por_dia:
                        turno_info = turnos_por_dia[dia_num]
                        
                        if turno_info['es_dia_libre']:
                            eventos_principales[fila, columna] = "Día Libre"
                        elif turno_info['turno']['horario']:
                            # Formato: "08:00 - 14:00 Dimensionado"
                            horario = turno_info['turno']['horario']
                            tipo = turno_info['turno']['tipo']
                            eventos_principales[fila, columna] = f"{horario} {tipo}"
                        
                        # Guardar break si existe
                        if turno_info['break'] and turno_info['break']['horario']:
                            eventos_secundarios[fila, columna] = f"{turno_info['break']['horario']} Break"
            
            # Obtener nombres de días de la semana
            dias_semana = ["Lun.", "Mar.", "Mié.", "Jue.", "Vie.", "Sáb.", "Dom."]
            
            return {
                'nombre_usuario': self.nombre_usuario,
                'dias_semana': dias_semana,
                'numeros_matriz': numeros_matriz,
                'eventos_principales': eventos_principales,
                'eventos_secundarios': eventos_secundarios,
                'es_festivo': zeros((5, 7), dtype=bool),
                'hoy_numero': hoy.day,
                'hoy_fecha': hoy.strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            self.config.log.error(f"Error generando estructura compatible: {str(e)}", "estructra incompatible")
            
            print_exc()
            return None

    def extraer_todo(self):
        """Extrae todos los datos del calendario usando el API"""
        try:
            self.config.log.comentario("INFO", "🔄 Iniciando extracción de turnos desde API...")
            
            # 1. Extraer datos del API
            data_api = self.extraer_turnos_api()
            if not data_api:
                return None
            
            # 2. Procesar datos
            turnos_por_dia = self.procesar_datos_api(data_api)
            if not turnos_por_dia:
                return None
            
            # 3. Generar estructura compatible
            datos_compatibles = self.generar_estructura_compatible(turnos_por_dia)

            self.config.log.comentario("SUCCESS", "Extracción completada exitosamente")
            return datos_compatibles
            
        except Exception as e:
            self.config.log.error(f"Error en extracción completa: {str(e)}", "extraccion de datos completo calendario")
            
            print_exc()
            return None

    def mostrar_datos_extraidos(self, datos):
        """Muestra los datos extraídos de forma organizada"""
        if not datos:
            print("No hay datos para mostrar")
            return
        
        print("\n" + "="*60)
        print("📊 DATOS EXTRAÍDOS DEL CALENDARIO")
        print("="*60)
        
        if datos.get('nombre_usuario'):
            print(f"👤 Usuario: {datos['nombre_usuario']}")
        
        print(f"📅 Fecha de extracción: {datos['hoy_fecha']}")
        print(f"🔢 Día actual: {datos['hoy_numero']}")
        
        # Mostrar días con turnos
        print("\n📋 TURNOS POR DÍA:")
        print("-" * 60)
        
        numeros = datos['numeros_matriz']
        turnos = datos['eventos_principales']
        breaks = datos['eventos_secundarios']
        
        for i in range(5):
            for j in range(7):
                dia_num = numeros[i, j]
                if dia_num > 0:
                    turno = turnos[i, j]
                    break_info = breaks[i, j]
                    
                    if turno or break_info:
                        dia_semana = datos['dias_semana'][j]
                        es_hoy = " ⭐" if dia_num == datos['hoy_numero'] else ""
                        
                        print(f"\n  📅 {dia_semana} {dia_num}{es_hoy}:")
                        if turno:
                            print(f"     🕐 Turno: {turno}")
                        if break_info:
                            print(f"     ☕ Break: {break_info}")
        
        print("\n" + "="*60)

    def obtener_ruta_json_usuario(self):
        """
        Obtiene la ruta del archivo JSON único para el usuario.
        """
        try:
            if not self.nombre_usuario:
                # Usar email como fallback
                nombre_usuario = self.config.user_eco.split('@')[0] if '@' in self.config.user_eco else self.config.user_eco
            
            # Limpiar nombre para usar como directorio
            nombre_limpio = "".join(c for c in self.nombre_usuario if c.isalnum() or c in (' ', '_')).rstrip() if self.nombre_usuario else self.config.user_eco
            nombre_directorio = nombre_limpio.replace(' ', '_').upper()
            
            # Ruta: ./data/usuarios/{NOMBRE_USUARIO}/
            ruta_base = "./data/usuarios"
            ruta_usuario = os_path.join(ruta_base, nombre_directorio)
            
            # Crear directorios si no existen
            makedirs(ruta_usuario, exist_ok=True)
            
            # Nombre del archivo único
            nombre_archivo = "calendario.json"
            ruta_json = os_path.join(ruta_usuario, nombre_archivo)
            
            return ruta_json
            
        except Exception as e:
            print(f"⚠️ Error obteniendo ruta JSON usuario: {e}")
            return None

    def cargar_json_existente(self):
        """
        Carga el JSON existente del usuario (si existe).
        """
        ruta_json = self.obtener_ruta_json_usuario()
        if not ruta_json or not os_path.exists(ruta_json):
            return None
        
        try:
            with open(ruta_json, 'r', encoding='utf-8') as f:
                return load(f)
        except Exception as e:
            print(f"⚠️ Error cargando JSON existente: {e}")
            return None

    def comparar_y_actualizar(self, datos_extractos):
        """
        Compara datos extraídos con JSON existente y actualiza con cambios.
        VERIFICACIÓN ROBUSTA: Confirma existencia física del archivo ANTES de comparar.
        """
        try:
            from os import path as os_path
            from datetime import datetime
            
            # 1. Generar JSON con datos nuevos
            calendario_nuevo = self.generar_json_calendario(datos_extractos)
            if not calendario_nuevo:
                print("No se pudo generar JSON con datos nuevos")
                return None
            
            # 2. OBTENER RUTA Y VERIFICAR EXISTENCIA FÍSICA EN DISCO (¡CRÍTICO!)
            ruta_json = self.obtener_ruta_json_usuario()
            json_existe_en_disco = ruta_json and os_path.exists(ruta_json)
            
            print(f"\n🔍 VERIFICACIÓN FÍSICA DEL JSON:")
            print(f"   Ruta: {ruta_json}")
            print(f"   ¿Existe en disco? {'SÍ' if json_existe_en_disco else 'NO'}")
            
            # 3. EXTRAER MES DEL NUEVO CALENDARIO
            mes_nuevo = calendario_nuevo.get("periodo", {}).get("mes", "")
            año_nuevo = datetime.now().year
            
            # 4. SI NO EXISTE EN DISCO → PRIMERA EXTRACCIÓN (SIN COMPARACIÓN)
            if not json_existe_en_disco:
                print(f"📝 PRIMERA EXTRACCIÓN del mes ({mes_nuevo}) - guardando SIN historial de cambios")
                return self._guardar_calendario_limpio(calendario_nuevo, es_primera_extraccion=True)
            
            # 5. SI EXISTE EN DISCO → CARGAR Y VERIFICAR MES
            calendario_existente = self.cargar_json_existente()
            
            if not calendario_existente:
                print(f"⚠️  JSON existe en disco pero no se pudo cargar - tratando como primera extracción")
                return self._guardar_calendario_limpio(calendario_nuevo, es_primera_extraccion=True)
            
            # 6. EXTRAER MES DEL JSON EXISTENTE
            mes_existente = calendario_existente.get("periodo", {}).get("mes", "")
            
            print(f"   Mes nuevo: {mes_nuevo}")
            print(f"   Mes existente: {mes_existente}")
            
            # 7. SI LOS MESES SON DIFERENTES → NO COMPARAR (eliminar implícitamente)
            if mes_nuevo != mes_existente:
                print(f"🔄 MES DIFERENTE detectado ({mes_existente} → {mes_nuevo}) - guardando SIN comparación")
                return self._guardar_calendario_limpio(calendario_nuevo, es_primera_extraccion=True)
            
            # 8. SI ES EL MISMO MES → COMPARAR NORMALMENTE
            print(f"🔄 Mismo mes ({mes_nuevo}) - comparando con versión anterior...")
            calendario_actualizado = self._detectar_cambios(calendario_existente, calendario_nuevo)
            return self._guardar_json_actualizado(calendario_actualizado)
            
        except Exception as e:
            print(f"Error en comparar_y_actualizar: {e}")
            
            print_exc()
            return None

    def _guardar_calendario_limpio(self, calendario, es_primera_extraccion=True):
        """
        Guarda el calendario SIN historial de cambios (para primera extracción del mes).
        """
        try:
            # Limpiar cualquier rastro de cambios en TODOS los días
            for dia in calendario.get("calendario", []):
                dia["cambios"] = {
                    "ha_cambiado": False,
                    "detalle_cambios": None,
                    "campos_modificados": [],
                    "ultima_modificacion": None,
                    "historial": []
                }
            
            # Limpiar metadata de cambios
            calendario["metadata"]["tiene_cambios_versiones_anteriores"] = False
            calendario["metadata"]["ultima_comparacion"] = None
            
            # Resumen de cambios limpio
            calendario["resumen_cambios"] = {
                "ultima_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_cambios": 0,
                "dias_con_cambios": [],
                "dias_eliminados": [],
                "se_detectaron_cambios": False
            }
            
            # Guardar SIN crear backup (es primera extracción)
            ruta_json = self.obtener_ruta_json_usuario()
            if not ruta_json:
                print("No se pudo obtener ruta para guardar JSON")
                return False
            
            # Eliminar backup previo si existe (evitar acumulación)
            if os_path.exists(ruta_json):
                try:
                    from os import remove
                    remove(ruta_json)
                    print(f"🗑️  JSON anterior eliminado antes de guardar nuevo")
                except Exception as e:
                    print(f"⚠️  No se pudo eliminar JSON anterior: {e}")
            
            # Guardar nuevo JSON
            with open(ruta_json, 'w', encoding='utf-8') as f:
                dump(calendario, f, ensure_ascii=False, indent=2)
            
            if es_primera_extraccion:
                print(f"Calendario GUARDADO (primera extracción del mes): {ruta_json}")
            else:
                print(f"Calendario actualizado SIN cambios: {ruta_json}")
            
            return True
            
        except Exception as e:
            print(f"Error guardando calendario limpio: {e}")
            return False

    def _detectar_cambios(self, calendario_antiguo, calendario_nuevo):
        """
        Detecta cambios entre dos versiones del calendario y los marca.
        """
        try:
            # Crear copia del nuevo calendario para modificarlo
            calendario_actualizado = calendario_nuevo.copy()
            
            # Crear diccionarios por día para fácil acceso
            dias_antiguos = {d["dia"]: d for d in calendario_antiguo["calendario"]}
            dias_nuevos = {d["dia"]: d for d in calendario_actualizado["calendario"]}
            
            cambios_detectados = False
            total_cambios = 0
            dias_con_cambios = []
            dias_eliminados = []
            
            # 1. Comparar días existentes en el nuevo calendario
            for dia_num, dia_nuevo in dias_nuevos.items():
                dia_antiguo = dias_antiguos.get(dia_num)
                cambios_dia = []
                cambio_detectado = False
                
                if not dia_antiguo:
                    # Día nuevo (no existía antes)
                    cambios_dia = ["nuevo_dia"]
                    cambio_detectado = True
                else:
                    # Comparar campos específicos
                    # a) Turno
                    turno_antiguo = dia_antiguo.get("turno", {})
                    turno_nuevo = dia_nuevo.get("turno", {})
                    
                    if turno_antiguo.get("horario") != turno_nuevo.get("horario"):
                        cambios_dia.append("turno.horario")
                    
                    if turno_antiguo.get("tipo") != turno_nuevo.get("tipo"):
                        cambios_dia.append("turno.tipo")
                    
                    # b) Break
                    break_antiguo = dia_antiguo.get("break", {})
                    break_nuevo = dia_nuevo.get("break", {})
                    
                    # Verificar existencia real de break (horario no nulo)
                    existe_break_antiguo = break_antiguo.get("horario") is not None
                    existe_break_nuevo = break_nuevo.get("horario") is not None
                    
                    if existe_break_antiguo != existe_break_nuevo:
                        cambios_dia.append("break.existencia")
                    
                    if existe_break_antiguo and existe_break_nuevo:
                        if break_antiguo.get("horario") != break_nuevo.get("horario"):
                            cambios_dia.append("break.horario")
                        if break_antiguo.get("duracion_minutos") != break_nuevo.get("duracion_minutos"):
                            cambios_dia.append("break.duracion")
                    
                    # c) Día libre
                    es_libre_antiguo = dia_antiguo.get("es_dia_libre", False)
                    es_libre_nuevo = dia_nuevo.get("es_dia_libre", False)
                    
                    if es_libre_antiguo != es_libre_nuevo:
                        cambios_dia.append("es_dia_libre")
                        # Si cambia estado de día libre, los campos de turno también cambian
                        if es_libre_nuevo:
                            cambios_dia.extend(["turno.horario", "turno.tipo"])
                
                # Si hay cambios, actualizar información
                if cambios_dia:
                    cambio_detectado = True
                    total_cambios += 1
                    dias_con_cambios.append(dia_num)
                    
                    # Obtener historial anterior
                    historial_anterior = dia_antiguo.get("cambios", {}).get("historial", []) if dia_antiguo else []
                    
                    # Crear nueva entrada de historial
                    nueva_entrada = {
                        "fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "cambio": f"Modificados: {', '.join(cambios_dia)}",
                        "detalle": {}
                    }
                    
                    if dia_antiguo:
                        nueva_entrada["detalle"] = {
                            "antes": {
                                "turno": dia_antiguo.get("turno"),
                                "break": dia_antiguo.get("break"),
                                "es_dia_libre": dia_antiguo.get("es_dia_libre")
                            },
                            "despues": {
                                "turno": dia_nuevo.get("turno"),
                                "break": dia_nuevo.get("break"),
                                "es_dia_libre": dia_nuevo.get("es_dia_libre")
                            }
                        }
                    
                    # Actualizar información de cambios
                    dia_nuevo["cambios"] = {
                        "ha_cambiado": True,
                        "detalle_cambios": f"Cambios en: {', '.join(cambios_dia)}",
                        "campos_modificados": cambios_dia,
                        "ultima_modificacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "historial": historial_anterior + [nueva_entrada]
                    }
                else:
                    # Sin cambios - mantener historial anterior
                    historial_previo = []
                    if dia_antiguo and "cambios" in dia_antiguo:
                        historial_previo = dia_antiguo["cambios"].get("historial", [])
                    
                    dia_nuevo["cambios"] = {
                        "ha_cambiado": False,
                        "detalle_cambios": None,
                        "campos_modificados": [],
                        "ultima_modificacion": None,
                        "historial": historial_previo
                    }
                
                if cambio_detectado:
                    cambios_detectados = True
            
            # 2. Detectar días eliminados (existen en antiguo pero no en nuevo)
            for dia_num, dia_antiguo in dias_antiguos.items():
                if dia_num not in dias_nuevos:
                    dias_eliminados.append(dia_num)
                    total_cambios += 1
                    cambios_detectados = True
            
            # 3. Actualizar metadata con información de cambios
            calendario_actualizado["metadata"]["tiene_cambios_versiones_anteriores"] = cambios_detectados
            calendario_actualizado["metadata"]["ultima_comparacion"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            calendario_actualizado["metadata"]["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # 4. Añadir resumen de cambios
            resumen = {
                "ultima_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_cambios": total_cambios,
                "dias_con_cambios": dias_con_cambios,
                "dias_eliminados": dias_eliminados,
                "se_detectaron_cambios": cambios_detectados
            }
            
            calendario_actualizado["resumen_cambios"] = resumen
            
            # Mensajes de feedback
            if cambios_detectados:
                if dias_con_cambios:
                    print(f"🔄 Detectados {len(dias_con_cambios)} días modificados: {dias_con_cambios}")
                if dias_eliminados:
                    print(f"🗑️  Detectados {len(dias_eliminados)} días eliminados: {dias_eliminados}")
            else:
                print("Sin cambios detectados respecto a la versión anterior")
            
            return calendario_actualizado
            
        except Exception as e:
            print(f"Error grave detectando cambios: {e}")
            
            print_exc()
            # En caso de error, mantener el nuevo calendario sin cambios
            return calendario_nuevo

    def _guardar_json_actualizado(self, calendario, es_primera_extraccion=False):
        """
        Guarda el JSON actualizado.
        es_primera_extraccion: True si es la primera extracción del mes (evita mensajes de "cambios")
        """
        try:
            ruta_json = self.obtener_ruta_json_usuario()
            if not ruta_json:
                print("No se pudo obtener ruta para guardar JSON")
                return False
            
            # Crear backup SOLO si NO es primera extracción
            if os_path.exists(ruta_json) and not es_primera_extraccion:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_backup = ruta_json.replace(".json", f"_backup_{timestamp}.json")
                from shutil import copy2
                copy2(ruta_json, ruta_backup)
                print(f"💾 Backup creado: {os_path.basename(ruta_backup)}")
            
            # Guardar nuevo JSON
            with open(ruta_json, 'w', encoding='utf-8') as f:
                dump(calendario, f, ensure_ascii=False, indent=2)
            
            # Mensaje apropiado según contexto
            if es_primera_extraccion:
                print(f"Calendario GUARDADO (primera extracción del mes): {ruta_json}")
            else:
                print(f"Calendario actualizado guardado: {ruta_json}")
            
            # Limpiar backups solo si no es primera extracción
            if not es_primera_extraccion:
                self._limpiar_backups_viejos(ruta_json)
            
            return True
            
        except Exception as e:
            print(f"Error guardando JSON actualizado: {e}")
            return False

    def _limpiar_backups_viejos(self, ruta_json_principal):
        """
        Limpia backups viejos, manteniendo solo los 2 más recientes.
        """
        try:
            directorio = os_path.dirname(ruta_json_principal)
            nombre_base = os_path.basename(ruta_json_principal).replace(".json", "")
            
            # Buscar todos los backups
            patron_backup = os_path.join(directorio, f"{nombre_base}_backup_*.json")
            backups = glob(patron_backup)
            
            # Ordenar por fecha (más reciente primero)
            backups.sort(key=os_path.getmtime, reverse=True)
            
            # Mantener solo 1 backup más recientes
            for backup in backups[1:]:
                try:
                    import os
                    os.remove(backup)
                    print(f"🗑️  Eliminado backup antiguo: {os_path.basename(backup)}")
                except Exception as e:
                    print(f"⚠️  Error eliminando backup {backup}: {e}")
                    
        except Exception as e:
            print(f"⚠️  Error limpiando backups: {e}")

    def generar_json_calendario(self, datos_extractos):
        """
        Genera la estructura JSON básica del calendario.
        """
        try:
            # Información del usuario
            nombre_usuario = datos_extractos.get('nombre_usuario', 'Usuario Desconocido')
            
            usuario_info = {
                "id": nombre_usuario.upper().replace(" ", "_") if nombre_usuario else self.config.user_eco.upper().replace("@", "_").replace(".", "_"),
                "nombre_completo": nombre_usuario if nombre_usuario else self.config.user_eco
            }
            
            # Información del período
            periodo_info = {
                "mes": datetime.now().strftime("%B %Y"),
                "dias_totales": 0,
                "dias_laborables": 0,
                "dias_libres": 0,
                "fecha_generacion": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Calendario detallado
            calendario_detallado = []
            numeros = datos_extractos['numeros_matriz']
            
            # Mapeo simple de días abreviados a completos
            dias_semana_completos = {
                "Lun.": "Lunes", "Mar.": "Martes", "Mié.": "Miércoles",
                "Jue.": "Jueves", "Vie.": "Viernes", "Sáb.": "Sábado",
                "Dom.": "Domingo"
            }
            
            for i in range(5):
                for j in range(7):
                    dia_num = numeros[i, j]
                    if dia_num > 0:
                        # Actualizar contadores
                        periodo_info["dias_totales"] += 1
                        
                        turno_raw = datos_extractos['eventos_principales'][i, j]
                        break_raw = datos_extractos['eventos_secundarios'][i, j]
                        
                        # Obtener día de la semana
                        dia_semana_key = datos_extractos['dias_semana'][j] if j < len(datos_extractos['dias_semana']) else f"Día {j+1}"
                        dia_semana = dias_semana_completos.get(dia_semana_key, dia_semana_key)
                        
                        # Determinar si es día libre
                        es_dia_libre = turno_raw == "Día Libre" if turno_raw else False
                        
                        if es_dia_libre:
                            periodo_info["dias_libres"] += 1
                            turno_info = {
                                "horario": None,
                                "tipo": "Día Libre",
                                "duracion_horas": 0
                            }
                        else:
                            periodo_info["dias_laborables"] += 1
                            # Extraer información básica del turno
                            turno_info = {
                                "horario": turno_raw.split()[0] + ":00 - " + turno_raw.split()[2] + ":00" if turno_raw and len(turno_raw.split()) >= 3 else None,
                                "tipo": " ".join(turno_raw.split()[3:]) if turno_raw and len(turno_raw.split()) > 3 else "Dimensionado",
                                "duracion_horas": 6  # Valor por defecto
                            }
                        
                        # Información del break
                        break_info = {
                            "horario": break_raw.split("Break")[0].strip() if break_raw else None,
                            "duracion_minutos": 20  # Valor por defecto
                        }
                        
                        dia_info = {
                            "dia": int(dia_num),
                            "dia_semana": dia_semana,
                            "turno": turno_info,
                            "break": break_info,
                            "es_dia_libre": es_dia_libre,
                            "cambios": {
                                "ha_cambiado": False,
                                "detalle_cambios": None,
                                "campos_modificados": [],
                                "ultima_modificacion": None,
                                "historial": []
                            }
                        }
                        
                        calendario_detallado.append(dia_info)
            
            # Ordenar por día
            calendario_detallado.sort(key=lambda x: x["dia"])
            
            # Metadata con fecha y hora de última ejecución
            metadata = {
                "version": "1.0",
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tiene_cambios_versiones_anteriores": False
            }
            
            # Estructura completa
            calendario_json = {
                "usuario": usuario_info,
                "periodo": periodo_info,
                "calendario": calendario_detallado,
                "estadisticas": {},
                "metadata": metadata
            }
            
            return calendario_json
            
        except Exception as e:
            print(f"Error generando JSON: {e}")
            
            print_exc()
            return None

    def ejecutar_proceso_simplificado(self):
        """
        Ejecuta el proceso simplificado: extraer, comparar y actualizar un solo archivo.
        """
        try:
            print("🔄 Extrayendo datos del calendario...")
            
            # 1. Extraer datos
            datos = self.extraer_todo()
            
            if not datos:
                print("Error extrayendo datos")
                return None
            
            # 2. Mostrar datos extraídos
            self.mostrar_datos_extraidos(datos)
            
            # 3. Verificar si el JSON existe ANTES de comparar
            ruta_json = self.obtener_ruta_json_usuario()
            json_existe = ruta_json and os_path.exists(ruta_json)
            
            # 4. Comparar y actualizar archivo único
            resultado = self.comparar_y_actualizar(datos)
            
            if resultado:                
                # Mostrar resumen de cambios si existe
                if ruta_json and os_path.exists(ruta_json):
                    with open(ruta_json, 'r', encoding='utf-8') as f:
                        json_data = load(f)
                    
                    # Si el JSON no existía antes, es una nueva extracción
                    if not json_existe:
                        print("📝 Nueva extracción (no existía JSON anterior)")
                    elif json_data.get("resumen_cambios", {}).get("se_detectaron_cambios", False):
                        print("🔄 Cambios detectados respecto a versión anterior")
                    else:
                        print("Sin cambios en esta ejecución")
                
                return resultado
            else:
                print("Error en el proceso")
                return None
                
        except Exception as e:
            print(f"💥 Error en ejecución: {e}")
            
            print_exc()
            return None