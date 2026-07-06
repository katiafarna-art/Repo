"""Modulo contenente la classe astratta per i Language Models offerti dal servizio"""

import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict

from config.input_models.entity_extraction import EntityExtractionParams
from config.parameters import RetryDefaultConfig, LEGACY_USE_CASES
from core.data.entities import parse_json_content
from core.data.entities.embedder import dct_embedder_factory
from core.routines.entities import session, get_function_name
from core.routines.services import LAIUtilitiesManager
from core.exceptions import SmartOCRLayeraiException, SmartOCRException


class AbstractLM(ABC):
    """
    Classe astratta utilizzata come framework per la definizione dei diversi estrattori di entità basati sui diversi
    servizi disponibili.
    """

    def __init__(self, provider: str, service: str, params: EntityExtractionParams) -> None:
        """
        Metodo di inizializzazione di un oggetto AbstractLM. Nello specifico, vengono inizializzati gli attributi
        relativi al servizio da utilizzare per l'estrazione di entità ('provider' e 'service').
        """
        self.provider = provider
        self.service = service
        self.config_class = params

    @staticmethod
    def _extract_tokens(item, is_google_signature):
        """Extracts token count based on the response structure."""
        return (
            item["generation_info"]["total_tokens"]
            if not is_google_signature
            else item["generation_info"]["usage_metadata"]["total_token_count"]
        )

    @staticmethod
    def _parse_response_content(item, is_google_signature):
        """Extracts and parses response content based on format."""
        std_content = item["generation_info"]["choices"][0]["content"]
        real_content = std_content if not is_google_signature else std_content["parts"][0]["text"]
        return real_content

    @staticmethod
    def _process_json_content(real_content, template, use_case: str = None):
        """Processes parsed JSON content based on template type."""
        parsed_content = parse_json_content(real_content)

        if isinstance(parsed_content, list):  # Fix bug where content is a list of JSONs
            parsed_content = parsed_content[0]

        if (template == "base") and (use_case in LEGACY_USE_CASES):
            message_content = defaultdict(lambda: defaultdict(dict))
            for key, content in parsed_content.items():
                if isinstance(content, dict):
                    page = content.get("page") or content.get("pag") or "NA"
                    value = content.get("value", "NA")
                    if page != "NA" and value != "NA":
                        message_content[f"pag_{page}"][key] = value
            return message_content

        return parsed_content  # "custom" template case

    def _postprocess_chunk_layerai(
        self,
        response_list: list,
        response_format: str = "json_object",
        template: str = "base",
        is_google_signature: bool = False,
        use_case: str = None
    ) -> dict:

        final_dict = {
            "choices": [],
            "model": self.config_class.model_id,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }

        total_tokens = 0
        json_formats = ("json_object", "application/json") if is_google_signature else ("json_object",)

        for item in response_list:

            total_tokens += self._extract_tokens(item, is_google_signature)
            real_content = self._parse_response_content(item, is_google_signature)

            if response_format in json_formats:
                final_message_content = self._process_json_content(real_content, template, use_case)
                final_dict["choices"].append({"message": {"content": dict(final_message_content)}})

            else:
                final_dict["choices"].append({"message": {"content": real_content}})

            final_dict["usage"]["total_tokens"] = total_tokens

        return final_dict

    def _get_vlm_payloads(
        self, img, pages: list, text_extracted: dict, use_rag: bool, prompt, emb_params: dict
    ):

        token, use_case, int_mode = (
            emb_params.get("token"),
            emb_params.get("use_case"),
            emb_params.get("int_mode"),
        )

        if text_extracted and use_rag:

            embedder = dct_embedder_factory.get(f"{self.config_class.embedder_id}")
            images_mapped = {key: img[i] for i, key in enumerate(text_extracted.keys())}
            embedder_routine = embedder(
                token=token, use_case=use_case, interaction_mode=int_mode
            )

            text_extracted, img, page_mapping = embedder_routine.start_rag(
                text_extracted=text_extracted,
                images_mapped=images_mapped,
                dict_entity=prompt.dict_entity,
            )

        elif text_extracted and not use_rag:

            page_mapping = {
                i: int(key.split("_")[1])
                for i, key in enumerate(text_extracted.keys(), start=1)
            }
            text_extracted = [value for _, value in text_extracted.items()]
        elif pages:
            page_mapping = {i: value for i, value in enumerate(pages, start=1)}
        else:
            page_mapping = None

        necessary_prompts, text_img_prompts = prompt.build_prompt_vlm(
            img_b64=img, text_extracted=text_extracted, page_mapping=page_mapping
        )

        return prompt.create_payloads(
            necessary_prompts=necessary_prompts,
            prompts=text_img_prompts,
            page_mapping=page_mapping,
            max_tokens_per_call=self.config_class.model_params.max_input_tokens,
            model=self.config_class.original_model
        )

    def _get_lm_payloads(
        self,
        text_extracted: dict,
        use_rag: bool,
        prompt,
        emb_params: dict,
        prompt_need_auth: bool = False      
    ):

        token, use_case, int_mode = (
            emb_params.get("token"),
            emb_params.get("use_case"),
            emb_params.get("int_mode"),
        )

        if use_rag:

            embedder = dct_embedder_factory.get(f"{self.config_class.embedder_id}")

            embedder_routine = embedder(
                token=token, use_case=use_case, interaction_mode=int_mode
            )

            text_extracted, _, page_mapping = embedder_routine.start_rag(
                text_extracted=text_extracted, dict_entity=prompt.dict_entity
            )

        else:

            page_mapping = {
                i: int(key.split("_")[1])
                for i, key in enumerate(text_extracted.keys(), start=1)
            }
            text_extracted = [value for _, value in text_extracted.items()]

        necessary_prompts, text_prompts = prompt.build_prompt_llm(
            text_extracted=text_extracted, page_mapping=page_mapping
        )

        if prompt_need_auth:
            return prompt.create_payloads(
                necessary_prompts=necessary_prompts,
                prompts=text_prompts,
                page_mapping=page_mapping,
                max_tokens_per_call=self.config_class.model_params.max_input_tokens,
                use_case=use_case,
                token=token,
                model=self.config_class.original_model
            )

        return prompt.create_payloads(
            necessary_prompts=necessary_prompts,
            prompts=text_prompts,
            page_mapping=page_mapping,
            max_tokens_per_call=self.config_class.model_params.max_input_tokens,
            model=self.config_class.original_model
        )

    @staticmethod
    def _call_api_sync(token: str, payload: dict, lai_manager: LAIUtilitiesManager):

        max_retry = RetryDefaultConfig.max_retry_sync
        sync_started = False
        response_out = ""
        sync_response = None
        exception_text = ""

        while max_retry > 0 and not sync_started:

            try:
                sync_response = session.post(
                    url=f"{lai_manager.dispatcher_url}srv/sync/generate?sv=1",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                    stream=False,
                    verify=False,
                )

                if sync_response.status_code == 200:
                    logging.debug("Sync execution completed")
                    response_out = sync_response
                    sync_started = True

                elif sync_response.status_code == 500:
                    logging.error(
                        f"Error response sync endpoint: {sync_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    sync_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method AbstractLM.{get_function_name()}:"
                        f"Error response sync endpoint: {sync_response.text}.",
                        status_code=sync_response.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Exception occurred on response sync endpoint: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not sync_started:
            if sync_response is None:
                raise SmartOCRException(
                    msg=f"Method AbstractLM.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries due "
                        f"to the following exception: {exception_text}"
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractLM.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries "
                        f"due to the following error response from sync endpoint: {sync_response.text}",
                    status_code=sync_response.status_code
                )

        return response_out

    @staticmethod
    def _call_api_async(token: str, payload: dict, lai_manager: LAIUtilitiesManager):

        uid = lai_manager.initiate_job()
        payload["uid"] = uid

        max_retry = RetryDefaultConfig.max_retry_async
        async_started = False
        async_response = None
        exception_text = ""

        while max_retry > 0 and not async_started:

            try:
                async_response = session.post(
                    url=f"{lai_manager.dispatcher_url}srv/async/generate?sv=1",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                    stream=False,
                    verify=False,
                )

                if async_response.status_code == 200:
                    logging.debug("Async execution started")
                    async_started = True

                elif async_response.status_code == 500:
                    logging.error(
                        f"Error response async endpoint: {async_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    async_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method AbstractLM.{get_function_name()}:"
                            f"Error response async endpoint: {async_response.text}.",
                        status_code=async_response.status_code
                    )

            except Exception as e:
                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Exception occurred on response async endpoint: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not async_started:
            if async_response is None:
                raise SmartOCRException(
                    msg=f"Method AbstractLM.{get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries "
                        f"due to the following exception: {exception_text}",
                )
            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractLM.{get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries "
                        f"due to the following error response in async endpoint {async_response.text}",
                    status_code=async_response.status_code
                )

        return lai_manager.check_status_and_retrieve(uid=uid)

    def call_api(
        self, token: str, payload: dict, lai_manager: LAIUtilitiesManager, sync: bool
    ):

        if sync:
            return self._call_api_sync(
                token=token, payload=payload, lai_manager=lai_manager
            )

        return self._call_api_async(
            token=token, payload=payload, lai_manager=lai_manager
        )

    @abstractmethod
    def extract_entity_from_image(self, *args, **kwargs):
        """
        Metodo astratto relativo all'estrazione di entità da file immagine.
        """
        pass

    @abstractmethod
    def extract_entity_from_text(self, *args, **kwargs):
        """
        Metodo astratto relativo all'estrazione di entità da contenuto testuale.
        """
        pass
