from controller.BasePlaywright import BasePlaywright
from controller.utils.Helpers import Helpers
from numpy import array as ar, zeros, int32
from time import sleep
from datetime import datetime

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
            
            # Turnos (verde #c1e6c5 o gris #d0d0d0) - plantilla con {fila} dinámico
            "turnos_fila": "//div[contains(@class, 'fc-row')][{fila}]//a[contains(@class, 'fc-day-grid-event')][contains(@style, '#c1e6c5') or contains(@style, '#d0d0d0')]",
            
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
        """Extrae los días de la semana del calendario"""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            selector = self._get_selector("dias_semana")
            dias_elements = page.query_selector_all(f"xpath={selector}")
            
            dias_semana = []
            for element in dias_elements:
                texto = element.text_content().strip()
                if texto:
                    dias_semana.append(texto)
            
            return dias_semana[:7]  # Solo los primeros 7 días
        except Exception as e:
            print(f"⚠️ Error extrayendo días semana: {e}")
            return []
    
    def extraer_numeros_matriz(self):
        """Extrae los números de día para formar la matriz 5x7"""
        try:
            if self.login_instance:
                page = self.login_instance.page
            else:
                page = self.page
            
            matriz_numeros = zeros((5, 7), dtype=int32)
            
            # Extraer cada fila (1-5)
            for fila_idx in range(5):
                selector = self._get_selector("numeros_fila", fila_idx + 1)
                elements = page.query_selector_all(f"xpath={selector}")
                
                # Procesar hasta 7 columnas
                for col_idx, element in enumerate(elements[:7]):
                    try:
                        texto = element.text_content().strip()
                        if texto:
                            # Extraer solo números
                            numero = ''.join(filter(str.isdigit, texto))
                            if numero:
                                matriz_numeros[fila_idx, col_idx] = int(numero)
                    except:
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
        Extrae turnos y breaks por filas manejando correctamente los rowspan.
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
            
            # Extraer por cada fila (semana)
            for fila_idx in range(5):
                fila_num = fila_idx + 1
                
                # Selector para el tbody de esta semana
                tbody_xpath = f"//div[contains(@class, 'fc-row')][{fila_num}]//div[@class='fc-content-skeleton']//tbody"
                tbody = page.query_selector(f"xpath={tbody_xpath}")
                
                if not tbody:
                    continue
                
                # Obtener las filas <tr> dentro del tbody
                trs = tbody.query_selector_all("xpath=./tr")
                
                if len(trs) == 0:
                    continue
                
                # Primera <tr>: turnos principales
                # Rastrear columnas con rowspan
                columnas_con_rowspan = {}  # {col_idx: rowspan_restante}
                
                if len(trs) > 0:
                    celdas_turnos = trs[0].query_selector_all("xpath=./td")
                    col_idx = 0
                    
                    for celda in celdas_turnos:
                        if col_idx >= 7:
                            break
                        
                        # Verificar si es fc-event-container
                        if 'fc-event-container' in (celda.get_attribute('class') or ''):
                            # Buscar evento verde o gris (turno)
                            evento = celda.query_selector("xpath=.//a[contains(@style, '#c1e6c5') or contains(@style, '#d0d0d0')]")
                            if evento:
                                texto = evento.text_content().strip()
                                if texto:
                                    eventos_principales[fila_idx, col_idx] = texto
                            
                            # Verificar rowspan
                            rowspan_attr = celda.get_attribute('rowspan')
                            if rowspan_attr:
                                rowspan = int(rowspan_attr)
                                if rowspan > 1:
                                    columnas_con_rowspan[col_idx] = rowspan - 1
                            
                            col_idx += 1
                        else:
                            # Celda sin clase específica, avanzar
                            col_idx += 1
                
                # Segunda <tr> y siguientes: breaks
                if len(trs) > 1:
                    for tr_idx, tr in enumerate(trs[1:], start=1):
                        celdas_breaks = tr.query_selector_all("xpath=./td")
                        
                        # Ajustar columnas considerando rowspan de la fila anterior
                        col_real = 0  # Columna real en la matriz
                        td_idx = 0    # Índice del td actual
                        
                        while col_real < 7 and td_idx < len(celdas_breaks):
                            # Saltar columnas ocupadas por rowspan
                            while col_real in columnas_con_rowspan and columnas_con_rowspan[col_real] > 0:
                                col_real += 1
                                if col_real >= 7:
                                    break
                            
                            if col_real >= 7:
                                break
                            
                            celda = celdas_breaks[td_idx]
                            
                            # Verificar si es fc-event-container
                            if 'fc-event-container' in (celda.get_attribute('class') or ''):
                                # Buscar evento morado (break)
                                evento = celda.query_selector("xpath=.//a[contains(@style, '#bcb9d8')]")
                                if evento:
                                    texto = evento.text_content().strip()
                                    if texto:
                                        eventos_secundarios[fila_idx, col_real] = texto
                                
                                # Actualizar rowspan para filas futuras (si aplica)
                                rowspan_attr = celda.get_attribute('rowspan')
                                if rowspan_attr:
                                    rowspan = int(rowspan_attr)
                                    if rowspan > 1 and tr_idx == 1:  # Solo en la segunda fila
                                        if col_real in columnas_con_rowspan:
                                            columnas_con_rowspan[col_real] += rowspan - 1
                                        else:
                                            columnas_con_rowspan[col_real] = rowspan - 1
                            
                            col_real += 1
                            td_idx += 1
                        
                        # Decrementar rowspan para la siguiente iteración
                        for col in list(columnas_con_rowspan.keys()):
                            columnas_con_rowspan[col] -= 1
                            if columnas_con_rowspan[col] <= 0:
                                del columnas_con_rowspan[col]
            
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
        
        sleep(2)  # Esperar a que cargue
        
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
            'dias_semana': dias_semana,
            'numeros_matriz': numeros_matriz,
            'eventos_principales': eventos_principales,
            'eventos_secundarios': eventos_secundarios,
            'es_festivo': es_festivo,
            'hoy_numero': hoy_numero,
            'hoy_fecha': hoy_fecha
        }
    
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
    
