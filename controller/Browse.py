from controller.Config import Config
from controller.Correo import Correo
from selenium.webdriver.common.by import By
from time import sleep

class Browse_web(Config):
    def __init__(self) -> None:
        """Constructor optimizado que usa la instancia singleton del navegador"""
        super().__init__()
        
    def __navigate_to_aprendiz(self):
        # Navegar hasta aprendiz
        self.send_keys(
            By.XPATH, 
            "//a[@id='Salirform:cmdLogOut']", 
            None, 
            clear=False, 
            special_key=["TAB", "ENTER", "ARROWUP", "ENTER"],
            delay=0.3
        )

    def __navigate_to_certified(self):
        self.handle_link_element(
            By.XPATH, 
            "//span[contains(normalize-space(text()), 'Certificación')]/ancestor::a",
            action="click",
            special_key="ENTER"
        )

        self.handle_link_element(
            By.XPATH, 
            "//span[contains(normalize-space(text()), 'Certificación')]/ancestor::a/following-sibling::ul//a",
            action="click",
            special_key="ENTER"
        )

        self.handle_link_element(
            By.XPATH, 
            "//a[contains(text(), 'Consultar Constancias')]",
            action="click",
            special_key="ENTER"
        )
        self.handle_link_element(
            By.XPATH, 
            "//a[contains(text(), 'Consultar Constancias')]",
            action="click",
            special_key="ENTER"
        )
    
    def __select_certified(self):
        xpath_locator = "//span[contains(., 'TECNÓLOGO EN ANALISIS')]/ancestor::tr//a[contains(@id, 'clConsultaCertificadosgenerados')]"
        if self.switch_to_frame("contenido"):
            try:
                if self.wait_for_element(By.XPATH, xpath_locator, timeout=5):
                    self.click_metode(By.XPATH, xpath_locator)
                    xpath_estado_certificado = "//h2[contains(., 'Estado del Certificado')]/following-sibling::table"
                    boolean = True if self.wait_for_element(By.XPATH, f"{xpath_estado_certificado}//span[contains(text(), 'CERTIFICADO')]", timeout=5) else False
                    listado_urls = []
                    if boolean:
                        listado_info = ["A", "C", "N"]
                        codigo_array = self.get_elements_attribute(By.XPATH, f"{xpath_estado_certificado}//tr[.//span[contains(text(), 'CERTIFICADO')]]/td[1]/span", "text")
                        codigo = codigo_array[0].split(self.username)[0]
                        for listado in listado_info:
                            code = f"{codigo + self.username + listado}"
                            listado_urls.append(f"{self.url_certificado_descarga + code}")
                    else:
                        print("No encontrado")
                        return False
                    return boolean, listado_urls
            finally:
                self.__del__()
    
    def navigate_certified(self):
        self.__navigate_to_aprendiz()
        self.__navigate_to_certified()
        salida, urls = self.__select_certified()
        sender = Correo()
        return sender.EjecutarEnvioCorreo(urls) if salida else sender.EjecutarEnvioCorreo(urls, True)