from extractScreen import DofusScreenExtractor
path_to_tesseract = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
path_to_images = 'examples\\9.png'
conf= "--psm 6 -l eng+ita+fra+rus"

dse = DofusScreenExtractor(path_to_tesseract, conf)

print(dse.extractMain(path_to_images))