"""Modulo contenente funzioni ausiliarie generiche su dati di input"""

import re
import json
from langchain_core.output_parsers import JsonOutputParser
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInvalidOutputException


def is_valid_params(params: dict) -> bool:
    """
    Funzione per la validazione del parametro params.

    :param params: parametro da validare
    :type params: dict

    :return: True se la validazione va a buon fine, altrimenti False.
    :rtype: bool
    """
    if not params or not isinstance(params, dict) or "args" not in params.keys():
        return False

    return True


def is_valid_messages(messages: dict) -> bool:
    """
    Funzione per la validazione dei prompt messages.

    :param messages: parametro da validare
    :type params: dict

    :return: True se la validazione va a buon fine, altrimenti False.
    :rtype: bool
    """
    if not messages or not isinstance(messages, dict):
        return False

    return True


def fix_json_errors(input_string):
    """
    Funzione che rende conforme la stringa in input al formato json.
    Nello specifico, viene svolto un controllo sulle parentesi '{}' e sulle virgolette.

    :param input_string: testo in input
    :type input_string: str

    :return: input reso conforme al formato json. Se non è stato possibile correggere gli errori viene restituito un
        dizionario vuoto.
    :rtype: Any

    """
    # Trova il primo '{' e il corrispondente '}'
    start = input_string.find("{")
    if start == -1:
        return dict()

    # Troviamo la chiusura corrispondente
    open_braces = 0
    for i, char in enumerate(input_string[start:]):
        if char == "{":
            open_braces += 1
        elif char == "}":
            open_braces -= 1
            if open_braces == 0:
                end = start + i
                break
    else:
        return dict()

    # Estrai la parte che sembra essere JSON
    json_string = input_string[start : end + 1]

    # Verifica se il JSON è già valido
    try:
        json_object = json.loads(json_string)
        return json_object  # Restituisce il JSON formattato correttamente
    except json.JSONDecodeError:
        # Se non è valido, procede con i tentativi di correzione
        pass

    # Corregge le virgolette per le chiavi
    json_string = re.sub(r'(?<=\{|\,)\s*"?(\w+)"?\s*:', r'"\1":', json_string)

    # Corregge le virgolette per i valori stringa
    json_string = re.sub(
        r': "?([^",\{\}\[\]]+)"?', lambda m: f': "{m.group(1)}"', json_string
    )

    # Rimuove le virgole in eccesso
    json_string = re.sub(r",\s*}", "}", json_string)
    json_string = re.sub(r",\s*\]", "]", json_string)

    # Prova a parsare il JSON
    try:
        json_object = json.loads(json_string)
        return json_object  # Restituisce il JSON formattato correttamente
    except json.JSONDecodeError:
        raise SmartOCRInvalidOutputException(f"Func {get_function_name()}: the LLM returned an output with an incorrect"
                                             f"format.")


def parse_json_content(content: str):

    try:
        if "```json" in content:
            json_content = JsonOutputParser().invoke(content)
        else:
            json_content = json.loads(content)

    except:  # noqa
        json_content = fix_json_errors(content)

    return json_content
