"""Modulo contenente la classe dell'estrattore di testo tramite tesseract"""

import time
import json
import asyncio
import logging
from typing import Optional, Literal
from io import BytesIO
from PIL import Image
from config.parameters import SplitterDefaultConfig, TesseractDefaultConfig
from core.data.entities import is_valid_params, Pdf2ImageSplitter
from core.pipelines.entities.ocr.abstract_text_extractor import TextExtractor
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInputError

# TODO: va portata la logica della splliter_pipeline


class TesseractExtractor(TextExtractor):
    """
    Classe associata alla definizione dell'estrattore di testo tramite l'OCR tesseract.

    Questa classe fornisce metodi per configurare e utilizzare l'OCR Tesseract per estrarre testo da immagine o PDF.
    In particolare, permette la configurazione dei parametri associati all'immagine e all'OCR, e offre
    funzionalità di estrazione.

    Attributi:

    * provider (str): Il fornitore del servizio OCR. Default a "isp".
    * service (str): Il servizio OCR utilizzato. Default a "tesseract".
    * model_ocr (str): Il modello OCR utilizzato. Default a "tesseract".

    """

    provider: str = "isp"
    service: str = "tesseract"
    model_ocr: str = "tesseract"

    def __init__(self, token: Optional[dict] = None, use_case: Optional[str] = None):
        """
        Metodo di inizializzazione dell'oggetto estrattore. Questo metodo valorizza gli attributi di classe relativi al
        numero dpi, alla scala di grigi e ad ulteriori configurazioni per la chiamata a tesseract. Tali valori di
        default, alla versione attuale del servizio, i valori di default sono: 250, False e '', rispettivamente.
        Il nome del modello OCR ("tesseract") e l'eventuale token sono inizializzati attraverso il super().__init__()
        della classe astratta *TextExtractor*.

        :param token: token contenente le credenziali necessarie per la chiamata al servizio OCR. Default a None.
        :type token: (dict, optional)
        """
        super().__init__(model_ocr=self.model_ocr, token=token, use_case=use_case)
        self.dpi_default = SplitterDefaultConfig.dpi
        self.greyscale_default = str(SplitterDefaultConfig.greyscale)
        self.config_default = TesseractDefaultConfig.config

    def _extract_image_params(self, params: dict) -> dict:
        """
        Metodo privato che estrae e valida i parametri relativi alla configurazione dell'immagine ('dpi' e 'greyscale').
        Qualora i volari non siano specificati tramite il parametro in input al metodo, vengono utilizzati i valori di
        default associati ai corrispettivi attributi di classe.

        :param params: Dizionario contenente i parametri di configurazione dell'immagine.
        :type params: dict

        :return: Dizionario contenente i parametri validati per l'immagine, come `dpi` e `greyscale`.
        :rtype: dict

        :raises Exception: Se i parametri `dpi` o `greyscale` non sono del tipo corretto.
        """
        logging.debug("Extracting image configuration")

        dpi = params["args"].get("image", dict()).get("dpi", self.dpi_default)
        greyscale = (
            params["args"].get("image", dict()).get("greyscale", self.greyscale_default)
        )

        if not isinstance(dpi, int):
            raise SmartOCRInputError(
                f"Method {self.__class__.__name__}.{get_function_name()}: "
                "Error in extracting image configuration: if specified, 'dpi' must be an integer!"
            )

        if greyscale not in {"True", "False"}:
            raise SmartOCRInputError(
                f"Method {self.__class__.__name__}.{get_function_name()}: "
                "Error in extracting image configuration: if specified, 'greyscale' must be of str-type and either "
                "'True' or 'False'"
            )

        greyscale_bool = True if greyscale.lower() == "true" else False
        return {"dpi": dpi, "greyscale": greyscale_bool}

    def _extract_ocr_params(self, params: dict):
        """
        Metodo privato che estrae il parametro di configurazione per l'OCR tesseract. Qualora il volare non sia
        specificato tramite il parametro in input al metodo, viene utilizzato il valore di default associato al
        corrispettivo attributo di classe.

        :param params: Dizionario contenente i parametri di configurazione del modello OCR.
        :type params: dict

        :return: Dizionario contenente i parametri valorizzati di configurazione per l'OCR.
        :rtype: dict
        """
        logging.debug("Extracting OCR configuration")

        config = params["args"].get("model", dict()).get("config", self.config_default)

        return {"config": config}

    def _configure(self, params: dict) -> dict:
        """
        Metodo privato che configura i parametri di estrazione utilizzando i valori di default e/o i valori forniti
        dall'utente.

        :param params: Dizionario contenente i parametri di configurazione forniti dall'utente.
        :type params: dict

        :return: Dizionario contenente la configurazione completa per l'estrazione con tutti i parametri correttamente
            validati e valorizzati.
        :rtype: dict
        """
        logging.debug("Extracting request configuration")
        greyscale_bool = True if self.greyscale_default.lower() == "true" else False
        image_params = {"dpi": self.dpi_default, "greyscale": greyscale_bool}
        ocr_params = {"config": self.config_default}
        dct_configuration = {"image_params": image_params, "ocr_params": ocr_params}

        if is_valid_params(params):
            dct_configuration["image_params"] = self._extract_image_params(params)
            dct_configuration["ocr_params"] = self._extract_ocr_params(params)

        return dct_configuration

    def _postprocess_output(
        self, raw_output: dict, params: dict, languages: Optional[list] = None
    ) -> dict:
        """
        Metodo privato che esegue la post-elaborazione dell'output generato dall'OCR.

        :param raw_output: Risultato (non elaborato) dell'estrazione OCR.
        :type raw_output: dict
        :param params: Parametri di configurazione utilizzati durante l'estrazione.
        :type params: dict
        :param languages: Lingue utilizzate per l'estrazione. Default a None.
        :type languages: (list, optional)

        :return: Dizionario contenente l'output post-elaborato. Nello specifico, il dizionario contiene il testo
            estratto sotto la chiave 'texts' e le informazioni aggiuntive relative all'estrazione sotto la chiave
            'extra'.
        :rtype: dict
        """
        logging.debug("Postprocessing raw OCR output")

        if "greyscale" in params["image_params"]:
            params["image_params"]["greyscale"] = str(
                params["image_params"]["greyscale"]
            )

        params["ocr_params"]["languages"] = "-".join(languages) if languages else "ita"

        return {
            "texts": raw_output,
            "extra": {
                "request_info": {
                    "provider": self.provider,
                    "service": self.service,
                    "model": self.ocr_model.model_name,
                    "model_version": self.ocr_model.version,
                },
                "execution_params": params,
            },
        }

    def _extraction(
        self,
        input_params: dict,
        splitter: Pdf2ImageSplitter,
        pdf: bytes,
        languages: Optional[list] = None,
        tesseract_mode: Literal["text", "data"] = None,
    ) -> dict:
        """
        Metodo privato che esegue l'estrazione del testo da un PDF tramite l'OCR. Nello specifico, il file PDF viene
        suddiviso in sezioni ('chunk'), ciascuna pagina di ogni sezione viene convertita in immagine su cui viene
        svolta l'estrazione del testo tramite OCR. I risultati relativi all'estrazione per ogni sezione vengono poi
        agglomerati in un unico output.

        :param input_params: Parametri di input per l'estrazione, inclusi quelli relativi all'immagine e al modello OCR.
        :type input_params: dict
        :param splitter: Oggetto Pdf2ImageSplitter utilizzato per dividere il PDF in immagini.
        :type splitter: Pdf2ImageSplitter
        :param pdf: PDF su cui svolgere l'estrazione del testo.
        :type pdf: bytes
        :param languages: Lingue da utilizzare durante l'estrazione OCR. Default a None.
        :type languages: (list, optional)
        :param tesseract_mode: parametro che ci permette di distinguere tra le chiamate a Tesseract per l'estrazione di 
        solo testo (image_to_string) e per l'estrazione dei metadati (image_to_data)
        :type tesseract_mode: (Literal["text", "data"], optional)

        :return: Dizionario contenente il testo estratto e le informazioni aggiuntive sotto le rispettive chiavi 'texts'
            e 'extra'.
        :rtype: dict
        """
        start_time = time.time()
        splitting: bool = True
        texts = dict()

        while splitting:
            chunk = splitter.get_next_split(pdf_content=pdf)

            if len(chunk) == 0:
                splitting = False

            else:
                for elem in chunk:
                    texts[
                        f"pag_{elem['pag']}"
                    ] = self.ocr_model().extract_text_from_img(
                        img=elem["img"],
                        languages=languages,
                        params=input_params["ocr_params"],
                        tesseract_mode=tesseract_mode,
                    )

        elapsed_time = time.time() - start_time
        logging.debug(
            f"Correctly performed OCR on {len(list(texts.keys()))} pages in {elapsed_time} seconds"
        )

        return self._postprocess_output(
            raw_output=texts, params=input_params, languages=languages
        )

    def create_splitter(
        self, params: dict = None, page_from: int = 1, page_to: int = None
    ):
        """
        Metodo che crea e configura un oggetto Pdf2ImageSplitter necessario per dividere il PDF in sezioni di immagini.

        :param params: Parametri di configurazione per lo splitter. Default a None.
        :type params: (dict, optional)
        :param page_from: Numero della pagina del file pdf da cui iniziare lo splitting. Default a 1.
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere lo splitting. Default a None (splitting prosegue fino
            alla fine del file).
        :type page_to: (int, optional)

        :return: Una tupla contenente i parametri di input e l'oggetto Pdf2ImageSplitter.
        :rtype: tuple
        """
        input_params = self._configure(params)

        splitter = Pdf2ImageSplitter(
            dpi=input_params["image_params"]["dpi"],
            greyscale=input_params["image_params"]["greyscale"],
            start_page=page_from,
            end_page=page_to,
        )

        return input_params, splitter

    async def async_extraction(
        self,
        input_params: dict,
        splitter: Pdf2ImageSplitter,
        pdf: bytes,
        languages: Optional[list] = None,
    ) -> dict:
        """
        Metodo che esegue l'estrazione del testo da un PDF tramite l'OCR in modalità asincrona.
        Nello specifico, il file PDF viene suddiviso in sezioni ('chunk'), ciascuna pagina di ogni sezione viene
        convertita in immagine su cui viene svolta l'estrazione del testo tramite OCR. Il risultato dell'estrazione
        viene restituito pagina per pagina. Nel caso si riscontrasse un errore durante l'estrazione, il metodo lo
        restituisce in output.

        :param input_params: Parametri di input per l'estrazione, inclusi quelli relativi all'immagine e al modello OCR.
        :type input_params: dict
        :param splitter: Oggetto Pdf2ImageSplitter utilizzato per dividere il PDF in sezioni di immagini.
        :type splitter: Pdf2ImageSplitter
        :param pdf: PDF sul quale svolgere l'estrazione del testo.
        :type pdf: bytes
        :param languages: Lingue da utilizzare durante l'estrazione OCR. Default a None.
        :type languages: (list, optional)ù

        :yield: Output dell'estrazione, pagina per pagina, in formato JSON.
        :rtype: dict
        """
        logging.debug("Extracting text from a PDF")

        start_time = time.time()
        splitting: bool = True

        if str(input_params["image_params"]["greyscale"]):
            input_params["image_params"]["greyscale"] = str(
                input_params["image_params"]["greyscale"]
            )

        input_params["ocr_params"]["languages"] = "-".join(languages)

        try:
            while splitting:
                chunk = splitter.get_next_split(pdf_content=pdf)

                if len(chunk) == 0:
                    splitting = False

                else:
                    try:
                        for elem in chunk:
                            str_pag = f"pag_{elem['pag']}"
                            text = self.ocr_model().extract_text_from_img(
                                img=elem["img"],
                                languages=languages,
                                params=input_params["ocr_params"],
                            )
                            yield json.dumps({str_pag: text}).encode("utf-8") + b"\n"

                            elapsed_time = time.time() - start_time
                            logging.debug(
                                f"Correctly performed OCR on page {str_pag} in {elapsed_time} seconds"
                            )
                            await asyncio.sleep(0.1)
                        yield json.dumps(
                            {
                                "extra": {
                                    "request_info": {
                                        "provider": self.provider,
                                        "service": self.service,
                                        "model": self.ocr_model.model_name,
                                        "model_version": self.ocr_model.version,
                                    },
                                    "execution_params": input_params,
                                }
                            }
                        ).encode("utf-8")

                    except Exception as e:
                        yield json.dumps({"error": str(e)}).encode("utf-8")

        except Exception as e:
            yield json.dumps({"error": str(e)}).encode("utf-8")

    def extract_text_from_image(
        self,
        img: bytes,
        languages: Optional[list] = None,
        params: Optional[dict] = None,
        num_page: int = 1,
        interaction_mode: Optional[str] = None,
    ) -> dict:
        """
        Metodo che estrae il testo da un'immagine tramite OCR. Nello specifico, vengono dapprima configurati i
        parametri relativi all'estrazione. Successivamente viene definito un oggetto OCR che svolge l'estrazione
        del testo dall'immagine. Il risultato dell'estrazione viene post-elaborato e restituito dal metodo.

        :param img: Immagine su cui svolgere l'estrazione del testo.
        :type img: bytes
        :param languages: Lingue da utilizzare durante l'estrazione. Default a None.
        :type languages: (list, optional)
        :param params: Parametri di configurazione opzionali per l'estrazione. Default a None.
        :type params: (dict, optional)
        :param num_page: Numero di pagina associato all'immagine. Default a 1.
        :type num_page: (int, optional)

        :return: Dizionario contenente il testo estratto e le informazioni aggiuntive relative all'estrazione.
        :rtype: dict
        """
        logging.debug("Extracting text from an image")
        img_pil = Image.open(BytesIO(img))

        input_params = self._configure(params)
        input_params["image_params"] = dict()

        texts = {
            f"pag_{num_page}": self.ocr_model().extract_text_from_img(
                img=img_pil, languages=languages, params=input_params["ocr_params"]
            )
        }
        return self._postprocess_output(
            raw_output=texts, params=input_params, languages=languages
        )

    def extract_text_from_pdf(
        self,
        pdf: bytes,
        languages: Optional[list] = None,
        page_from: int = 1,
        page_to: Optional[int] = None,
        params: Optional[dict] = None,
        interaction_mode: Literal["async", "sync"] = None,
        tesseract_mode: Literal["text", "data"] = None,
    ) -> dict:
        """
        Metodo che estrae il testo da un PDF tramite OCR. Nello specifico, viene definito uno splitter per processare
        il file in sezioni. Viene dunque svolta l'estrazione del testo.

        :param pdf: PDF su cui svolgere l'estrazione testo.
        :type pdf: bytes
        :param languages: Lingue da utilizzare durante l'estrazione. Default a None.
        :type languages: (list, optional)
        :param page_from: Numero della pagina del file pdf da cui iniziare lo splitting. Default a 1.
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere lo splitting. Default a None (splitting prosegue fino
            alla fine del file).
        :type page_to: (int, optional)
        :param params: Parametri di configurazione opzionali per l'estrazione. Default a None.
        :type params: (dict, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type: Literal["async", "sync"]
        :param tesseract_mode: parametro che ci permette di distinguere tra le chiamate a Tesseract per l'estrazione di 
        solo testo (image_to_string) e per l'estrazione dei metadati (image_to_data)
        :type tesseract_mode: Literal["text", "data"]
        :return: Dizionario contenente il testo estratto e le informazioni aggiuntive.
        :rtype: dict
        """
        logging.debug("Extracting text from a PDF")

        input_params, splitter = self.create_splitter(
            params=params, page_from=page_from, page_to=page_to
        )

        return self._extraction(
            input_params=input_params, splitter=splitter, pdf=pdf, languages=languages, tesseract_mode=tesseract_mode
        )
