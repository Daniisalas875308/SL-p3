import pygetwindow as gw

class Window:

    def __init__(self,nombre):
        self._nombre = nombre
        ventanas = gw.getWindowsWithTitle(self._nombre)
        if not ventanas:
            ventanas = gw.getWindowsWithTitle("DOSBox")  # fallback
        if not ventanas:
            raise Exception(f"No se encontró ninguna ventana con el título '{self._nombre}' ni con 'DOSBox'.")
        self.__window = ventanas[0]


    def Cerrar_ventana(self):
        self.__window.close()