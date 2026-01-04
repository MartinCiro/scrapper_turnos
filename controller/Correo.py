# ===========================================================================
# Importaciones de clases y librerias necesarias
# ===========================================================================

# Region Llamado de clases o librerias necesarias
from smtplib import SMTP_SSL
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
from ssl import create_default_context
from controller.Config import Config
# Endregion Llamado de clases o librerias necesarias


# ===========================================================================
# VARIABLES GLOBALES - LOCALES
# ===========================================================================
# Region Instancia de las clases y generación de var globales


# En los destinatarios se separa el array por comas y se deja en lista
# '<Correo1@gmail.com>','<Correo2@gmail.com>'

# Endregion Instancia de las clases y generación de var globales

class Correo(Config):
    """
        Correo
        ======
        Desde esta clase nos encargamos del envio de correos del bot
        estos correos pueden ser multiples o de reporte final, se debería
        modificar, según la necesidad del bot.
        ### `Usos`:
        - Podemos usar el servicio para reportar la finalización del bot.
    """
    def __init__(self):
        """
            Instancia de variables usadas dentro de la clase.
            - Se instancia el `remitente`, `destinatario(s)`, y `asunto del correo`.
        """
        super().__init__()
        self.__asuntoCorreo= "Alerta Bot"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

    def __login(self) -> SMTP_SSL:
        """Establece conexión SMTP segura con Google."""
        try:
            context = create_default_context()
            smtp = SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            try:
                smtp.login(self.user_email, self.user_pass)
            except Exception as e:
                print(f"Error: {e}")
            print("✅ Login exitoso con Google SMTP")
            return smtp
        except Exception as e:
            raise Exception(f"❌ Error en login: {str(e)}")
            
    def EjecutarEnvioCorreo(self, urls: list, error: bool = False):
        if not error:
            # Estructura de documentos con nombres asociados
            documentos = [
                {
                    "url": urls[0], 
                    "nombre": "Acta"
                },
                {
                    "url": urls[2], 
                    "nombre": "Notas"
                },
                {
                    "url": urls[1], 
                    "nombre": "Certificado"
                }        
            ]

            # Generar botones con estilos INLINE (requerido para clientes de email)
            botones_html = ""
            for doc in documentos:
                botones_html += f"""
                <div style="margin-bottom: 15px;">
                    <a href="{doc['url']}" download style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 12px 20px;
                        background-color: #f8f9fa;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        text-decoration: none;
                        color: #212529;
                    ">
                        <span style="flex-grow: 1;">{doc['nombre']} &nbsp;</span>
                        <span style="color: #0d6efd; font-size: 14px;">Descargar</span>
                    </a>
                </div>
                """

            # HTML completo con estilos INLINE
            mensaje_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
                    <p style="line-height: 1.6;">¡Hola! Tus documentos están disponibles para descarga:</p>
                    <div style="margin-top: 20px;">
                        {botones_html}
                    </div>
                    <p style="margin-top: 25px; font-size: 14px; color: #6c757d;">
                        Si tienes problemas con la descarga, copia y pega la URL en tu navegador.
                    </p>
                </body>
            </html>
            """
        else: 
            mensaje_html = "Aún no se ha generado certificado"
        # Configuración del mensaje
        msg = MIMEMultipart()
        msg.attach(MIMEText(mensaje_html, 'html'))
        msg['Subject'] = self.__asuntoCorreo
        msg['From'] = self.user_email
        msg['To'] = ", ".join([self.user_email])

        # Envío seguro usando context manager
        try:
            with self.__login() as smtp:
                smtp.send_message(msg)
        except Exception as e:
            print(f"Error enviando correo: {str(e)}")