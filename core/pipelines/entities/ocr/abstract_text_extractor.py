"""Classe astratta relativa alla definizione degli estrattori di testo"""

from typing import Optional
from abc import abstractmethod, ABC
from core.models.entities.ocr import dct_ocr_factory


class TextExtractor(ABC):
    """
    Classe astratta relativa alla definizione degli estrattori di testo.
    """

    provider: str
    service: str

    def __init__(
        self,
        model_ocr: str,
        token: [dict, str] = None,
        use_case: Optional[str] = None,
        *args,
        **kwargs
    ):
        """
        Medoto di inizializzazione dell'estrattore di testo astratto. Questo metodo valorizza gli attributi di classe
        relativi al nome del modello OCR da impiegare per l'estrazione e all'eventuale token contenente le credenziali
        (indirizzo api e chiave associata) necessarie a svolgere la chiamata al servizio OCR.

        :param model_ocr: nome del modello OCR.
        :type model_ocr: str
        :param token: token contenente le credenziali necessarie per la chiamata al servizio OCR.
        :type token: (dict, optional)
        """
        self.ocr_model = dct_ocr_factory.get(model_ocr)
        self.token = token
        self.use_case = use_case

    @abstractmethod
    def extract_text_from_image(self, img: bytes, *args, **kwargs) -> dict:
        """
        Metodo astratto per l'estrazione di testo da immagine.
        """
        pass

    @abstractmethod
    def extract_text_from_pdf(self, pdf: bytes, *args, **kwargs) -> dict:
        """
        Metodo astratto per l'estrazione di testo da pdf.
        """
        pass
