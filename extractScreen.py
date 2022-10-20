from pytesseract import pytesseract
import cv2 as cv
import numpy as np
import re

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

        res=res.replace("'", " ")

        res=res.split()

        if "Do" in res:
            
            percePos=res.index("Do")

            del res[(percePos-1):(percePos+2)]

        res = [x for x in res if len(x) > 2]

        if "Pie" in res:
            res.remove("Pie")
            
        return res

    def extractMain(self, path_to_images):

        img = cv.imread(path_to_images)
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

        #extract the two text from the image and process them with regex
        res1=self.extractPrepare(img1)
        res2=self.extractPrepare(img2)

        #take only intersection
        res= self.intersection(res1, res2)

        return res
