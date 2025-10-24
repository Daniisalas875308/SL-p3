from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import os
import re

# 🧠 Ruta al ejecutable Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 📁 Carpeta donde DOSBox guarda las capturas
capture_dir = r"C:\Users\samuel\AppData\Local\DOSBox\capture"

# 📋 Buscar todas las imágenes PNG, ordenadas por nombre (gwbasic_001.png, gwbasic_002.png, ...)
imagenes = sorted([
    os.path.join(capture_dir, f)
    for f in os.listdir(capture_dir)
    if f.lower().endswith(".png")
])

# ⚙️ Configuración OCR
custom_config = r'--oem 3 --psm 4'

# 📄 Fichero de salida
output_file = "salida_ocr.txt"

if not imagenes:
    print("⚠️ No se encontró ninguna captura en la carpeta capture.")
else:
    print(f"📷 {len(imagenes)} capturas encontradas.")
    texto_total = ""

    for idx, ruta in enumerate(imagenes, 1):
        print(f"\n🔹 Procesando {os.path.basename(ruta)} ({idx}/{len(imagenes)})")

        # --- Preprocesado ---
        img = Image.open(ruta).convert("L")
        img = ImageOps.invert(img)
        img = img.filter(ImageFilter.MedianFilter(size=1))
        img = ImageEnhance.Contrast(img).enhance(4.0)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.point(lambda x: 0 if x < 150 else 255, "1")

        w, h = img.size
        img = img.crop((5, int(h * 0.08), w - 5, int(h * 0.95)))

        # --- OCR ---
        texto = pytesseract.image_to_string(img, lang="eng", config=custom_config)

        # --- Limpieza ---
        texto_limpio = re.sub(r'[^A-Z0-9\s,\'".:-]', '', texto.upper())
        texto_limpio = re.sub(r'\s{2,}', ' ', texto_limpio)

        # --- Separar registros correctamente ---
        texto_formateado = re.sub(r'(?<=\D)(\d{1,3})\s(?=[A-Z])', r'\n\1 ', texto_limpio)

        texto_total += f"\n### {os.path.basename(ruta)} ###\n{texto_formateado.strip()}\n"

    # --- Guardar todo el texto en un solo archivo ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(texto_total)

    print(f"\n✅ OCR completado. Resultado guardado en: {output_file}")
