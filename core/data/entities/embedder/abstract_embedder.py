"""Modulo contenente la classe astratta per gli embedder offerti dal servizio"""

import json
import time
import logging
import operator
import numpy as np
from typing import Optional
from collections import OrderedDict
from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.parameters import EmbedderDefaultConfig, RetryDefaultConfig
from core.routines.entities import session, get_function_name
from core.routines.services import LAIUtilitiesManager
from core.exceptions import (
    SmartOCRInputError,
    SmartOCRLayeraiException,
    SmartOCRException,
)


class AbstractEmbedder(ABC):

    top_n: int = EmbedderDefaultConfig.top_n

    def __init__(self, chunk_size: int = 1500):
        self.chunk = chunk_size

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm_vec1, norm_vec2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        return (
            0.0
            if norm_vec1 == 0 or norm_vec2 == 0
            else np.dot(vec1, vec2) / (norm_vec1 * norm_vec2)
        )

    def _split_pages_max_tokens(self, documents: dict) -> dict[str, list]:

        if not documents:
            raise SmartOCRInputError(
                f"Method {self.__class__.__name__}.{get_function_name()}: "
                f"No document provided for processing"
            )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk, chunk_overlap=100
        )

        return {
            page: text_splitter.create_documents(texts=[documents[page]])
            for page in documents
        }

    @staticmethod
    def _extract_content_and_images(
        data_dict: dict, image_bytes_dict: Optional[dict] = None
    ):

        content_dict = OrderedDict()
        pages = []
        # Estrae e ordina le chiavi doc_id
        doc_ids = sorted(
            [item["doc_id"] for key in data_dict for item in data_dict[key]],
            key=lambda x: int(x.split("_")[1]),
        )

        # Popola content_dict e page_mapping in ordine
        for doc_id in doc_ids:
            for key, items in data_dict.items():
                for item in items:
                    if item["doc_id"] == doc_id and doc_id not in content_dict:
                        content_dict[doc_id] = item["content"]
                        pages.append(int(doc_id.split("_")[1]))
                        break

        # Estrae testo e immagini nell'ordine corretto più mappa le pagine
        # con quelle effettivamente estratte per il prompt dopo

        text_extracted = list(content_dict.values())
        page_mapping = {i: pages[i - 1] for i in range(1, len(pages) + 1)}

        img = (
            [
                image_bytes_dict[f"pag_{page_mapping[key]}"]
                for key in page_mapping.keys()
            ]
            if image_bytes_dict
            else None
        )

        return text_extracted, img, page_mapping

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
                    url=f"{lai_manager.dispatcher_url}srv/sync/embedding?sv=1",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
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
                        msg=f"Method AbstractEmbedder.{get_function_name()}: "
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
                    msg=f"Method AbstractEmbedder.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries due to "
                        f" the following exception: {exception_text}",
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries! "
                        f" due to the following error response from sync endpoint: {sync_response.text}",
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
                    url=f"{lai_manager.dispatcher_url}srv/async/embedding?sv=1",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
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
                        msg=f"Method AbstractEmbedder.{get_function_name()}"
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
                    msg=f"Method AbstractEmbedder.{get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries due to "
                        f"the following exception: {exception_text}",
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractEmbedder.{get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries"
                        f" due to the following error response from async endpoint: {async_response.text}",
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
    def _get_embedding(self, page: str) -> list[float]:
        pass

    def _embed_pages(self, docs: dict) -> dict:

        docs = self._split_pages_max_tokens(docs)
        embeddings = {
            page: [] for page in docs
        }  # rimango coerente con i numeri di pagina

        for doc, chunks in docs.items():
            full_content = " ".join(chunk.page_content for chunk in chunks)
            for i, chunk in enumerate(chunks):
                if len(embeddings[doc]) <= i:
                    embeddings[doc].append({})

                # TODO: get_embedding ora può embeddare una lista di contenuti, valutare se rivisitare il ciclo for
                embeddings[doc][i]["embedding"] = self._get_embedding(
                    chunk.page_content
                )
                embeddings[doc][i]["content"] = full_content

        return embeddings

    def _embed_entities(self, entity_dict: list[dict]) -> dict:

        if not isinstance(entity_dict, list):
            entity_dict = [entity_dict]

        embeddings = {
            entity["name"]: {"embedding": self._get_embedding(entity["description"])}
            for entity in entity_dict
        }

        return embeddings

    def _compute_similarity(
        self, embedding_docs: dict, embedding_entities: dict
    ) -> dict:

        similarity_dict = {entity_key: {} for entity_key in embedding_entities.keys()}

        for entity_key, entity_content in embedding_entities.items():
            for doc_key, doc_chunks in embedding_docs.items():
                max_similarity = 0

                for chunk in doc_chunks:
                    similarity = self._cosine_similarity(
                        entity_content["embedding"], chunk["embedding"]
                    )

                    if similarity > max_similarity:
                        max_similarity = similarity

                similarity_dict[entity_key][doc_key] = max_similarity

        return similarity_dict

    def _retrieve_most_similar_pages(
        self,
        similarity_dict: dict[str, dict[str, float]],
        embeddings_dict: dict[str, dict[str, str]],
        images: Optional[dict] = None,
    ) -> dict[str, list[dict[str, any]]]:

        results = {}

        for key, similarities in similarity_dict.items():
            sorted_similarities = sorted(
                similarities.items(), key=operator.itemgetter(1), reverse=True
            )
            top_docs = sorted_similarities[: self.top_n]

            key_results = []
            for doc_id, similarity in top_docs:
                try:
                    content = embeddings_dict[doc_id][0]["content"]
                    key_results.append(
                        {"doc_id": doc_id, "content": content, "similarity": similarity}
                    )
                except KeyError:
                    logging.warning(
                        f"Documento non trovato durante l'embedding: {doc_id}"
                    )

            results[key] = key_results

        return self._extract_content_and_images(results, images)

    def start_rag(
        self,
        text_extracted: dict,
        dict_entity: list[dict],
        images_mapped: Optional[list[bytes]] = None,
    ):

        docs_embedding = self._embed_pages(text_extracted)
        entities_embedding = self._embed_entities(json.loads(dict_entity))
        similarity_dict = self._compute_similarity(docs_embedding, entities_embedding)

        return self._retrieve_most_similar_pages(
            similarity_dict, docs_embedding, images_mapped
        )
