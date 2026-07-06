"""Modulo contenente le pipeline di estrazione di entità basata su servizi LM"""

from typing import Optional, Literal

from config.input_models.entity_extraction import EntityExtractionParams
from config.parameters import ETA_PAGE_DEFAULT
from core.pipelines.entities.entity_extraction import dct_entity_extractor
from core.routines.services import track_and_save_results


def extract_entity_from_image(
    img: list[bytes],
    service: str,
    json_entity: Optional[str] = None,
    text_extracted: Optional[dict] = None,
    language: Optional[str] = None,
    use_rag: bool = False,
    params: Optional[EntityExtractionParams] = None,
    token: Optional[str] = None,
    use_case: Optional[str] = None,
    interaction_mode: Literal["async", "sync"] = "async",
    job_id: Optional[str] = None,
    expected_eta: int = ETA_PAGE_DEFAULT,
) -> dict:
    """
    Funzione relativa alla pipeline di estrazione di entità a partire da un file immagine utilizzando servizi LM.

    Descrizione: Questa funzione contiene la pipeline relativa all'estrazione di entità da un file immagine.
    Come prima cosa, qualora il servizio richiamato (parametro 'service') sia "openai", il
    token fornito in input viene decrittato.
    Successivamente viene definito l'estrattore relativo al servizio desiderato, il quale viene impiegato
    per svolgere l'estrazione di entità dalle immagini, utilizzando gli altri eventuali parametri forniti
    in input alla funzione.
    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del json
    va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param img: immagini su cui svolgere l'estrazione dell'entità.
    :type img: list[bytes]
    :param json_entity: dizionario contenente le entità da ricercare nel file.
    :type json_entity: dict
    :param service: nome del servizio desiderato.
    :type service: str
    :param text_extracted: testo estratto relativo alle immagini fornite in input. Default a None.
    :type text_extracted: (dict, optional)
    :param use_rag: Parametro booleano associato all'impiego di un embedder. Default a False.
    :type use_rag: (bool, optional)
    :param params: Dizionario contenente ulteriori parametri relativi al modello LM (e all'eventuale embedder).
    :type params: (EntityExtractionParams, optional)
    :param token: token cifrato contenente le informazioni necessarie per svolgere la chimata al modello LM.
    :type token: (dict, optional)
    :param use_case: codice identificativo univoco associato al progetto che richiama l'esecuzione della pipeline
        necessario per l'interazione con il layer-ai.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal['sync', 'async'], optional)
    :param job_id: codice identificativo univoco associato all'esecuzione della pipeline di estrazione dell'entità.
        Default a None.
    :type job_id: (str, optional)
    :param expected_eta: numero di secondi stimati per l'esecuzione dell'estrazione dell'entità. Default a 5 secondi.
    :type expected_eta: (float, optional)

    :return: La funzione restituisce il risultato dell'estrazione qualora essa vada a buon fine. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.
    """

    use_rag = use_rag if text_extracted else False

    if (
        not text_extracted
        or not isinstance(text_extracted, dict)
        or not text_extracted.get("texts")
    ):
        text_extracted = {"texts": dict()}

    extractor = dct_entity_extractor[service](token, use_case)

    func_kwargs = {
        "img": img,
        "dct_entity": json_entity,
        "language": language,
        "text_extracted": text_extracted["texts"],
        "use_rag": use_rag,
        "params": params,
        "interaction_mode": interaction_mode,
    }

    return track_and_save_results(
        callable_func=extractor.extract_entity_from_image,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )


def extract_entity_from_text(
    service: str,
    text_extracted: dict,
    language: Optional[str] = None,
    json_entity: Optional[str] = None,
    use_rag: bool = False,
    params: Optional[EntityExtractionParams] = None,
    token: Optional[str] = None,
    use_case: Optional[str] = None,
    interaction_mode: Literal["async", "sync"] = "async",
    job_id: Optional[str] = None,
    expected_eta: float = ETA_PAGE_DEFAULT,
):
    """
    Funzione relativa alla pipeline di estrazione di entità a partire da contenuto testuale utilizzando servizi LM.

    Descrizione: Questa funzione contiene la pipeline relativa all'estrazione di entità da contenuto testuale.
    Come prima cosa, qualora il servizio richiamato (parametro 'service') sia "openai", il
    token fornito in input viene decrittato.
    Successivamente viene definito l'estrattore relativo al servizio desiderato, il quale viene impiegato
    per svolgere l'estrazione di entità dal testo, utilizzando gli altri eventuali parametri forniti
    in input alla funzione.
    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del json
    va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param json_entity: dizionario contenente le entità da ricercare nel contenuto testuale.
    :type json_entity: dict
    :param service: nome del servizio desiderato.
    :type service: str
    :param text_extracted: contenuto testuale su cui svolgere l'estrazione di entità.
    :type text_extracted: dict
    :param use_rag: Parametro booleano associato all'impiego di un embedder. Default a False.
    :type use_rag: (bool, optional)
    :param params: Dizionario contenente ulteriori parametri relativi al modello LM (e all'eventuale embedder).
    :type params: (EntityExtractionParams, optional)
    :param token: token cifrato contenente le informazioni necessarie per svolgere la chimata al modello LM.
    :type token: (dict, optional)
    :param use_case: codice identificativo univoco associato al progetto che richiama l'esecuzione della pipeline
        necessario per l'interazione con il layer-ai.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal['sync', 'async'], optional)
    :param language: lingua relative al contenuto del testo. Default a "it".
    :type language: (str, optional)
    :param path_prompt_template: Percorso al template da utilizzare per la costruzione del prompt. Default a None.
    :type path_prompt_template: (str, optional)
    :param job_id: codice identificativo univoco associato all'esecuzione della pipeline di estrazione dell'entità.
        Default a None.
    :type job_id: (str, optional)
    :param expected_eta: numero di secondi stimati per l'esecuzione dell'estrazione dell'entità. Default a 5 secondi.
    :type expected_eta: (float, optional)

    :return: La funzione restituisce il risultato dell'estrazione qualora essa vada a buon fine. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.
    """

    use_rag = use_rag if text_extracted else False

    if (
        not text_extracted
        or not isinstance(text_extracted, dict)
        or not text_extracted.get("texts")
    ):
        text_extracted = {"texts": dict()}

    extractor = dct_entity_extractor[service](token, use_case)

    func_kwargs = {
        "dct_entity": json_entity,
        "language": language,
        "text_extracted": text_extracted["texts"],
        "use_rag": use_rag,
        "params": params,
        "interaction_mode": interaction_mode,
    }

    return track_and_save_results(
        callable_func=extractor.extract_entity_from_text,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )


def extract_entity_from_pdf(
    pdf: bytes,
    service: str,
    json_entity: Optional[str] = None,
    language: Optional[str] = None,
    page_from: int = 1,
    page_to: int = None,
    text_extracted: Optional[dict] = None,
    use_rag: bool = False,
    params: Optional[EntityExtractionParams] = None,
    token: Optional[str] = None,
    use_case: Optional[str] = None,
    interaction_mode: Literal["async", "sync"] = "async",
    job_id: Optional[str] = None,
    expected_eta: float = ETA_PAGE_DEFAULT,
):
    """
    Funzione relativa alla pipeline di estrazione di entità a partire da un file pdf utilizzando servizi LM.

    Descrizione: Questa funzione contiene la pipeline relativa all'estrazione di testo da un file pdf.
    Come prima cosa, qualora il servizio richiamato (parametro 'service') sia "openai", il
    token fornito in input viene decrittato.
    Successivamente viene definito l'estrattore relativo al servizio desiderato, il quale viene impiegato
    per svolgere l'estrazione di entità dal file pdf, utilizzando gli altri eventuali parametri forniti
    in input alla funzione.
    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del json
    va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param pdf: file pdf su cui svolgere l'estrazione di entità.
    :type pdf: bytes
    :param json_entity: dizionario contenente le entità da ricercare nel file.
    :type json_entity: dict
    :param service: nome del servizio desiderato.
    :type service: str
    :param text_extracted: testo estratto relativo alle immagini fornite in input. Default a None.
    :type text_extracted: (dict, optional)
    :param use_rag: Parametro booleano associato all'impiego di un embedder. Default a False.
    :type use_rag: (bool, optional)
    :param params: Dizionario contenente ulteriori parametri relativi al modello LM (e all'eventuale embedder).
    :type params: (EntityExtractionParams, optional)
    :param token: token cifrato contenente le informazioni necessarie per svolgere la chimata al modello LM.
    :type token: (dict, optional)
    :param use_case: codice identificativo univoco associato al progetto che richiama l'esecuzione della pipeline
        necessario per l'interazione con il layer-ai.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal['sync', 'async'], optional)
    :param language: lingua relative al contenuto del file pdf. Default a "it".
    :type language: (str, optional)
    :param path_prompt_template: Percorso al template da utilizzare per la costruzione del prompt. Default a None.
    :type path_prompt_template: (str, optional)
    :param page_from: pagina relativa al file pdf da cui partire a svolgere l'estrazione dell'entità. Default a 1.
    :type page_from: (int, optional)
    :param page_to: pagina relativa al file pdf dove interrompere l'estrazione dell'entità. Default a None (estrazione
        prosegue fino alla fine del file).
    :type page_to: (int, optional)
    :param job_id: codice identificativo univoco associato all'esecuzione della pipeline di estrazione dell'entità.
        Default a None.
    :type job_id: (str, optional)
    :param expected_eta: numero di secondi stimati per l'esecuzione dell'estrazione dell'entità. Default a 5 secondi.
    :type expected_eta: (float, optional)

    :return: La funzione restituisce il risultato dell'estrazione qualora essa vada a buon fine. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.
    """

    # TODO: sopra il "default" è {"texts": dict()}, qui però si romperebbe per un controllo interno che
    #  TODO: prevede di non usare il testo se text_extracted["texts"] è None. Così così, ma al momento teniamo.

    if (
        not text_extracted
        or not isinstance(text_extracted, dict)
        or not text_extracted.get("texts")
    ):
        text_extracted = {"texts": None}

    use_rag = use_rag if text_extracted else False

    extractor = dct_entity_extractor[service](token, use_case)
        
    func_kwargs = {
        "pdf": pdf,
        "language": language,
        "dct_entity": json_entity,
        "page_from": page_from,
        "page_to": page_to,
        "text_extracted": text_extracted["texts"],
        "use_rag": use_rag,
        "params": params,
        "interaction_mode": interaction_mode,
    }

    return track_and_save_results(
        callable_func=extractor.extract_entity_from_pdf,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )
