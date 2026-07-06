"""Modulo contenente funzioni per il calcolo del time laps di retrieve (eta)"""

import io
import logging
from typing import AnyStr, Union, Optional
import pypdf
from config.parameters import ETA_PAGE_DEFAULT, ETA_PAGE_LAI


def get_pdf_len(pdf_file: AnyStr) -> int:
    """
    Funzione che restituisce il numero di pagine presenti in un file PDF utilizzando la libreria pypdf.

    :param pdf_file: file PDF.
    :type pdf_file: AnyStr

    :return: numero di pagine presenti nel file. Se il calcolo delle pagine non va a buon fine viene restituito 0.
    :rtype: int
    """
    pdf_len = 1

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_file))
        pdf_len = len(reader.pages)

    # TODO: sta funzione è sbagliata; ritorna 0 anche in caso di pdf corrotti o errori minando il retrieve
    except Exception as e:
        logging.warning(
            f"Error in retrieving the number of pages from the pdf file correctly {e}: returning 1."
        )

    finally:
        return pdf_len


def eta_estimator(pdf_file: AnyStr) -> Union[int, float]:
    """
    Funzione che restituisce un ETA basato sul numerous di pagine di un file pdf.

    :param pdf_file: file PDF.
    :type pdf_file: AnyStr

    :return: ETA stimato sul numero di pagine del file PDF oppure ETA di default (5) se il calcolo delle pagine non è
        andato a buon fine.
    :rtype: (int, float)
    """
    eta = 5

    if get_pdf_len(pdf_file):
        eta = get_pdf_len(pdf_file) * ETA_PAGE_DEFAULT

    return eta


def eta_estimator_from_text(
    text_in: dict
) -> Union[int, float]:
    """
    Funzione che restituisce un ETA basato sul numero di pagine associate a del contenuto
    testuale.

    :param text_in: contenuto testuale.
    :type text_in: dict

    :return: ETA stimato
    :rtype: (int, float)
    """
    num_pages = len(text_in["texts"].keys())

    eta = num_pages * ETA_PAGE_LAI

    return eta
