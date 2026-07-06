"""Modulo contenente la classe Splitter necessaria per la divisione dei file PDF in sezioni di pagine."""

import io
import base64
from typing import Optional
from PIL import Image
from pdf2image import convert_from_bytes
from config.parameters import SplitterDefaultConfig
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInputError


class Pdf2ImageSplitter:
    """
    Classe relativa alla definizione di oggetti splitter per la suddivisione di file PDF in sezioni di pagine e la
    conversione delle pagine in immagini.
    """

    split_chunk: int = SplitterDefaultConfig.num_chunk

    def __init__(
        self,
        dpi: int = SplitterDefaultConfig.dpi,
        greyscale: bool = SplitterDefaultConfig.greyscale,
        start_page: int = SplitterDefaultConfig.start_page,
        end_page: Optional[int] = None,
    ):
        """
        Metodo di inizializzazione dell'oggetto splitter.
        Questo metodo valorizza gli attributi di classe relativi a dpi e scala di grigi dell'immagine e range di
        pagine del file da convertire. Tale range è anche validato.

        :param dpi: Valore dpi dell'immagine. Default a SplitterDefaultConfig.dpi (250)
        :type dpi: (int, optional)
        :param greyscale: parametro associato alla scala di grigi. Default a SplitterDefaultConfig.greyscale (False).
        :type greyscale: (bool, optional)
        :param start_page: pagina del file PDF a partire dalla quale svolgere le operazioni. Default a
            SplitterDefaultConfig.start_page (1).
        :type start_page: (int, optional)
        :param end_page: pagina del file PDF alla quale interrompere le operazioni. Default a None (operazioni svolte
            fino alla fine del file).
        :type end_page: (int, optional)
        """
        self.dpi = dpi
        self.greyscale = greyscale
        self._validate_range(start_page=start_page, end_page=end_page)
        self.start_from = start_page
        self.end_to = end_page
        self.bookmark = start_page

    @staticmethod
    def _validate_range(start_page: Optional[int], end_page: Optional[int]):
        """
        Metodo statico per la validazione del range di pagine del file pdf.

        :param start_page: pagina del file PDF a partire dalla quale svolgere le operazioni. Default a None.
        :type start_page: (int, optional)
        :param end_page: pagina del file PDF alla quale interrompere le operazioni. Default a None.
        :type end_page: (int, optional)
        """
        if end_page is not None and start_page is not None and end_page < start_page:

            raise SmartOCRInputError(
                f"Method Pdf2ImageSplitter.{get_function_name()}: "
                "The provided interval of pages is not valid"
                f"(page_to {end_page} must be >= page_from {start_page})"
            )

    @staticmethod
    def _get_image_base64(image: Image.Image) -> bytes:
        """
        Metodo privato che restituisce un'immagine in formato base64.

        :param image: immagine
        :type image: PIL.Image

        :return: immagine in formato base64
        :rtype: bytes
        """
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
        return img_base64

    def get_next_split(self, pdf_content: bytes, return_bytes: bool = False) -> list:
        """
        Metodo che consente di svolgere la conversione in immagini di un file pdf, suddividendo quest'ultimo in
        sottosezioni ('chunk'). Le immagini del 'chunk' e i corrispettivi numeri di pagina del file sono restituite.

        :param pdf_content: file pdf
        :type pdf_content: bytes
        :param return_bytes: parametro che consente di scegliere se restituire le immagini in formato base64 o in
            formato PIL.Image. Default a False (immagini restituite come PIL.Image).
        :type return_bytes: (bool, optional)

        :return: 'chunk' di immagini associate alle pagine del pdf.
        :rtype: list
        """
        end_chunk = min(self.bookmark + self.split_chunk, self.end_to or float("inf"))

        images = convert_from_bytes(
            pdf_file=pdf_content,
            dpi=self.dpi,
            grayscale=self.greyscale,
            first_page=self.bookmark,
            last_page=end_chunk,
        )

        chunk = [
            {
                "pag": idx + self.bookmark,
                "img": self._get_image_base64(img) if return_bytes else img,
            }
            for idx, img in enumerate(images)
        ]

        if images:
            self.bookmark = end_chunk + 1

        return chunk
