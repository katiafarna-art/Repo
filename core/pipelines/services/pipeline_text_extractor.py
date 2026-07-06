"""Modulo contenente le pipeline di estrazione di testo da immagini e pdf basate su servizi OCR"""

import logging
from typing import Optional, Literal
from config.parameters import ETA_PAGE_DEFAULT
from core.pipelines.entities.ocr import dct_extractor
from core.routines.services import track_and_save_results


def extract_text_from_image(
    img: bytes,
    service: str,
    languages: Optional[list] = None,
    params: Optional[dict] = None,
    num_page: int = 1,
    token: [dict, str] = None,
    use_case: Optional[str] = None,
    interaction_mode: Literal["sync", "async"] = "async",
    job_id: Optional[str] = None,
    expected_eta: Optional[float] = ETA_PAGE_DEFAULT,
):
    """
    Funzione relativa alla pipeline di estrazione di testo a partire da un file immagine utilizzando servizi OCR.

    Descrizione: Questa funzione contiene la pipeline relativa all'estrazione di testo da un file immagine.
    Come prima cosa, qualora il servizio richiamato (parametro 'service') sia "document_intelligence", il
    token fornito in input viene decrittato in modo tale da avere accesso alle credenziali necessarie per richiamare i
    servizi Azure Document Intelligence.
    Successivamente viene definito l'estrattore relativo al servizio desiderato, il quale viene impiegato
    per svolgere l'estrazione del testo dall'immagine, utilizzando gli altri eventuali parametri forniti
    in input alla funzione.
    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del
    json va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param img: immagine su cui svolgere l'estrazione del testo.
    :type img: bytes
    :param service: nome del servizio relativo all'engine OCR desiderato.
    :type service: str
    :param languages: lista delle lingue relative al contenuto del file immagine. Default a None.
    :type languages: (list, optional)
    :param params: dizionario contenente i valori associati ad ulteriori parametri relativi all'esecuzione
        dell'estrazione del testo. Default a None.
    :type params: (dict, optional)
    :param num_page: numero da associare all'immagine fornita in input. Default a 1.
    :type num_page: (int, optional)
    :param token: token cifrato contenente le informazioni necessarie per svolgere la chiamata al modello OCR. Default a
        None.
    :type token: (dict, optional)
    :param use_case: codice identificativo univoco associato al progetto che richiama l'esecuzione della pipeline
        necessario per l'interazione con il layer-ai.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal['sync', 'async'], optional)
    :param job_id: codice identificativo univoco associato all'esecuzione della pipeline di estrazione del testo.
        Default a None.
    :type job_id: (str, optional)
    :param expected_eta: numero di secondi stimati per l'esecuzione dell'estrazione del testo. Default a 5 secondi.
    :type expected_eta: (float, optional)

    :return: La funzione restituisce il risultato dell'estrazione qualora essa vada a buon fine. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.
    """

    logging.info(f"Starting text extraction from image for service {service}")
    extractor = dct_extractor[service](token=token, use_case=use_case)

    func_kwargs = {
        "img": img,
        "languages": languages,
        "params": params,
        "num_page": num_page,
        "interaction_mode": interaction_mode,
    }

    return track_and_save_results(
        callable_func=extractor.extract_text_from_image,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )


def extract_text_from_pdf(
    pdf: bytes,
    service: str,
    languages: Optional[list] = None,
    params: Optional[dict] = None,
    page_from: int = 1,
    page_to: Optional[int] = None,
    token: [dict, str] = None,
    use_case: Optional[str] = None,
    interaction_mode: Literal["sync", "async"] = "async",
    job_id: Optional[str] = None,
    expected_eta: Optional[float] = ETA_PAGE_DEFAULT,
    tesseract_mode: Literal["text", "data"] = "text",
):
    """
    Funzione relativa alla pipeline di estrazione di testo a partire da un file pdf utilizzando servizi OCR.

    Descrizione: Questa funzione contiene la pipeline relativa all'estrazione di testo da un file pdf.
    Come prima cosa, qualora il servizio richiamato (parametro 'service') sia "document_intelligence", il
    token fornito in input viene decrittato in modo tale da avere accesso alle credenziali necessarie per richiamare i
    servizi Azure Document Intelligence.
    Successivamente viene definito l'estrattore relativo al servizio desiderato, il quale viene impiegato
    per svolgere l'estrazione del testo dal file pdf, utilizzando gli altri eventuali parametri forniti
    in input alla funzione.
    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del json
    va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param pdf: file pdf su cui svolgere l'estrazione del testo.
    :type pdf: bytes
    :param service: nome del servizio relativo all'engine OCR desiderato.
    :type service: str
    :param languages: lista delle lingue relative al contenuto del file pdf. Default a None.
    :type languages: (list, optional)
    :param params: dizionario contenente i valori associati ad ulteriori parametri relativi all'esecuzione
        dell'estrazione del testo. Default a None.
    :type params: (dict, optional)
    :param page_from: pagina relativa al file pdf da cui partire a svolgere l'estrazione del testo. Default a 1.
    :type page_from: (int, optional)
    :param page_to: pagina relativa al file pdf dove interrompere l'estrazione del testo. Default a None (estrazione
        prosegue fino alla fine del file).
    :type page_to: (int, optional)
    :param token: token cifrato contenente le informazioni necessarie per svolgere la chiamata al modello OCR. Default a
        None.
    :type token: (dict, optional)
    :param use_case: codice identificativo univoco associato al progetto che richiama l'esecuzione della pipeline
        necessario per l'interazione con il layer-ai.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal['sync', 'async'], optional)
    :param job_id: codice identificativo univoco associato all'esecuzione della pipeline di estrazione del testo.
        Default a None.
    :type job_id: (str, optional)
    :param expected_eta: numero di secondi stimati per l'esecuzione dell'estrazione del testo. Default a 5 secondi.
    :type expected_eta: (float, optional)
    :param tesseract_mode: parametro che ci permette di distinguere tra le chiamate a Tesseract per l'estrazione di 
    solo testo (image_to_string) e per l'estrazione dei metadati (image_to_data)
    :type tesseract_mode: (Literal['text', 'data'], optional)

    :return: La funzione restituisce il risultato dell'estrazione qualora essa vada a buon fine. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.
    """

    logging.info(f"Starting text extraction from pdf for service {service}")
    extractor = dct_extractor[service](token=token, use_case=use_case)

    # TODO: add validation here
    func_kwargs = {
        "pdf": pdf,
        "languages": languages,
        "params": params,
        "page_from": page_from,
        "page_to": page_to,
        "interaction_mode": interaction_mode,
    }

    if service == "tesseract":
        func_kwargs["tesseract_mode"] = tesseract_mode

    return track_and_save_results(
        callable_func=extractor.extract_text_from_pdf,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )
