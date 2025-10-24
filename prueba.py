from PIL import Image
import pytesseract
import os


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
capture_dir = r"C:\Users\danii\AppData\Local\DOSBox\capture"

imagenes = sorted([
    os.path.join(capture_dir, f)
    for f in os.listdir(capture_dir)
    if f.lower().endswith(".png")
])

if not imagenes:
    print("No se encontraron imágenes en la carpeta capture.")
else:
    # Solo la primera imagen
    ruta = imagenes[0]
    texto = pytesseract.image_to_string(Image.open(ruta))
    print(f"\n--- {os.path.basename(ruta)} ---")
    print(texto)