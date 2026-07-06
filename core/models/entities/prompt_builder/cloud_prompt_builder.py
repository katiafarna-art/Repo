"""Modulo contenente la classe concreta per il PromptBuilder relativo a strumenti Cloud (Azure, Google)"""
import logging
import tiktoken
import re
import math
from io import BytesIO
import base64
from PIL import Image
from typing import Optional, List

from core.models.entities.prompt_builder.abstract_prompt_builder import (
    AbstractPromptBuilder,
)
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInputError, SmartOCRException
from config.input_models.supported_models import supported_models


class CloudPromptBuilder(AbstractPromptBuilder):
    """
    Classe per la creazione di prompt relativi ai servizi OpenAI per l'estrazione di entitò.
    """

    @staticmethod
    def _num_tokens_from_string(string: str, encoding_name: str = "cl100k_base", model: str = 'gpt-4o') -> int:
        """
        Metodo privato che restituisce il numero di token presenti in una stringa di testo.

        :param string: stringa di testo.
        :type string: str
        :param encoding_name: nome associato alla tipologia di encoding da considerare. Default a 'cl100k_base'.
        :type encoding_name: (str, optional)

        :return: restituisce il numero di token presenti nella stringa di testo.
        :rtype: int
        """
        # Get actual models supported by SmartOCR
        models = supported_models.keys()

        # Check if model is supported among openai ones
        # At the moment the only supported series is "gpt".

        if model in list(filter(lambda x: "gpt" in x, models)): 
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(string))
            return num_tokens

        # Check if model is supported among google ones.
        # At the moment the only supported series is "gemini".
        elif model in list(filter(lambda x: "gemini" in x, models)):
            string = re.sub(r'\s+', ' ', string)
            # Conta il numero di parole
            words = len(string.split())
            
            # Conta simboli speciali, numeri e punteggiatura
            special_chars = len(re.findall(r'[^\w\s]', string))
            numbers = len(re.findall(r'\d+', string))
            
            # Formula approssimativa per Gemini
            # Gemini usa SentencePiece, quindi una parola è tipicamente ~1.3 token
            estimated_tokens = math.ceil(words * 1.3 + special_chars * 0.5 + numbers * 0.5)
            
            return estimated_tokens
        else:
            # Modello non supportato
            raise SmartOCRInputError(
                f"Method CloudPromptBuilder.{get_function_name()}:"
                f"Invalid model {model}. Supported models are: {str(supported_models.keys())}."
            )

    @staticmethod
    def _get_image_dims(image_uri: str):
        """
        Metodo privato che restituisce le dimensioni dell'immagine fornita in input.
        La gestione dell'immagine è svolta seguendo quanto riportato in:
        https://github.com/openai/openai-cookbook/pull/881/files

        :param image_uri: URI relativo all'immagine.
        :type image_uri: str

        :return: dimensioni dell'immagine.
        :rtype: tuple[int, int]

        :raises ValueError: Se l'immagine fornita in input non è in formato base64.
        """
        if re.match(r"data:image\/\w+;base64", image_uri):  # noqa
            image_uri = re.sub(r"data:image\/\w+;base64,", "", image_uri)  # noqa
            image = Image.open(BytesIO(base64.b64decode(image_uri)))
            return image.size
        else:
            raise SmartOCRException(
                f"Method CloudPromptBuilder.{get_function_name()}:"
                f"Image must be a base64 string."
            )

    #TODO CAMBIARE PER GPT-4O-MINI e per GEMINI
    def _num_tokens_from_image(self, image_uri: str, model: str = "gpt-4o") -> int:
        """
        Metodo privato che restituisce il numero di token associati all'immagine fornita in input.
        L'immagine viene prima resa conforme al formato appropriato in base al modello,
        poi viene suddivisa in quadrati (tile). Viene poi utilizzato un costo fisso per ogni quadrato per
        calcolare il numero di token, seguendo la documentazione ufficiale.

        :param image_uri: URI relativo all'immagine.
        :type image_uri: str
        :param model: modello da utilizzare per il conteggio dei token. Default a "gpt-4o".
                    Possibili valori ('gpt-4o', 'gpt-4o-mini', 'gemini-1.5-pro').
        :type model: (str, optional)

        :return: Numero di token associati all'immagine.
        :type: int

        :raises ValueError: Se viene specificato un modello non supportato.
        """

        models = supported_models.keys()
        
        # Costo per tile per Gemini
        GEMINI_COST_PER_TILE = 258

        # Ottieni le dimensioni dell'immagine
        width, height = self._get_image_dims(image_uri)
        
        if model in list(filter(lambda x: "gpt" in x, models)):
            # Gestione per modelli GPT-4.1, GPT-4o e GPT-4o-mini (stessa logica di ridimensionamento)
            
            # Check if resizing is needed to fit within a 2048 x 2048 square
            if max(width, height) > 2048:
                # Resize dimensions to fit within a 2048 x 2048 square
                ratio = 2048 / max(width, height)
                width = int(width * ratio)
                height = int(height * ratio)
                
            # Further scale down to 768px on the shortest side
            if min(width, height) > 768:
                ratio = 768 / min(width, height)
                width = int(width * ratio)
                height = int(height * ratio)
                
            # Calculate the number of 512px squares
            num_squares = math.ceil(width / 512) * math.ceil(height / 512)
            
            return self._compute_tokens_from_img_gpt(model, num_squares)
        
        elif model in list(filter(lambda x: "gemini" in x, models)):
                       
            # Se entrambe le dimensioni sono <= 384, usa un singolo tile
            if width <= 384 and height <= 384:
                return GEMINI_COST_PER_TILE
            
            # Calcola la dimensione del tile in base alla dimensione più piccola
            tile_size = min(width, height) / 1.5
            
            # Assicurati che il tile non sia più piccolo di 256 e non più grande di 768
            tile_size = max(256, min(768, tile_size))
            
            # Calcola il numero di tile necessari per coprire l'immagine
            num_tiles_width = math.ceil(width / tile_size)
            num_tiles_height = math.ceil(height / tile_size)
            total_tiles = num_tiles_width * num_tiles_height
            
            # Ogni tile usa 258 token
            return total_tiles * GEMINI_COST_PER_TILE
        
        else:
            # Modello non supportato
            raise SmartOCRInputError(
                f"Method CloudPromptBuilder.{get_function_name()}:"
                f"Invalid model. Supported models are: {str(supported_models.keys())}."
            )
    
    @staticmethod
    def _compute_tokens_from_img_gpt(model: str, num_squares: int):
        """
        Compute the number of tokens for each image. \
        
        References: 
        * https://learn.microsoft.com/en-us/azure/ai-foundry/openai/overview
        * https://platform.openai.com/docs/guides/images-vision#gpt-4o-gpt-4-1-gpt-4o-mini-cua-and-o-series-except-o4-mini

        Args:
            :param model: the model id
            :param num_squares: the number of tiles of each image

        Return:
            the number of tokens

        """
        tokens_per_tile = supported_models[model].get("img_tokens_per_tile")
        base_tokens = supported_models[model].get("img_base_tokens")
        # Calcola il costo totale in base al modello

        if model.startswith("gpt-4.1-nano"):
            raise SmartOCRException(
                "GPT-4.1 nano is not supported at the moment for entity extraction from images."
            )
        return num_squares * tokens_per_tile + base_tokens

    @staticmethod
    def _add_single_prompt(role: str, type_prompt: str, content: str):
        """
        Metodo privato che costruisce e restituisce un prompt.

        :param role: variabile 'role' associata al prompt.
        :type role: str
        :param type_prompt: tipo nativo associato.
        :type type_prompt: str
        :param content: contenuto del prompt.
        :type content: str

        :return: dizionario associato alla defizione del singolo prompt.
        :rtype: dict
        """
        dct_single_prompt = {
            "role": role,
            "content": [{"type": type_prompt, type_prompt: content}],
        }

        return dct_single_prompt

    @staticmethod
    def _postprocess_prompt(prompt_draft: dict) -> dict:
        """
        Metodo privato che svolge la post-elaborazione del prompt.
        Partendo da prompt grezzi, questi vengono riorganizzato a seconda del 'role' ('user' o 'system')
        ad essi associato.
        I prompt post-elaborati sono poi restituiti in un dizionario.

        :param prompt_draft: dizionario contenente i prompt grezzi da post-elaborare.
        :type prompt_draft: dict

        :return: dizionario contenente i prompt post-elaborati.
        :rtype: dict
        """
        # TODO: vale la pena usare gli attributi messages_sys e messages_user.
        system_prompts = [
            msg for msg in prompt_draft["messages"] if msg["role"] != "user"
        ]
        user_prompts = [
            msg for msg in prompt_draft["messages"] if msg["role"] == "user"
        ]

        consolidated_content = [msg["content"][0] for msg in user_prompts]
        user_prompt = {"role": "user", "content": consolidated_content}

        return {"messages": system_prompts + [user_prompt]}

    def build_prompt_llm(self, text_extracted: List[str], page_mapping: dict):
        """
        Metodo che costruisce i prompt per modelli LLM del servizio OpenAI.
        Utilizzando quanto specificato nel file template per la costruzione dei prompt, vengono definiti
        i prompt singoli per 'system' e 'user'. Tali prompt sono raccolti in una lista restituita in output dalla
        funzione. I prompt relativi alle diverse pagine associate al testo estratto (fornito in input), sono
        similmente raccolti in una diversa lista, sempre restituita in output.

        :param text_extracted: testo estratto tramite OCR da una lista di immagini o da un file PDF.
        :type text_extracted: list
        :param page_mapping: Mappatura associata alle diverse pagine il cui contenuto testuale è in 'text_extracted'.
        :type page_mapping: dict

        :return: tupla conenente la lista dei prompt 'system', 'user' e la lista dei prompt associati al testo.
        :rtype: tuple[list, list]
        """
        necessary_prompts = []
        list_prompts = []

        system_text = self.prompt_template["llm_entity_prompt"]["system"]["content"][
            self.messages["language"]
        ]["text"].format(system_message=self.messages["system_message_llm"])

        necessary_prompts.append(
            {"role": "system", "name": "system", "content": system_text}
        )

        # User prompt with entity (necessary)
        user_text = self.prompt_template["llm_entity_prompt"]["user"]["content"][
            self.messages["language"]
        ]["text"].format(input=self.messages["input"])
        necessary_prompts.append(self._add_single_prompt("user", "text", user_text))

        if text_extracted:
            for i, text in enumerate(text_extracted):
                ocr_base_text = f"pag_{page_mapping[i + 1]}:" + self.prompt_template[
                    "llm_entity_prompt"
                ]["user"]["content"][self.messages["language"]]["text_ocr"].format(
                    context=text
                )
                list_prompts.append(
                    self._add_single_prompt("user", "text", ocr_base_text)
                )

        return necessary_prompts, list_prompts

    def build_prompt_vlm(
        self,
        img_b64: Optional[bytes] = None,
        text_extracted: Optional[List] = None,
        page_mapping: Optional[dict] = None,
    ):
        """
        Metodo che costruisce i prompt per modelli VLM del servizio OpenAI.
        Utilizzando quanto specificato nel file template per la costruzione dei prompt, vengono definiti
        i prompt singoli per 'system' e 'user'. Tali prompt sono raccolti in una lista assieme ai prompt associati
        al testo fornito (opzionalmente) in input. La lista è poi restituita in output dalla funzione.
        I prompt relativi alle immagini fornite in input, sono similmente raccolti in una diversa lista, sempre
        restituita in output.

        :param img_b64: immagine in input
        :type img_b64: bytes
        :param text_extracted: testo estratto tramite OCR da una lista di immagini o da un file PDF. Default a None.
        :type text_extracted: (list, optional)
        :param page_mapping: Mappatura associata alle diverse pagine il cui contenuto testuale è in 'text_extracted'.
            Default a None.
        :type page_mapping: (dict, optional)

        :return: tupla conenente la lista dei prompt 'system', 'user' e la lista dei prompt associati alle immagini.
        :rtype: tuple[list, list]
        """
        list_prompts = []
        necessary_prompts = []
        ocr_system_text = ""
        ocr_system_pages = ""

        # System prompt
        system_text = self.prompt_template["vlm_entity_prompt"]["system"]["content"][
            self.messages["language"]
        ]["text"].format(system_message=self.messages["system_message_vlm"])

        if text_extracted:
            ocr_system_text = self.prompt_template["vlm_entity_prompt"]["system"][
                "content"
            ][self.messages["language"]]["ocr"].format(
                ocr_instructions=self.messages["ocr_instructions"]
            )

        if page_mapping and not text_extracted:
            ocr_system_pages = self.prompt_template["vlm_entity_prompt"]["system"][
                "content"
            ][self.messages["language"]]["ocr"].format(
                ocr_instructions=self.messages["page_instructions"]
            )

        necessary_prompts.append(
            {
                "role": "system",
                "name": "system",
                "content": system_text + "\n" + ocr_system_text + "\n" + ocr_system_pages,
            }
        )

        # User prompt with entity
        user_text = self.prompt_template["vlm_entity_prompt"]["user"]["content"][
            self.messages["language"]
        ]["text"].format(input=self.messages["input"])

        necessary_prompts.append(self._add_single_prompt("user", "text", user_text))

        # Process images and texts
        for i, img in enumerate(img_b64):

            image_content = f"data:image/png;base64,{img}"
            dct_image_content = self._add_single_prompt(
                "user", "image_url", image_content
            )
            dct_image_content["content"][0].update(**{"image_url_detail": "high"})
            list_prompts.append(dct_image_content)

            if page_mapping and not text_extracted:
                ocr_user_pages = f"pag_{page_mapping[i + 1]}"

                list_prompts.append(
                    self._add_single_prompt("user", "text", ocr_user_pages)
                )

            if text_extracted and i < len(text_extracted):
                ocr_user_text = f"pag_{page_mapping[i + 1]}:" + self.prompt_template[
                    "vlm_entity_prompt"
                ]["user"]["content"][self.messages["language"]]["text_ocr"].format(
                    context=text_extracted[i]
                )

                list_prompts.append(
                    self._add_single_prompt("user", "text", ocr_user_text)
                )

        return necessary_prompts, list_prompts

    def create_payloads(
        self, necessary_prompts, prompts, page_mapping=None, max_tokens_per_call=1000, model='gpt-4o'
    ):
        """
        Metodo che crea il payload per le chiamate API, gestendo sia input VLM (immagini + testo) che LLM (solo testo).
        Mantiene una numerazione progressiva delle pagine tra i payload.

        :param necessary_prompts: Lista di prompt necessari da includere in ogni payload
        :type necessary_prompts: list
        :param prompts: Lista di prompt aggiuntivi (immagini e/o testo)
        :type prompts: list
        :param page_mapping: Mappatura associata alle diverse pagine nel contenuto testuale. Default a None.
        :type page_mapping: (dict, optional)
        :param max_tokens_per_call: Numero massimo di token consentiti per chiamata. Default a 1000.
        :type max_tokens_per_call: (int, optional)

        :return: Lista di payload, ciascuno contenente messaggi e numeri di pagina.
        :rtype: list

        :raises ValueError: Se il numero di token necessari è superiore al numero massimo ti token ammesso.
        :raises ValueError: Se il tipo di prompt non è tra quelli supportati ('text', 'image_url').
        :raises ValueError: Se non è stato possibile aggiungere i prompt addizionali (non "necessary_prmpts")
            al payload.
        """
        payloads = []

        necessary_token_count = 0
        for prompt in necessary_prompts:
            if isinstance(prompt["content"], str):
                necessary_token_count += self._num_tokens_from_string(prompt["content"], model=model)
            elif (
                isinstance(prompt["content"], list)
                and prompt["content"][0]["type"] == "text"
            ):
                necessary_token_count += self._num_tokens_from_string(
                    prompt["content"][0]["text"], model=model
                )
            else:
                pass

        if necessary_token_count >= max_tokens_per_call:
            raise ValueError(
                "necessary_prompts exceed max_tokens_per_call"
            )  # todo error

        current_payload = necessary_prompts.copy()
        current_token_count = necessary_token_count
        current_pages = []
        total_pages_processed = 0  # Contatore per tutte le pagine processate

        i = 0
        while i < len(prompts):
            current_prompt = prompts[i]
            prompt_type = current_prompt["content"][0]["type"]

            if prompt_type == "image_url":
                image_prompt = current_prompt
                text_prompt = (
                    prompts[i + 1]
                    if i + 1 < len(prompts)
                    and prompts[i + 1]["content"][0]["type"] == "text"
                    else None
                )

                image_tokens = self._num_tokens_from_image(
                    image_prompt["content"][0]["image_url"], model
                )
                text_tokens = (
                    self._num_tokens_from_string(text_prompt["content"][0]["text"], model=model)
                    if text_prompt
                    else 0
                )
                page_tokens = image_tokens + text_tokens

                if current_token_count + page_tokens > max_tokens_per_call:
                    if len(current_payload) > len(necessary_prompts):
                        payloads.append(
                            {
                                "messages": self._postprocess_prompt(
                                    {"messages": current_payload}
                                ),
                                "pages": (
                                    list(
                                        map(
                                            lambda page: page_mapping[page],
                                            current_pages,
                                        )
                                    )
                                    if page_mapping
                                    else current_pages
                                ),
                            }
                        )
                    current_payload = necessary_prompts.copy()
                    current_token_count = necessary_token_count
                    current_pages = []

                current_payload.append(image_prompt)
                if text_prompt:
                    current_payload.append(text_prompt)

                total_pages_processed += 1
                current_pages.append(total_pages_processed)
                current_token_count += page_tokens

                i += 2 if text_prompt else 1

            elif prompt_type == "text":
                text_prompt = current_prompt
                text_tokens = self._num_tokens_from_string(
                    text_prompt["content"][0]["text"], model=model
                )

                if current_token_count + text_tokens > max_tokens_per_call:
                    if len(current_payload) > len(necessary_prompts):
                        payloads.append(
                            {
                                "messages": self._postprocess_prompt(
                                    {"messages": current_payload}
                                ),
                                "pages": (
                                    list(
                                        map(
                                            lambda page: page_mapping[page],
                                            current_pages,
                                        )
                                    )
                                    if page_mapping
                                    else current_pages
                                ),
                            }
                        )
                    current_payload = necessary_prompts.copy()
                    current_token_count = necessary_token_count
                    current_pages = []

                current_payload.append(text_prompt)
                total_pages_processed += 1
                current_pages.append(total_pages_processed)
                current_token_count += text_tokens

                i += 1

            else:
                raise SmartOCRInputError(
                    f"Method {self.__class__.__name__}.{get_function_name()}:"
                    f"Unsupported prompt type: {prompt_type}"
                )
        logging.info(f"Lenght of current payload: {len(current_payload)}")
        if len(current_payload) > len(necessary_prompts):
            payloads.append(
                {
                    "messages": self._postprocess_prompt({"messages": current_payload}),
                    "pages": (
                        list(map(lambda page: page_mapping[page], current_pages))
                        if page_mapping
                        else current_pages
                    ),
                }
            )

        if not payloads:
            raise SmartOCRException(
                f"Method {self.__class__.__name__}.{get_function_name()}:"
                f"Could not create any payload with additional prompts"
            )

        return payloads
