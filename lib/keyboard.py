from pynput.keyboard import Controller, Key

class Keyboard:
    def __init__(self):
        self.__keyboard = Controller()
    
    def Click_tecla(self, nombre):
        nombre = nombre.lower()
        if nombre==" ":
            self.__keyboard.press(Key.space)
            self.__keyboard.release(Key.space)
        else:
            if nombre.isalpha():
                self.__keyboard.press(Key.shift)
                self.__keyboard.press(nombre)
                self.__keyboard.release(nombre)
                self.__keyboard.release(Key.shift)
            elif nombre.isdigit():
                self.__keyboard.press(nombre)
                self.__keyboard.release(nombre)

    def Escribir_frase(self, frase):
        # for char in frase:
        #     self.Click_tecla(char)
        frase = frase.lower()
        self.__keyboard.type(frase)

    def Escribir_frase_normal(self, frase):
        self.__keyboard.type(frase)

        
    def Enter(self):
        self.__keyboard.press(Key.enter)
        self.__keyboard.release(Key.enter)
    
    def Down(self):
        self.__keyboard.press(Key.down)
        self.__keyboard.release(Key.down)
    
    def Seleccionar_linea(self):
        self.__keyboard.press(Key.shift)
        self.__keyboard.press(Key.ctrl)
        self.__keyboard.press(Key.right)
        self.__keyboard.release(Key.right)
        self.__keyboard.release(Key.ctrl)
        self.__keyboard.release(Key.shift)
    
    def Borrar(self):
        self.__keyboard.press(Key.delete)
        self.__keyboard.release(Key.delete)
    
    def Guardar(self):
        self.__keyboard.press(Key.ctrl)
        self.__keyboard.press("g")
        self.__keyboard.release("g")
        self.__keyboard.release(Key.ctrl)

    def Seleccionar_todo(self):
        self.__keyboard.press(Key.ctrl)
        self.__keyboard.press("a")
        self.__keyboard.release("a")
        self.__keyboard.release(Key.ctrl)
        self.__keyboard.press(Key.esc)
        self.__keyboard.release(Key.esc)
        self.__keyboard.press(Key.ctrl)
        self.__keyboard.press("e")
        self.__keyboard.release("e")
        self.__keyboard.release(Key.ctrl)
        self.__keyboard.press(Key.esc)
        self.__keyboard.release(Key.esc)
        
    def Captura_pantalla(self):
        # Simula Ctrl + F5 (atajo de DOSBox para capturar pantalla)
        self.__keyboard.press(Key.ctrl)
        self.__keyboard.press(Key.f5)
        self.__keyboard.release(Key.f5)
        self.__keyboard.release(Key.ctrl)
