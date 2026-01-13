from controller.BasePlaywright import BasePlaywright
from controller.utils.Helpers import Helpers
from numpy import array as ar, zeros, int32
from datetime import datetime
from os import path as os_path, makedirs, remove
from glob import glob
from json import dump, load

class ExtractorCalendario(BasePlaywright):
    """
    Clase encargada de extraer datos del calendario de turnos de EcoDigital.
    """
    
    def __init__(self, login_instance=None):
        """Constructor que inicializa el navegador Playwright"""
        super().__init__()
        self.helper = Helpers()
        self.login_instance = login_instance
        
        # Selectores base para extracción de datos del calendario
        self.selectores_base = {
            # Días de la semana (Lun, Mar, Mié, Jue, Vie, Sáb, Dom)
            "dias_semana": "//th[contains(@class, 'fc-day-header')]",
            
            # Números de día - plantilla con {fila} dinámico
            "numeros_fila": "//div[contains(@class, 'fc-row')][{fila}]//td[contains(@class, 'fc-day-number')]",

            # Números de día SOLO del mes actual (sin fc-other-month)
            "numeros_fila_mes_actual": "//div[contains(@class, 'fc-row')][{fila}]//td[contains(@class, 'fc-day-number') and not(contains(@class, 'fc-other-month'))]",
            
            # Turnos (verde #c1e6c5 o gris #d0d0d0) - plantilla con {fila} dinámico
            "turnos_fila": "//div[contains(@class, 'fc-row')][{fila}]//a[contains(@class, 'fc-day-grid-event')][contains(@style, '#c1e6c5') or contains(@style, '#d0d0d0') or contains(@style, '#528457')]",
            
            # Loader de carga del calendario
            "loader": "//div[@class='em-textLoader' and contains(@style, 'display: none')]",

            # Nombre de usuario logeado
            "nombre_usuario": "//span[@class='lblUsuarioLogeado']",
            
            # Break (morado #bcb9d8) - plantilla con {fila} dinámico
            "break_fila": "//div[contains(@class, 'fc-row')][{fila}]//a[contains(@class, 'fc-day-grid-event')][contains(@style, '#bcb9d8')]"
        }
    
    def _get_selector(self, tipo: str, fila: int = None) -> str:
        """
        Obtiene un selector formateado con el número de fila.
        
        Args:
            tipo: 'numeros_fila', 'turnos_fila', 'break_fila', o 'dias_semana'
            fila: Número de fila (1-5) para selectores que lo requieren
        
        Returns:
            Selector XPath formateado
        """
        if tipo not in self.selectores_base:
            raise ValueError(f"Tipo de selector desconocido: {tipo}")
        
        selector = self.selectores_base[tipo]
        
        if fila is not None:
            if "{fila}" not in selector:
                raise ValueError(f"Selector '{tipo}' no espera parámetro de fila")
            return selector.format(fila=fila)
        
        return selector
    
    def extraer_dias_semana(self):
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page

            selector = self._get_selector("dias_semana")
            page.wait_for_selector(f"xpath={selector}", timeout=10000)
            dias_elements = page.query_selector_all(f"xpath={selector}")
            
            dias_semana = []
            for element in dias_elements:
                texto = element.text_content().strip()
                if texto:
                    dias_semana.append(texto)
            
            if len(dias_semana) == 7:
                return dias_semana
            else:
                # Si no son 7, es un error grave: no adivinar
                raise ValueError(f"Se esperaban 7 días de la semana, se obtuvieron {len(dias_semana)}: {dias_semana}")
                
        except Exception as e:
            print(f"⚠️ Error extrayendo días de la semana: {e}")
            # No usar fallback peligroso
            # En su lugar, intentar estrategia alternativa o fallar
            # Para debugging, podrías devolver None y manejarlo arriba
            raise
    
    def extraer_numeros_matriz(self):
        """Extrae los números de día y evita duplicados (p. ej., día 1 repetido)."""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            matriz_numeros = zeros((5, 7), dtype=int32)
            dias_vistos = set()  # ← Para evitar duplicados
            
            # Extraer cada fila (1-5)
            for fila_idx in range(5):
                selector = self._get_selector("numeros_fila", fila_idx + 1)
                elements = page.query_selector_all(f"xpath={selector}")
                
                # Procesar hasta 7 columnas
                for col_idx, element in enumerate(elements[:7]):
                    try:
                        texto = element.text_content().strip()
                        if texto:
                            numero = ''.join(filter(str.isdigit, texto))
                            if numero:
                                dia_num = int(numero)
                                # Solo asignar si aún no se ha visto este día
                                if dia_num not in dias_vistos:
                                    matriz_numeros[fila_idx, col_idx] = dia_num
                                    dias_vistos.add(dia_num)
                                # Si ya existe, dejar la celda en 0 (o ignorar)
                    except Exception:
                        continue
            
            return matriz_numeros
            
        except Exception as e:
            print(f"⚠️ Error extrayendo números matriz: {e}")
            return zeros((5, 7), dtype=int32)
    
    def extraer_turnos_matriz(self):
        """Extrae los turnos principales (eventos principales)"""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            eventos_principales = ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            # Extraer cada fila (1-5)
            for fila_idx in range(5):
                selector = self._get_selector("turnos_fila", fila_idx + 1)
                elements = page.query_selector_all(f"xpath={selector}")
                
                # Procesar hasta 7 columnas
                for col_idx, element in enumerate(elements[:7]):
                    try:
                        texto = element.text_content().strip()
                        if texto:
                            eventos_principales[fila_idx, col_idx] = texto
                    except:
                        continue
            
            return eventos_principales
            
        except Exception as e:
            print(f"⚠️ Error extrayendo turnos: {e}")
            return ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
    
    def extraer_breaks_matriz(self):
        """Extrae los breaks (eventos secundarios)"""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            eventos_secundarios = ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            # Extraer cada fila (1-5)
            for fila_idx in range(5):
                selector = self._get_selector("break_fila", fila_idx + 1)
                elements = page.query_selector_all(f"xpath={selector}")
                
                # Procesar hasta 7 columnas
                for col_idx, element in enumerate(elements[:7]):
                    try:
                        texto = element.text_content().strip()
                        if texto:
                            eventos_secundarios[fila_idx, col_idx] = texto
                    except:
                        continue
            
            return eventos_secundarios
            
        except Exception as e:
            print(f"⚠️ Error extrayendo breaks: {e}")
            return ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
    
    def extraer_turnos_y_breaks_juntos(self):
        """
        Extrae turnos y breaks usando posiciones X (bounding box) para mapear correctamente ambos.
        """
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            eventos_principales = ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            eventos_secundarios = ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            
            for fila_idx in range(5):
                fila_num = fila_idx + 1
                
                # 1. Identificar columnas del mes actual y sus posiciones X
                selector_todos = self._get_selector("numeros_fila", fila_num)
                todas_celdas = page.query_selector_all(f"xpath={selector_todos}")
                
                columnas_info = []  # [(col_idx, x_center), ...]
                for col_idx, celda in enumerate(todas_celdas[:7]):
                    if 'fc-other-month' not in (celda.get_attribute('class') or ''):
                        bbox = celda.bounding_box()
                        if bbox:
                            x_center = bbox['x'] + bbox['width'] / 2
                            columnas_info.append((col_idx, x_center))
                
                # 2. EXTRAER TURNOS usando posición X
                selector_turnos = self._get_selector("turnos_fila", fila_num)
                elements_turnos = page.query_selector_all(f"xpath={selector_turnos}")
                
                for element in elements_turnos:
                    try:
                        bbox = element.bounding_box()
                        if not bbox:
                            continue
                        
                        turno_x_center = bbox['x'] + bbox['width'] / 2
                        
                        # Encontrar la columna más cercana
                        mejor_col = None
                        menor_distancia = float('inf')
                        
                        for col_idx, x_center in columnas_info:
                            distancia = abs(turno_x_center - x_center)
                            if distancia < menor_distancia:
                                menor_distancia = distancia
                                mejor_col = col_idx
                        
                        if mejor_col is not None:
                            texto = element.text_content().strip()
                            if texto:
                                eventos_principales[fila_idx, mejor_col] = texto
                    except Exception as e:
                        continue
                
                # 3. EXTRAER BREAKS usando posición X
                selector_breaks = self._get_selector("break_fila", fila_num)
                elements_breaks = page.query_selector_all(f"xpath={selector_breaks}")
                
                for element in elements_breaks:
                    try:
                        bbox = element.bounding_box()
                        if not bbox:
                            continue
                        
                        break_x_center = bbox['x'] + bbox['width'] / 2
                        
                        # Encontrar la columna más cercana
                        mejor_col = None
                        menor_distancia = float('inf')
                        
                        for col_idx, x_center in columnas_info:
                            distancia = abs(break_x_center - x_center)
                            if distancia < menor_distancia:
                                menor_distancia = distancia
                                mejor_col = col_idx
                        
                        if mejor_col is not None:
                            texto = element.text_content().strip()
                            if texto:
                                eventos_secundarios[fila_idx, mejor_col] = texto
                    except Exception as e:
                        continue
            
            return eventos_principales, eventos_secundarios
            
        except Exception as e:
            print(f"⚠️ Error extrayendo turnos y breaks juntos: {e}")
            import traceback
            traceback.print_exc()
            empty_matrix = ar([
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ], dtype=object)
            return empty_matrix, empty_matrix
    
    def extraer_matriz_festivos(self):
        """Extrae días festivos (si se pueden identificar)"""
        try:
            return zeros((5, 7), dtype=bool)
        except:
            return zeros((5, 7), dtype=bool)
    
    def extraer_todo(self):
        """Extrae todos los datos del calendario de forma eficiente"""

        # Extraer nombre del usuario
        nombre_usuario = self.extraer_nombre_usuario()
        
        # Extraer días de la semana
        dias_semana = self.extraer_dias_semana()
        
        # Extraer números de los días
        numeros_matriz = self.extraer_numeros_matriz()
        
        # Extraer turnos y breaks juntos (más eficiente)
        eventos_principales, eventos_secundarios = self.extraer_turnos_y_breaks_juntos()
        
        # Festivos (por ahora vacío)
        es_festivo = self.extraer_matriz_festivos()
        
        # Fecha actual
        hoy_numero = datetime.now().day
        hoy_fecha = datetime.now().strftime("%Y-%m-%d")
        
        return {
            'nombre_usuario': nombre_usuario,
            'dias_semana': dias_semana,
            'numeros_matriz': numeros_matriz,
            'eventos_principales': eventos_principales,
            'eventos_secundarios': eventos_secundarios,
            'es_festivo': es_festivo,
            'hoy_numero': hoy_numero,
            'hoy_fecha': hoy_fecha
        }
    
    def extraer_nombre_usuario(self):
        """Extrae el nombre del usuario logeado"""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            selector = self._get_selector("nombre_usuario")
            
            # Esperar un momento para que cargue
            page.wait_for_timeout(2000)
            
            # Buscar elemento del nombre de usuario
            elemento_usuario = page.query_selector(f"xpath={selector}")
            
            if elemento_usuario:
                nombre = elemento_usuario.text_content().strip()
                if nombre:
                    print(f"👤 Usuario identificado: {nombre}")
                    self.nombre_usuario=nombre
                    return nombre
            
            print("⚠️ No se pudo extraer el nombre de usuario")
            return None
            
        except Exception as e:
            print(f"⚠️ Error extrayendo nombre de usuario: {e}")
            return None
    
    def mostrar_datos_extraidos(self, datos):
        """Muestra los datos extraídos de forma organizada por partes"""
        if not datos:
            print("❌ No hay datos para mostrar")
            return
        
        numeros = datos['numeros_matriz']
        for i in range(5):
            fila_str = "  "
            for j in range(7):
                dia_num = numeros[i, j]
                if dia_num == datos['hoy_numero']:
                    fila_str += f"[{dia_num:2d}] "
                else:
                    fila_str += f" {dia_num:2d}  "
        
        turnos = datos['eventos_principales']
        for i in range(5):
            fila_str = "  "
            for j in range(7):
                turno = turnos[i, j]
                if turno:
                    # Acortar texto si es muy largo
                    if len(turno) > 12:
                        fila_str += f"{turno[:10]}... "
                    else:
                        fila_str += f"{turno:12s} "
                else:
                    fila_str += "   -        "
        
        breaks = datos['eventos_secundarios']
        for i in range(5):
            fila_str = "  "
            for j in range(7):
                break_info = breaks[i, j]
                if break_info:
                    # Acortar texto si es muy largo
                    if len(break_info) > 12:
                        fila_str += f"{break_info[:10]}... "
                    else:
                        fila_str += f"{break_info:12s} "
                else:
                    fila_str += "   -        "
        
        # 5. VISTA DETALLADA POR DÍA (solo días con datos)
        print("\n🔍 VISTA DETALLADA POR DÍA:")
        print("  " + "-" * 50)

        if datos.get('nombre_usuario'):
            print(f"👤 Usuario: {datos['nombre_usuario']}")
        
        dias_con_datos = False
        for i in range(5):  # Filas
            for j in range(7):  # Columnas
                dia_num = numeros[i, j]
                if dia_num > 0:
                    turno = turnos[i, j]
                    break_info = breaks[i, j]
                    
                    if turno or break_info:
                        dias_con_datos = True
                        # Nombre del día
                        nombre_dia = datos['dias_semana'][j] if j < len(datos['dias_semana']) else f"Día {j+1}"
                        
                        # Marcar si es hoy
                        es_hoy = " (HOY)" if dia_num == datos['hoy_numero'] else ""
                        
                        print(f"  📅 {nombre_dia} {dia_num}{es_hoy}:")
                        if turno:
                            print(f"     Turno: {turno}")
                        if break_info:
                            print(f"     Break: {break_info}")
                        print("  " + "-" * 50)
        
        if not dias_con_datos:
            print("  No hay datos en ningún día del calendario")

    def obtener_ruta_json_usuario(self):
        """
        Obtiene la ruta del archivo JSON único para el usuario.
        """
        try:
            if not self.nombre_usuario:
                return None
            
            # Limpiar nombre para usar como directorio
            nombre_limpio = "".join(c for c in self.nombre_usuario if c.isalnum() or c in (' ', '_')).rstrip()
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
        Esta es la NUEVA lógica: un solo archivo JSON por usuario.
        """
        try:
            # 1. Generar JSON con datos nuevos
            calendario_nuevo = self.generar_json_calendario(datos_extractos)
            if not calendario_nuevo:
                print("❌ No se pudo generar JSON con datos nuevos")
                return None
            
            # 2. Cargar JSON existente (si hay)
            calendario_existente = self.cargar_json_existente()
            
            # 3. Si no existe archivo previo, guardar directamente
            if not calendario_existente:
                print("📝 Primera ejecución para este usuario")
                return self._guardar_json_actualizado(calendario_nuevo)
            
            # 4. Comparar y marcar cambios
            calendario_actualizado = self._detectar_cambios(
                calendario_existente, 
                calendario_nuevo
            )
            
            # 5. Guardar versión actualizada
            return self._guardar_json_actualizado(calendario_actualizado)
            
        except Exception as e:
            print(f"❌ Error comparando y actualizando: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _detectar_cambios(self, calendario_antiguo, calendario_nuevo):
        """
        Detecta cambios entre dos versiones del calendario y los marca.
        Correcciones clave:
        1. Detección precisa de breaks usando horario (no existencia de objeto)
        2. Manejo de días eliminados
        3. Comparación de duración de breaks
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
                print("✅ Sin cambios detectados respecto a la versión anterior")
            
            return calendario_actualizado
            
        except Exception as e:
            print(f"❌ Error grave detectando cambios: {e}")
            import traceback
            traceback.print_exc()
            # En caso de error, mantener el nuevo calendario sin cambios
            return calendario_nuevo
        
    def _guardar_json_actualizado(self, calendario):
        """
        Guarda el JSON actualizado (sobrescribe el anterior).
        """
        try:
            ruta_json = self.obtener_ruta_json_usuario()
            if not ruta_json:
                print("❌ No se pudo obtener ruta para guardar JSON")
                return False
            
            # Crear backup del archivo anterior (si existe)
            if os_path.exists(ruta_json):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_backup = ruta_json.replace(".json", f"_backup_{timestamp}.json")
                import shutil
                shutil.copy2(ruta_json, ruta_backup)
                print(f"💾 Backup creado: {os_path.basename(ruta_backup)}")
            
            # Guardar nuevo JSON
            with open(ruta_json, 'w', encoding='utf-8') as f:
                dump(calendario, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Calendario actualizado guardado: {ruta_json}")
            
            # Limpiar backups antiguos (mantener solo los 2 más recientes)
            self._limpiar_backups_viejos(ruta_json)
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando JSON actualizado: {e}")
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
                    remove(backup)
                    print(f"🗑️  Eliminado backup antiguo: {os_path.basename(backup)}")
                except Exception as e:
                    print(f"⚠️  Error eliminando backup {backup}: {e}")
                    
        except Exception as e:
            print(f"⚠️  Error limpiando backups: {e}")
    
    def ejecutar_proceso_simplificado(self):
        """
        Ejecuta el proceso simplificado: extraer, comparar y actualizar un solo archivo.
        """
        try:
            print("🔄 Extrayendo datos del calendario...")
            
            # 1. Extraer datos
            datos = self.extraer_todo()
            
            # 2. Mostrar datos extraídos
            # self.mostrar_datos_extraidos(datos)
            
            # 3. Comparar y actualizar archivo único
            resultado = self.comparar_y_actualizar(datos)
            
            if resultado:                
                # Mostrar resumen de cambios si existe
                ruta_json = self.obtener_ruta_json_usuario()
                if ruta_json and os_path.exists(ruta_json):
                    with open(ruta_json, 'r', encoding='utf-8') as f:
                        json_data = load(f)
                    
                    if json_data.get("resumen_cambios", {}).get("se_detectaron_cambios", False):
                        print("🔄 Cambios detectados")
                    else:
                        print("✅ Sin cambios en esta ejecución")
                
                return resultado
            else:
                print("❌ Error en el proceso")
                return None
                
        except Exception as e:
            print(f"💥 Error en ejecución: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generar_json_calendario(self, datos_extractos):
        """
        Genera la estructura JSON básica del calendario.
        """
        try:
            # Información del usuario
            nombre_usuario = datos_extractos.get('nombre_usuario', 'Usuario Desconocido')
            
            usuario_info = {
                "id": nombre_usuario.upper().replace(" ", "_"),
                "nombre_completo": nombre_usuario
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
            print(f"❌ Error generando JSON: {e}")
            return None