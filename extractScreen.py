from pytesseract import pytesseract
import cv2 as cv
import numpy as np
from urllib.request import Request, urlopen
import re
import asyncio

FIRST=["Vittoria", "Sconfitta", "Victory", "Victoire", "Defeat", "Défaite"]
WINNERS=["Vincitori", "Gagnants"]
LOSERS=["Sconfitti", "Perdants"]
class DofusScreenExtractor:
    
    def __init__(self, path_to_tesseract, conf):
        pytesseract.tesseract_cmd = path_to_tesseract
        self.conf = conf

    def intersection(self,lst1, lst2):
    
        # Use of hybrid method
        temp = set(lst2)
        lst3 = [value for value in lst1 if value in temp]
        return lst3

    def extractPrepare(self, img):

        text = pytesseract.image_to_string(img, config=self.conf)

        res=re.sub('[^A-Za-z-\[\] \n\'аАбБвВгГдДеЕёЁжЖзЗиИйЙкКлЛмМнНоОпПрРсСтТуУфФхХцЦчЧшШщЩъЪыЫьЬэЭюЮяЯ]+', '', text)
        
        res=res.replace("'", "' ")

        res=res.split()

        if "Do'" in res:
            percePos=res.index("Do'")

            res[percePos-1]="Perce"
            
            del res[(percePos):(percePos+2)]
            
        elif "Do" in res:
            
            percePos=res.index("Do")

            res[percePos-1]="Perce"
            
            del res[(percePos):(percePos+2)]

        res = [x for x in res if len(x) > 2]

        if "Pie" in res:
            res.remove("Pie")
            
        return res

    async def extractMain(self, url):

        #img = cv.imread(url)
        #req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        #img = np.asarray(bytearray(urlopen(req).read()), dtype="uint8")
        img = np.asarray(bytearray(url), dtype="uint8")
        img = cv.imdecode(img, cv.IMREAD_COLOR)
        
        (h, w) = img.shape[: 2]

        img = cv.resize(img, (w * 2, h * 2), cv.INTER_LINEAR)
        img = img[0:img.shape[0], 0:round(w/2.2)]    
        img=cv.cvtColor(img, cv.COLOR_BGR2GRAY)

        #prepare the first image, apply binary inversion
        __ ,img1 = cv.threshold(img,127,255,cv.THRESH_BINARY_INV)
        kernel = np.ones((2, 2), np.uint8)
        img1 = cv.erode(img1, kernel, iterations=1)
        #prepare the second image, apply tozero and then not
        __ ,img2 = cv.threshold(img,127,255,cv.THRESH_TOZERO)
        img2 =cv.bitwise_not(img2)
        img2 = cv.erode(img2, kernel, iterations=1)

        #extract the two text from the image and process them with regex
        res1=self.extractPrepare(img1)
        res2=self.extractPrepare(img2)
            
        #take only intersection
        res= self.intersection(res1, res2)

        if res[0] in FIRST:
            del res[0]
        
        return res
