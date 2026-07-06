"""Routine per l'esecuzione di una pipeline e la gestione dei file di output ad essa connessi."""

import os
import logging
import time
from typing import Callable, Optional, Union
from core.data.entities import save_result, check_file
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRLayeraiException


def track_and_save_results(
    callable_func: Callable,
    func_args: Optional[tuple] = None,
    func_kwargs: Optional[dict] = None,
    job_id: Optional[str] = None,
    expected_eta: Optional[Union[float, int]] = None,
) -> dict:
    """
    La funzione prende un oggetto Callable e lo esegue con i rispettivi argomenti posizionali e keywords (se presenti):
    l'output restituito sarà quello generato dalla pipeline stessa o - in caso d'errore - un dizionario che ne riporti
    le caratteristiche.

    La funzione si occupa anche - nei casi in cui il parametro 'job_id' sia specificato - del salvataggio in formato
    json dell'output stesso e degli artefatti correlati all'esecuzione della pipeline, ovvero i file sentinella
    'success' o 'failure'.

    :param callable_func: Pipeline di cui si vuole ottenere e salvare output e artefatti correlati.
    :type callable_func: Callable
    :param func_args: Tupla degli argomenti posizionali da passare a 'callable_func'
    :type func_args: Optional[tuple]. Default a None.
    :param func_kwargs: Dizionario degli argomenti keywords da passare a 'callable_func'.
    :type func_kwargs: Optional[dict]. Default a None.
    :param job_id: Stringa identificativa del processo associato all'esecuzione asincrona della pipeline.
    :type job_id: Optional[str]. Default a None.
    :param expected_eta: Stima del tempo (espresso in secondi) necessario all'esecuzione della pipeline.
    :return: Optional[Union[float, int]]. Default a None.
    """

    func_args = func_args or ()
    func_kwargs = func_kwargs or {}

    if job_id:
        os.environ["TMP_JOB_ID"] = job_id

    try:
        start_time = time.time()

        output = callable_func(*func_args, **func_kwargs)

        if job_id:
            elapsed_time = time.time() - start_time
            logging.info(
                f"JOB-ID: {job_id} - Num. seconds: {elapsed_time} vs expected_eta: {expected_eta}"
            )

            save_result(job_id=job_id, output=output, extension="json")

            if check_file(job_id=job_id, extension="json"):
                save_result(job_id=job_id, output="", extension="success")

            else:
                logging.error("No result output.json saved")
                save_result(
                    job_id=job_id,
                    output="No result output.json saved",
                    extension="failure",
                )

    except Exception as e:
        logging.error(f"{e}")
        output = {"message": f"Exception {e} occurred in {get_function_name()}"}

        if isinstance(e, SmartOCRLayeraiException):
            output["layer_status_code"] = e.status_code

        if job_id:
            save_result(job_id=job_id, output=output, extension="failure")

        raise

    return output
