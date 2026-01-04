from datetime import datetime

class Impresor:
    """
    Clase para manejar la impresión de mensajes formateados en consola.
    
    Ejemplos de uso:
    ----------------
    >>> imp = Impresor()
    >>> imp.inicio("Mi Aplicación")
    >>> imp.proceso("Cálculo de datos")
    >>> imp.comentario("Validación", "Se verificaron los inputs")
    >>> imp.error("División por cero")
    >>> imp.final()
    """
    
    __ANCHO = 120  # Ancho constante para todos los mensajes
    
    def __formatear_linea(self, texto: str, caracter: str = "=") -> str:
        """Formatea una línea con el ancho constante"""
        return f"{caracter * self.__ANCHO}\n"
    
    def __formatear_contenido(self, *lineas: str) -> str:
        """Formatea el contenido central del mensaje"""
        contenido = ""
        for linea in lineas:
            contenido += f"| {linea.ljust(self.__ANCHO - 4)} |\n"
        return contenido
    
    def __imprimir_bloque(self, *contenido: str):
        """Método base para imprimir cualquier tipo de bloque"""
        mensaje = self.__formatear_linea()
        mensaje += self.__formatear_contenido(*contenido)
        mensaje += self.__formatear_linea()
        print(mensaje)
    
    def __obtener_tiempo(self) -> str:
        """Obtiene el tiempo actual formateado"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def inicio(self, nombre_app: str):
        """Imprime el inicio de la aplicación"""
        self.__imprimir_bloque(
            f"INICIO DE APLICACIÓN: {nombre_app}",
            f"Hora de ejecución: {self.__obtener_tiempo()}"
        )
    
    def proceso(self, nombre_proceso: str):
        """Imprime el inicio de un proceso"""
        self.__imprimir_bloque(
            f"Ejecutando tarea: {nombre_proceso}",
            f"Hora de ejecución: {self.__obtener_tiempo()}"
        )
    
    def comentario(self, contexto: str, mensaje: str):
        """Imprime un comentario contextual"""
        self.__imprimir_bloque(
            f"{contexto}: {mensaje}",
            f"Hora de ejecución: {self.__obtener_tiempo()}"
        )
    
    def error(self, descripcion_error: str):
        """Imprime un mensaje de error"""
        self.__imprimir_bloque(
            "ERROR EN EJECUCIÓN",
            descripcion_error,
            f"Hora del error: {self.__obtener_tiempo()}"
        )
    
    def final(self):
        """Imprime el cierre de la aplicación"""
        self.__imprimir_bloque(
            "FINALIZACIÓN DE APLICACIÓN",
            f"Hora de ejecución: {self.__obtener_tiempo()}"
        )