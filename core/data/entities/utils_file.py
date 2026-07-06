"""Modulo contenente funzioni ausiliarie per agire su file."""

import base64


def from_bytes_to_b64(img: bytes) -> str:
    """
    Funzione che converte un'immagine da bytes a una stringa in formato base64.

    :param img: immagine in bytes
    :type img: bytes

    :return: immagine in formato stringa base64
    :rtype: str
    """
    base64_bytes = base64.b64encode(img)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string
