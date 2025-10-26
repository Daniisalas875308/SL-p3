import pygetwindow as gw
from PIL import Image, ImageGrab
import pytesseract as pt
import pyautogui
import os, time
from pywinauto import Application, findwindows
from pynput.mouse import Controller, Button

class Window:

    def __init__(self,nombre):
        self._nombre = nombre
        self.__window = gw.getWindowsWithTitle(self._nombre)[0]
        self.__coor = [self.__window.left, self.__window.top, self.__window.width, self.__window.height]

    def __reubicar_ventana_tamaño(self):
        self.__window.moveTo(100, 100)

        self.__coor[0], self.__coor[1] = 100, 100

        w = 100+self.__window.width
        h = 100+self.__window.height

        self.__coor[2], self.__coor[3] = w, h

        return [100,100,w,h]

    def __capturar_ventana(self,fullscreen=False):
        # Define las coordenadas de la zona que deseas capturar
        if (fullscreen):
            x1, y1, x2, y2 = 0,0,self.__window.width, self.__window.height
        else:
            x1, y1, x2, y2 = self.__coor[0]+3, self.__coor[1]+25, self.__coor[2]-2, self.__coor[3]  # Define las coordenadas izquierda arriba y derecha abajo

        # Captura la zona de la pantalla
        # captura = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        captura = pyautogui.screenshot(region=(x1,y1,x2,y2))

        # Guarda la captura en un archivo de imagen
        captura.save("captura.png")

        # Cierra la captura
        captura.close()

    def __read_imagen(self):
        imagen = Image.open('captura.png')
        string = pt.image_to_string(imagen, lang="spa", config='--psm 6')
        # string = pt.image_to_string(imagen, lang="spa")
        return string

    def __delete_imagen(self):
        archivo_a_eliminar = "captura.png"
        if os.path.exists(archivo_a_eliminar):
            os.remove(archivo_a_eliminar)

    def Eliminar_lineas_vacias(self,string):
        # Divide el texto en líneas y filtra las líneas no vacías
        lines = [line for line in string.splitlines() if line.strip()]

        # Une las líneas en un solo string nuevamente
        cleaned_string = '\n'.join(lines)

        return cleaned_string

    def Info_ventana(self):
        self.__reubicar_ventana_tamaño()
        self.__capturar_ventana()
        time.sleep(4)
        imagen = self.__read_imagen()
        # self.__delete_imagen()
        return imagen
    
    def Info_ventana_completa(self):
        self.__capturar_ventana(fullscreen=True)
        time.sleep(4)
        imagen = self.__read_imagen()
        # self.__delete_imagen()
        return imagen
    
    def Print(self):
        print(self.__window)
        print(self._nombre)
        print(self.__coor)

    def Cerrar_ventana(self):
        self.__window.close()
