import multiprocessing, subprocess, signal, time, os, sys
import pygetwindow as gw
import pytesseract
import re
from flask import Flask, render_template, request, redirect, session
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from itertools import zip_longest  # Necesitamos esto para combinar las columnas


from lib.window import Window
from lib.keyboard import Keyboard

app = Flask(__name__)
delayScreen = 0.8
archivo = "./salida_ocr.txt"
nombre = "DOSBox 0.74, Cpu speed: 3000 cycles, Frameskip 0, Program:..."
leido = False
database = {
    "numReg": 0,
    "datos": []
}

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SEPARADOR = " | "


# Directorio base donde están tus ficheros
base_dir = ".\\Database-MSDOS" 

# Ruta al ejecutable de DOSBox
dosbox_exe = os.path.join(base_dir, "DOSBox-0.74", "DOSBox.exe")

# Directorio que DOSBox montará como C: (la carpeta "Database")
# Es crucial usar una ruta absoluta para el montaje en DOSBox
mount_dir_abs = os.path.abspath(os.path.join(base_dir, "Database"))
# --- Fin de Configuración ---


# 1. Comando para montar el directorio 'Database' como C:
mount_cmd = f"MOUNT C \"{mount_dir_abs}\""

# 2. Comando para cambiar a la unidad C:
drive_cmd = "C:"

# 3. Comando para ejecutar el .bat Y REDIRIGIR su salida
#    (Esto se ejecuta DENTRO de DOS)
run_cmd = "gwbasic.bat > SALIDA.TXT"

# 4. Comando para salir de DOSBox al terminar
exit_cmd = "EXIT"

# Construimos la lista de comandos final para Popen
command_list = [
    dosbox_exe,
    "-noconsole",    # Mantenemos tu -noconsole
    "-c", mount_cmd,   # Monta C:
    "-c", drive_cmd,   # Cambia a C:
    "-c", run_cmd,     # ¡Aquí está la magia! Ejecuta y redirige
    "-c", exit_cmd     # Cierra DOSBox
]

def cambiar_ciclos():
    teclado = Keyboard()
    teclado.Seleccionar_todo()
    teclado.Borrar()
    teclado.Escribir_frase_normal("[sdl]\n\nfullscreen=false\nfulldouble=false\nfullresolution=original\nwindowresolution=original\noutput=surface\nautolock=true\nsensitivity=100\nwaitonerror=true\npriority=higher,normal\nmapperfile=mapper-0.74.map\nusescancodes=true\n\n")
    teclado.Escribir_frase_normal("[dosbox]\n\nlanguage=\nmachine=svga_s3\ncaptures=capture\nmemsize=16\n\n")
    teclado.Escribir_frase_normal("[render]\n\nframeskip=0\naspect=false\nscaler=normal2x\n\n")
    teclado.Escribir_frase_normal("[cpu]\n\ncore=auto\ncputype=auto\ncycles=max\ncycleup=10\ncycledown=20\n\n")
    teclado.Escribir_frase_normal("[mixer]\n\nnosound=false\nrate=44100\nblocksize=1024\nprebuffer=20\n\n")
    teclado.Escribir_frase_normal("[midi]\n\nmpu401=intelligent\nmididevice=default\nmidiconfig=\n\n")
    teclado.Escribir_frase_normal("[sblaster]\n\nsbtype=sb16\nsbbase=220\nirq=7\ndma=1\nhdma=5\nsbmixer=true\noplmode=auto\noplemu=default\noplrate=44100\n\n")
    teclado.Escribir_frase_normal("[gus]\n\ngus=false\ngusrate=44100\ngusbase=240\ngusirq=5\ngusdma=3\nultradir=C:\\ULTRASND\n\n")
    teclado.Escribir_frase_normal("[speaker]\n\npcspeaker=true\npcrate=44100\ntandy=auto\ntandyrate=44100\ndisney=true\n\n")
    teclado.Escribir_frase_normal("[joystick]\n\njoysticktype=auto\ntimed=true\nautofire=false\nswap34=false\nbuttonwrap=false\n\n")
    teclado.Escribir_frase_normal("[serial]\n\nserial1=dummy\nserial2=dummy\nserial3=disabled\nserial4=disabled\n\n")
    teclado.Escribir_frase_normal("[dos]\n\nxms=true\nems=true\numb=true\nkeyboardlayout=auto\n\n")
    teclado.Escribir_frase_normal("[ipx]\n\nipx=false\n\n")
    teclado.Escribir_frase_normal("[autoexec]\n\n")
    teclado.Guardar() 
    time.sleep(1)
    del teclado

def modificarCiclosYRedireccion():
    configuracion=subprocess.Popen("cd .\\Database-MSDOS\\DOSBox-0.74 && .\\\"DOSBox 0.74 Options.bat\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while chequearVentana("dosbox-0.74.conf: Bloc de notas")==False: 0
    config = Window("dosbox-0.74.conf: Bloc de notas")
    num_linea = cambiar_ciclos()
    configuracion.wait()
    config.Cerrar_ventana()
    del config

def read_line(line, file="ventana.txt"):
    line = line - 1
    # Abre el archivo en modo lectura
    with open(file, "r") as archivo:
        lineas = archivo.readlines()  # Lee todas las líneas del archivo

        if 0 <= line < len(lineas):
            linea_deseada = lineas[line]
            return linea_deseada.strip()  # strip() elimina los caracteres de nueva línea
        else:
            return 0

def esperar_salida(file=archivo, timeout=60):
    print(f"[LOG] Esperando a que {file} se genere...")
    t_inicio = time.time()
    while True:
        if os.path.exists(file):
            size = os.path.getsize(file)
            if size > 0:
                print(f"[LOG] Archivo {file} generado correctamente, tamaño: {size} bytes")
                return True
        if time.time() - t_inicio > timeout:
            print(f"[ERROR] Timeout: {file} no se generó en {timeout} segundos")
            return False
        time.sleep(2)


def chequearVentana():
    ventanas_abiertas = gw.getWindowsWithTitle("DOSBox")
    return len(ventanas_abiertas) > 0


def iniciar():
    global ventana, teclado, basededatos, db

    basededatos = subprocess.Popen(command_list, 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
    intentos=0
    while chequearVentana()==False:
        if intentos>5:
            print("Aqui")
            terminar_aplicacion()
            sys.exit(0)
        time.sleep(5)
        intentos = intentos + 1
    print("Aqui 1")
    time.sleep(5)
    ventana = Window(nombre)
    time.sleep(5)
    teclado = Keyboard()
    db = True

def terminar():
    global ventana, teclado, basededatos, db
    ventana.Cerrar_ventana()
    del ventana
    del teclado
    basededatos.terminate()
    db = False

def lectura():
    teclado.Click_tecla('6')
    time.sleep(delayScreen)
    teclado.Enter()
    time.sleep(delayScreen)
    time.sleep(0.3)
    teclado.Captura_pantalla()
    i = 1
    time.sleep(0.8)
    time.sleep(delayScreen)
    while i<=42:
        teclado.Click_tecla(' ')
        time.sleep(delayScreen)
        time.sleep(0.3)
        teclado.Captura_pantalla()
        time.sleep(0.5)
        i = i+1
    teclado.Click_tecla(' ')
    time.sleep(delayScreen)
    teclado.Click_tecla('8')
    time.sleep(delayScreen)
    teclado.Click_tecla('S')
    time.sleep(delayScreen)
    teclado.Enter()
    time.sleep(delayScreen)
    teclado.Escribir_frase('LIST')
    time.sleep(delayScreen)
    teclado.Enter()
    time.sleep(delayScreen)
    teclado.Escribir_frase('RUN')
    time.sleep(delayScreen)
    teclado.Enter()
    time.sleep(delayScreen)

    global leido
    leido = True

def leer_capturas():
    capture_dir = r"C:\Users\danii\AppData\Local\DOSBox\capture"
    imagenes = sorted([
        os.path.join(capture_dir, f)
        for f in os.listdir(capture_dir)
        if f.lower().endswith(".png")
    ])

    # ⚙️ Configuración OCR (Cambiamos a --psm 6)
    # psm 6 asume un bloque de texto uniforme, lo cual es perfecto para una columna
    custom_config = r'--oem 3 --psm 6'

    # 📄 Fichero de salida
    output_file = "salida_ocr.txt"
    COLUMNAS = [
        ("N", (0, 60)),
        ("NOMBRE", (60, 350)),
        ("TIPO", (350, 505)),
        ("CINTA", (505, 570)),
        ("REGISTRO", (570, 630)), # Ajustado al ancho de 630px (640 - 5 - 5)
    ]

    # Separador que usaremos en el archivo de texto
    SEPARATOR = " | "


    if not imagenes:
        print("⚠️ No se encontró ninguna captura en la carpeta capture.")
    else:
        print(f"📷 {len(imagenes)} capturas encontradas.")
        texto_total = ""

        for idx, ruta in enumerate(imagenes, 1):
            print(f"\n🔹 Procesando {os.path.basename(ruta)} ({idx}/{len(imagenes)})")

            # --- Preprocesado (el mismo que tenías) ---
            img_orig = Image.open(ruta).convert("L")
            img_orig = ImageOps.invert(img_orig)
            img_orig = img_orig.filter(ImageFilter.MedianFilter(size=1))
            img_orig = ImageEnhance.Contrast(img_orig).enhance(4.0)
            img_orig = ImageEnhance.Sharpness(img_orig).enhance(2.0)
            img_orig = img_orig.point(lambda x: 0 if x < 150 else 255, "1")

            w, h = img_orig.size
            # Este es tu recorte principal
            img = img_orig.crop((5, int(h * 0.08), w - 5, int(h * 0.95)))
            
            w_new, h_new = img.size
            
            columnas_datos = [] # Aquí guardaremos los datos de cada columna

            # --- Procesar cada columna por separado ---
            for col_nombre, (left, right) in COLUMNAS:
                # 1. Cortar la imagen principal para obtener solo esta columna
                col_img = img.crop((left, 0, right, h_new))
                
                # 2. Ejecutar OCR solo en esa columna
                texto = pytesseract.image_to_string(col_img, lang="eng", config=custom_config)
                
                # 3. Limpiar el texto de la columna
                texto_limpio = re.sub(r'[^A-Z0-9\s,\'".:-]', '', texto.upper())
                
                # 4. Dividir en líneas y limpiar espacios
                lineas = [re.sub(r'\s+', ' ', linea.strip()) for linea in texto_limpio.split('\n') if linea.strip()]
                
                # 5. Asumimos que la primera línea es la cabecera (ej. "NOMBRE") y la saltamos
                datos_columna = lineas[1:] if lineas else []
                
                columnas_datos.append(datos_columna)

            # --- Recomponer el texto por filas ---
            texto_formateado = f"\n### {os.path.basename(ruta)} ###\n"
            
            # Añadir la cabecera al fichero
            cabeceras = [nombre for nombre, _ in COLUMNAS]
            texto_formateado += SEPARATOR.join(cabeceras) + "\n"
            texto_formateado += ("-" * (len(SEPARATOR) * (len(cabeceras) - 1) + sum(len(n) for n in cabeceras))) + "\n"

            # 6. Combinar las líneas de cada columna usando zip_longest
            #    Rellena con "" si una columna tiene menos líneas que otra (ej. un campo vacío)
            filas_combinadas = zip_longest(*columnas_datos, fillvalue="")
            
            for fila in filas_combinadas:
                if any(fila): # Solo añadir la fila si no está completamente vacía
                    texto_formateado += SEPARATOR.join(fila) + "\n"
            
            texto_total += texto_formateado

        # --- Guardar todo el texto en un solo archivo ---
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(texto_total.strip())

        print(f"\n✅ OCR completado. Resultado guardado en: {output_file}")

def eliminar_capturas():
    capture_dir = r"C:\Users\danii\AppData\Local\DOSBox\capture"
    imagenes = [
        os.path.join(capture_dir, f)
        for f in os.listdir(capture_dir)
        if f.lower().endswith(".png")
    ]
    for ruta in imagenes:
        os.remove(ruta)


def procesar(file=archivo):
    
    if not os.path.exists(file):
        print(f"❌ Error: El fichero '{file}' no existe.")
        return None # Devolvemos None si no se encuentra

    print(f"🔎 Abriendo fichero '{file}' para cargar en la BD...")

    # --- Abrimos y leemos el fichero ---
    with open(file, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    contador_registros = 1

    # --- Procesamos cada línea del fichero ---
    for linea in lineas:
        
        linea_limpia = linea.rstrip()

        # --- Filtramos las líneas que NO son datos ---
        if not linea_limpia or \
           linea_limpia.startswith("###") or \
           linea_limpia.startswith("N | NOMBRE") or \
           linea_limpia.startswith("-"):
            continue # Pasamos a la siguiente línea

        
        # Partimos la línea por el separador
        campos = linea_limpia.split(SEPARADOR)
        
        nombre = ""
        tipo = ""
        cinta_str = ""
        
        es_campo_numero_vacio = False
        if len(campos) > 0:
            primer_campo = campos[0].strip()
            # Si está vacío O es un número
            if primer_campo == "" or primer_campo.isdigit() or len(primer_campo) <= 3:
                es_campo_numero_vacio = True

        # los datos están en [1], [2], [3]
        if es_campo_numero_vacio:
            nombre = campos[1].strip() if len(campos) > 1 else ""
            tipo = campos[2].strip() if len(campos) > 2 else ""
            cinta_str = campos[3].strip().strip('|').strip() if len(campos) > 3 else ""
        else:
            nombre = campos[0].strip() if len(campos) > 0 else ""
            tipo = campos[1].strip() if len(campos) > 1 else ""
            cinta_str = campos[2].strip().strip('|').strip() if len(campos) > 2 else ""


        if not nombre:
            print(f"⚠️ Advertencia: Se ignoró la línea con 'Nombre' vacío: '{linea_limpia}'")
            continue # Saltar a la siguiente línea
        
        # Creamos el diccionario para este registro
        # Usamos nuestro 'contador_registros' para el campo "Numero"
        registro_dato = {
            "Numero": str(contador_registros), # <-- Usamos el contador
            "Nombre": nombre,
            "Tipo": tipo,
            "Cinta": cinta_str
        }
        print(f"➕ Añadiendo registro: {registro_dato}")
        database["datos"].append(registro_dato)

        database["numReg"] = str(contador_registros)

        contador_registros += 1


    print(f"✅ Carga completada. Se procesaron {len(database['datos'])} registros.")
    

def inicio():
    iniciar()
    lectura()
    terminar()
    leer_capturas()
    eliminar_capturas()
    procesar()
    

@app.route('/', methods=['GET'])
def index():
    data = {
        "numReg": database["numReg"],
        "encontrado": "SI",
        "datos": []
    }
    return render_template("app.html", data=data)

@app.route('/nombre', methods=['GET'])
def nombre_get():
    return redirect('/')

@app.route('/nombre', methods=['POST'])
def nombre_post():
    data = {
        "numReg": database["numReg"],
        "encontrado": "NO",
        "datos": []
    }
    nombre = request.form['nombre'].upper()
    instancias_conversacionales = [instancia for instancia in database["datos"] if nombre in instancia["Nombre"]]
    if len(instancias_conversacionales)>0:
        data["encontrado"] = "SI"
        for instancia in instancias_conversacionales:
            data["datos"].append({"numero": instancia["Numero"], "nombre": instancia["Nombre"], "tipo": instancia["Tipo"], "cinta": instancia["Cinta"]})
    return render_template("app.html", data=data)

@app.route('/cinta', methods=['GET'])
def cinta_get():
    return redirect('/')

@app.route('/cinta', methods=['POST'])
def cinta_post():
    data = {
        "numReg": database["numReg"],
        "encontrado": "NO",
        "datos": []
    }
    cinta = request.form['cinta'].upper()
    if cinta.isdigit():
        instancias_conversacionales = [instancia for instancia in database["datos"] if cinta == instancia["Cinta"]]
    else:
        instancias_conversacionales = [instancia for instancia in database["datos"] if cinta in instancia["Cinta"]]
        
    if len(instancias_conversacionales)>0:
        data["encontrado"] = "SI"
        for instancia in instancias_conversacionales:
            data["datos"].append({"numero": instancia["Numero"], "nombre": instancia["Nombre"], "tipo": instancia["Tipo"], "cinta": instancia["Cinta"]})
    return render_template("app.html", data=data)

def terminar_aplicacion():
    if leido==True:
        archivo_a_eliminar = archivo
        #if os.path.exists(archivo_a_eliminar):
        #    os.remove(archivo_a_eliminar)
        archivo_a_eliminar = "./Database-MSDOS/salida.txt"
        if os.path.exists(archivo_a_eliminar):
            os.remove(archivo_a_eliminar)

def terminar_app(signum, frame):
    terminar_aplicacion()
    sys.exit(0)

if __name__ == '__main__':
    inicio()
    signal.signal(signal.SIGINT, terminar_app)
    app.run(host='0.0.0.0', port=8080)