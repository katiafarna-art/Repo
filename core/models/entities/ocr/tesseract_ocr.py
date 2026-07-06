"""Modulo contenente la classe concreta per lo strumento ocr Tesseract"""

import requests
import pytesseract
from typing import Optional, Literal
from PIL import Image
from config.parameters import TesseractDefaultConfig
from core.models.entities.ocr.abstract_ocr import AbstractOCR

from requests.packages.urllib3.exceptions import InsecureRequestWarning  # noqa

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # noqa


class TesseractOCR(AbstractOCR):
    """
    Classe relativa all'estrazione di testo utilizzando l'OCR Tesseract.

    Questa classe consente l'estrazione di testo a partire da file immagine utilizzando l'engine OCR Tesseract.
    Le lingue relative all'immagine su cui svolgere l'estrazione ed eventuali ulteriori parametri legati
    all'esecuzione dell'OCR sono utilizzati nella chiamata della funzione *image_to_string* appartenenete alla libreria
    pytesseract.

    Attributi:

    * mode_name (str): Il nome del modello OCR utilizzato. Default a "tesseract".
    * version (str): Versione del modello utilizzato. Default a "5.3.4"

    """

    model_name: str = "tesseract"
    version: str = "5.3.4"

    @staticmethod
    def _extract_params(params: Optional[dict] = None) -> str:
        """
        Metodo privato per l'estrazione dei parametri da utlizzare per la chiamata della funzione di estrazione di testo
        da immagine di Tesseract.
        Nello specifico, qualora il dizionario "params" venga passato in input alla funzione, verrà estratta la stringa
        contenuta nella chiave "config".

        :param params:  Dizionario contenente le configurazioni dei parametri da impiegare per la chiamata a Tesseract.
            Default a None.
        :type params: (dict, optional)

        :return: configurazioni da impiegare per la chiamata a Tesseract.
        :rtype: str
        """
        if not params or not isinstance(params, dict):
            config = TesseractDefaultConfig.config
        else:
            config = params.get("config", TesseractDefaultConfig.config)

        return config

    def extract_text_from_img(
        self, img: Image.Image, languages: list, params: Optional[dict] = None,
            tesseract_mode: Literal["text", "data"] = None,
    ) -> str:
        """
        Metodo relativo all'estrazione di testo da file immagine. Nello specifico, viene svolta la chiamata all'OCR
        Tesseract utilizzando i parametri e le lingue fornite in input, richiamando il metodo 'image_to_String' della
        libreria 'pytesseract'.

        :param img: immagine su cui svolgere l'estrazione del testo.
        :type img: Image.Image
        :param languages: lingue relative all'immagine.
        :type languages: list
        :param params: Parametri da impiegare per la chiamata a Tesseract. Defalut a None.
        :type params: (dict, optional)
        :param tesseract_mode: parametro che ci permette di distinguere tra le chiamate a Tesseract per l'estrazione di 
        solo testo (image_to_string) e per l'estrazione dei metadati (image_to_data)
        :type tesseract_mode: (Literal["text", "data"], optional)
        
        :return: La funzione restituisce il risultato dell'estrazione svolta tramite l'OCR Tesseract.
        :rtype: str
        """
        config = self._extract_params(params)
        language = "+".join(languages) if languages else "ita"

        if tesseract_mode == "data":
            return pytesseract.image_to_data(image=img, lang=language, config=config, output_type="dict")
        else:
            return pytesseract.image_to_string(image=img, lang=language, config=config)
