"""Modulo contenente la classe astratta per i PromptBuilder"""

from typing import Union, Optional
from abc import ABC, abstractmethod
from bdlpkg.utils.bdlfile.services.bdlfile import get_obj_from_config_path
from config.parameters import PromptDefaultConfig, LegacyDefaultConfig,  LEGACY_USE_CASES
from core.data.entities import is_valid_messages
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInputError


class AbstractPromptBuilder(ABC):
    """
    Classe astratta relativa alla definizione dei prompt per i modelli LM.
    """
    # Questi è indifferente mettere PromptDefaultConfig o Legacy perchè si sovrappongono
    language: str = PromptDefaultConfig.language
    response_format: str = PromptDefaultConfig.response_format
    path_template: str = PromptDefaultConfig.path_template

    def __init__(
        self,
        language: Optional[str] = None,
        dct_entity: Optional[str] = None,
        prompt_params: Optional[dict] = None,
        use_case: Optional[str] = None
    ) -> None:
        """
        Metodo di inizializzazione dell'oggetto prompt. Nello specifico, il metodo configura il template da utilizzare
        per la costruzione dei prompt ai modelli LM, se specificato in input.

        """
        if language in ("en", "it"):
            self.language = language

        if not dct_entity and not prompt_params.get("input"):
            raise SmartOCRInputError(f"Method {self.__class__.__name__}.{get_function_name()}: "
                                     f"Entity Extraction must have a valid entity dict or an input in prompt params")

        if dct_entity and any(
            key in prompt_params
            for key in ["input", "system_message_vlm", "system_message_llm"]
        ):
            raise SmartOCRInputError(f"Method {self.__class__.__name__}.{get_function_name()}: "
                                     f"Entity Extraction must have either a valid entity dict or an input "
                                     f"in prompt params, but both are passed.")

        # TODO: ocr_instruction possono sovrascriverlo se usano prompt standard?
        self.dict_entity = dct_entity
        self.use_case = use_case
        self.messages = self._configure_prompt_params(prompt_params)
        self.prompt_template = self._configure(self.path_template)
        self.current_messages = None
        self.system_message_llm = None
        self.system_message_vlm = None
        self.ocr_instructions = None
        self.page_instructions = None
        self.user_input = None

    def update_messages(self, language):
        """
        Aggiorna i messaggi correnti in base alla lingua.
        Se la lingua non è supportata, usa quella di default.
        """
        prompt_class = LegacyDefaultConfig if self.use_case in LEGACY_USE_CASES else PromptDefaultConfig
        self.current_messages = prompt_class.prompt_standard.get(
            language, prompt_class.prompt_standard["en"]
        )

        # Aggiorna i messaggi della classe
        self.system_message_vlm = self.current_messages["system_message_vlm"]
        self.system_message_llm = self.current_messages["system_message_llm"]
        self.ocr_instructions = self.current_messages["ocr_instructions"]
        self.page_instructions = self.current_messages["page_instructions"]
        self.user_input = self.current_messages["input"].format(
            dct_entity=self.dict_entity
        )

    def _configure_prompt_params(self, messages: dict) -> dict:
        """
        Metodo privato che configura i parametri per la creazione del prompt o
        utilizza i valori di default.

        :param messages: Dizionario contenente i messaggi per il prompt.
        :type messages: dict

        :return: Dizionario contenente i messaggi configurati per la creazione del prompt e per la formattazione della risposta dell'LLM.
        :rtype: dict
        """

        self.update_messages(self.language)

        dct_prompt_config = {
            "language": self.language,
            "system_message_vlm": self.system_message_vlm,
            "system_message_llm": self.system_message_llm,
            "ocr_instructions": self.ocr_instructions,
            "page_instructions": self.page_instructions,
            "input": self.user_input,
            "response_format": self.response_format,
        }

        if is_valid_messages(messages):
            dct_prompt_config = self._extract_ee_messages(messages)

        return dct_prompt_config

    def _extract_ee_messages(self, messages: dict) -> dict:
        """
        Metodo privato che estrae e valida i prompt di configurazione specificati dall'utente, in base al prompt template scelto.

        :param messages: Dizionario contenente i prompt messages e formato risposta LLM
        :type messages: dict

        :return: Dizionario contenente le info per il prompt configurate.
        :rtype: dict
        """

        system_message_vlm = messages.get("system_message_vlm", self.system_message_vlm)
        system_message_llm = messages.get("system_message_llm", self.system_message_llm)
        ocr_instructions = messages.get("ocr_instructions", self.ocr_instructions)
        page_instructions = messages.get("page_instructions", self.page_instructions)
        user_input = messages.get("input", self.user_input)
        response_format = messages.get("response_format", self.response_format)

        if not isinstance(system_message_vlm, str):
            system_message_vlm = self.system_message_vlm

        if not isinstance(system_message_llm, str):
            system_message_llm = self.system_message_llm

        if not isinstance(ocr_instructions, str):
            ocr_instructions = self.ocr_instructions

        if not isinstance(page_instructions, str):
            page_instructions = self.page_instructions

        if not isinstance(user_input, str):
            user_input = self.user_input

        if (
            not isinstance(response_format, (str, dict)) or self.dict_entity
        ):
            response_format = self.response_format

        return {
            "language": self.language,
            "system_message_vlm": system_message_vlm,
            "system_message_llm": system_message_llm,
            "ocr_instructions": ocr_instructions,
            "page_instructions": page_instructions,
            "input": user_input,
            "response_format": response_format,
        }

    @staticmethod
    def _configure(path_template: Optional[str] = None) -> Union[dict, str, None]:
        """
        Metodo privato che recupera il file contenente il template per la creazione dei prompt, se specificato in
        input alla funzione.

        :param path_template: percorso al file template per la creazione dei prompt ai modelli LM. Default a None.
        :type path_template: (str, optional)

        :return: La funzione restituisce il template come dizionario. Se il path al template non è specificato in input
            alla fuznione, viene restituito None.
        :rtype: (dict, None)
        """
        return get_obj_from_config_path(path_template) if path_template else None

    @abstractmethod
    def build_prompt_vlm(self, *args, **kwargs) -> Union[dict, str]:
        """
        Metodo astratto per la creazione di prompt per modelli VLM.
        """
        pass

    def build_prompt_llm(self, *args, **kwargs) -> Union[dict, str]:
        """
        Metodo per la creazione di prompt per modelli LLM.
        """
        pass
