"""Modulo contenente la classe che consente la creazione dello splitter di un file PDF"""

from typing import Optional
from config.parameters import SplitterDefaultConfig
from core.data.entities import Pdf2ImageSplitter


class PdfSplitter:
    """
    Classe associata alla defnizione dello splitter, utilizzato per suddividere un file PDF in sezioni e poi convertire
    le sezioni in immagini.

    La classe PdfExtractor gestisce la configurazione dei parametri dpi e scala di grigi. Utilizza un
    `Pdf2ImageSplitter` per suddividere il PDF in immagini.
    """

    dpi_default: int = SplitterDefaultConfig.dpi
    greyscale_default: str = str(SplitterDefaultConfig.greyscale)

    def __init__(
        self,
        params: dict,
        page_from: int = SplitterDefaultConfig.start_page,
        page_to: Optional[int] = None,
    ) -> None:
        """
        Metodo di inizializzazione dell'oggetto PdfExtractor con i parametri specificati e crea uno splitter per il PDF.

        :param params: Parametri di configurazione per l'estrazione delle immagini.
        :type params: dict
        :param page_from: Numero della pagina del file pdf da cui iniziare l'estrazione. Default a
            SplitterDefaultConfig.start_page (1).
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere l'estrazione. Default a None (estrazione prosegue fino
            alla fine del file).
        :type page_to: (int, optional)
        """
        self.ext_params, self.splitter = self.__create_splitter(
            params=params, page_from=page_from, page_to=page_to
        )

    def __create_splitter(
        self,
        params: dict = None,
        page_from: int = SplitterDefaultConfig.start_page,
        page_to: int = None,
    ):
        """
        Metodo privato che crea un'istanza di Pdf2ImageSplitter con i parametri di configurazione specificati.

        Questo metodo configura i parametri e crea un'istanza di `Pdf2ImageSplitter`
        per suddividere il pdf nelle immagini corrispondenti alle singole pagine.

        :param params: Parametri di configurazione per l'estrazione.
        :type params: (dict, optional)
        :param page_from: Numero della pagina del file pdf da cui iniziare l'estrazione. Default a
            SplitterDefaultConfig.start_page (1).
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere l'estrazione. Default a None (estrazione prosegue fino
            alla fine del file).
        :type page_to: (int, optional)

        :return: Una tupla contenente i parametri di configurazione e l'istanza di `Pdf2ImageSplitter`.
        :rtype: tuple
        """
        splitter = Pdf2ImageSplitter(
            dpi=params["dpi"],
            greyscale=params["greyscale"],
            start_page=page_from,
            end_page=page_to,
        )

        return params, splitter
