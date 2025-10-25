from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import os
import re
from itertools import zip_longest  # Necesitamos esto para combinar las columnas

# 🧠 Ruta al ejecutable Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 📁 Carpeta donde DOSBox guarda las capturas
capture_dir = r"C:\Users\danii\AppData\Local\DOSBox\capture"
def procesar():
    # 📋 Buscar todas las imágenes PNG, ordenadas por nombre
    imagenes = sorted([
        os.path.join(capture_dir, f)
        for f in os.listdir(capture_dir)
        if f.lower().endswith(".png")
    ])

    # ⚙️ Configuración OCR (Cambiamos a --psm 6)
    # psm 6 asume un bloque de texto uniforme, lo cual es perfecto para una columna
    custom_config = r'--oem 3 --psm 6'

    # 📄 Fichero de salida
    output_file = "salida_ocr_columnas.txt"

    # --------------------------------------------------------------------------
    # 🎯 ¡AQUÍ ESTÁ LA CLAVE! 🎯
    # Define las coordenadas (izquierda, derecha) de CADA COLUMNA.
    # Estas coordenadas son RELATIVAS a la imagen DESPUÉS del recorte principal.
    # (Tu recorte es: (5, int(h * 0.08), w - 5, int(h * 0.95)))
    #
    # Tendrás que AJUSTAR estos números (en píxeles) para que coincidan
    # perfectamente con tus capturas.
    #
    # Formato: (Nombre_Campo, (pixel_izquierda, pixel_derecha))
    # --------------------------------------------------------------------------
    COLUMNAS = [
        ("N", (0, 60)),
        ("NOMBRE", (60, 350)),
        ("TIPO", (350, 505)),
        ("CINTA", (505, 570)),
        ("REGISTRO", (570, 630)), # Ajustado al ancho de 630px (640 - 5 - 5)
    ]

    # Separador que usaremos en el archivo de texto
    FIELD_SEPARATOR = " | "


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
            texto_formateado += FIELD_SEPARATOR.join(cabeceras) + "\n"
            texto_formateado += ("-" * (len(FIELD_SEPARATOR) * (len(cabeceras) - 1) + sum(len(n) for n in cabeceras))) + "\n"

            # 6. Combinar las líneas de cada columna usando zip_longest
            #    Rellena con "" si una columna tiene menos líneas que otra (ej. un campo vacío)
            filas_combinadas = zip_longest(*columnas_datos, fillvalue="")
            
            for fila in filas_combinadas:
                if any(fila): # Solo añadir la fila si no está completamente vacía
                    texto_formateado += FIELD_SEPARATOR.join(fila) + "\n"
            
            texto_total += texto_formateado

        # --- Guardar todo el texto en un solo archivo ---
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(texto_total.strip())

        print(f"\n✅ OCR completado. Resultado guardado en: {output_file}")


SEPARADOR = " | "

def cargar_datos_desde_fichero(nombre_fichero):
    
    # 1. Creamos la estructura de la base de datos, igual que la tenías
    database = {
        "datos": [],
        "numReg": None  # Aquí guardaremos el 'REGISTRO' del último ítem
    }
    
    # --- Comprobamos si el fichero existe ---
    if not os.path.exists(nombre_fichero):
        print(f"❌ Error: El fichero '{nombre_fichero}' no existe.")
        return None # Devolvemos None si no se encuentra

    print(f"🔎 Abriendo fichero '{nombre_fichero}' para cargar en la BD...")

    # --- Abrimos y leemos el fichero ---
    with open(nombre_fichero, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # --- ¡CAMBIO! Inicializamos nuestro propio contador ---
    contador_registros = 1

    # --- Procesamos cada línea del fichero ---
    for linea in lineas:
        # --- ¡CAMBIO CLAVE! ---
        # Usamos .rstrip() para quitar solo espacios/newlines del FINAL.
        # Esto preserva el espacio inicial si la línea empieza con " | ".
        linea_limpia = linea.rstrip()

        # --- Filtramos las líneas que NO son datos ---
        # (Esto se mantiene igual)
        if not linea_limpia or \
           linea_limpia.startswith("###") or \
           linea_limpia.startswith("N | NOMBRE") or \
           linea_limpia.startswith("-"):
            continue # Pasamos a la siguiente línea

        # --- Si estamos aquí, la línea SÍ es de datos ---
        
        # Partimos la línea por el separador
        campos = linea_limpia.split(SEPARADOR)
        
        # --- LÓGICA DE ÍNDICES REFINADA Y LIMPIA ---
        # Esta es la única lógica que necesitamos.
        
        nombre = ""
        tipo = ""
        cinta_str = ""
        
        es_campo_numero_vacio = False
        if len(campos) > 0:
            primer_campo = campos[0].strip()
            # Si está vacío O es un número
            if primer_campo == "" or primer_campo.isdigit():
                es_campo_numero_vacio = True

        # Si el primer campo es un número o vacío (Casos "18 | ..." o " | ...")
        # los datos están en [1], [2], [3]
        if es_campo_numero_vacio:
            nombre = campos[1].strip() if len(campos) > 1 else ""
            tipo = campos[2].strip() if len(campos) > 2 else ""
            # --- ¡CAMBIO AQUÍ! ---
            # Limpiamos espacios Y el carácter "|" del final
            cinta_str = campos[3].strip().strip('|').strip() if len(campos) > 3 else ""
        # Si el primer campo NO es un número (Caso "HIGH NOON | ...")
        # los datos están en [0], [1], [2]
        else:
            nombre = campos[0].strip() if len(campos) > 0 else ""
            tipo = campos[1].strip() if len(campos) > 1 else ""
            # --- ¡CAMBIO AQUÍ! ---
            # Limpiamos espacios Y el carácter "|" del final
            cinta_str = campos[2].strip().strip('|').strip() if len(campos) > 2 else ""


        # --- ¡CAMBIO DE LÓGICA DE VALIDACIÓN! ---
        # Ya no validamos por 'numero_str'. Validamos por 'nombre'.
        # Si no hay nombre, la línea no es válida.
        if not nombre:
            # (Opcional) Puedes comentar la línea de abajo si no quieres ver este aviso
            print(f"⚠️ Advertencia: Se ignoró la línea con 'Nombre' vacío: '{linea_limpia}'")
            continue # Saltar a la siguiente línea
        
        # --- ¡CAMBIO EN LA CREACIÓN DE REGISTRO! ---
        # Creamos el diccionario para este registro
        # Usamos nuestro 'contador_registros' para el campo "Numero"
        registro_dato = {
            "Numero": str(contador_registros), # <-- Usamos el contador
            "Nombre": nombre,
            "Tipo": tipo,
            "Cinta": cinta_str
        }
        print(f"➕ Añadiendo registro: {registro_dato}")
        # Esta línea es IDÉNTICA a tu código anterior:
        database["datos"].append(registro_dato)

        # --- ¡CAMBIO EN LA ACTUALIZACIÓN DE numReg! ---
        # 'numReg' ahora también se basa en nuestro contador,
        # imitando tu lógica de que guarde el último número.
        database["numReg"] = str(contador_registros)

        # --- Incrementamos el contador para el próximo registro ---
        contador_registros += 1

    # (Ya no necesitamos la variable 'ultimo_numReg_encontrado')

    print(f"✅ Carga completada. Se procesaron {len(database['datos'])} registros.")
    
    # Devolvemos la base de datos completa
    return database


# --------------------------------------------------------------------------
# EJEMPLO DE CÓMO USAR ESTE FICHERO
# (Esta parte solo se ejecuta si lanzas 'lector_db.py' directamente)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    
    print("--- Ejecutando prueba de 'lector_db.py' ---")
    procesar()
    # El fichero que nos adjuntaste
    FICHERO_DE_PRUEBA = "salida_ocr_columnas.txt"
    
    if os.path.exists(FICHERO_DE_PRUEBA):
        # 1. Llamamos a la función
        mi_db = cargar_datos_desde_fichero(FICHERO_DE_PRUEBA)
        
        # 2. Comprobamos los resultados
        if mi_db:
            print("\n--- Primeros 3 registros cargados: ---")
            print(mi_db["datos"][:3])
            
            print("\n--- Último 'numReg' guardado: ---")
            print(mi_db["numReg"])
    else:
        print(f"\nAVISO: No se encontró el fichero '{FICHERO_DE_PRUEBA}'.")
        print("Asegúrate de que esté en la misma carpeta para poder probar.")

