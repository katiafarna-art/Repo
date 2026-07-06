from abc import ABC, abstractmethod
from typing import Optional, Literal


class IDPromptTemplate:
    """Classe conenente le stringhe di default per il prompt usato per la descrizione delle immagini"""

    system_message = {
        "en": """
        You are an AI assistant that converts document images into text-based representations.  
        For every image you receive, generate a clear and informative caption that describes its visible content and purpose within a document.
        The description will then be used to replace the image inside its original document.
        Follow these guidelines: 
        * Be factual and neutral — do not infer beyond what is visible
        * Include relevant visual elements (e.g., people, objects, text, charts, tables, diagrams)
        * If it is a chart or figure, summarize its type and what it appears to show.
        * Avoid artistic or emotional descriptions.
        * Output only the caption text, without metadata or additional commentary.
        """,
        "it": """
        Sei un assistente AI che converte le immagini presenti nei documenti in rappresentazioni testuali.
        Per ogni immagine ricevuta, genera una didascalia chiara e informativa che descriva il contenuto visibile e lo scopo dell’immagine all’interno del documento.
        La descrizione verrà poi utilizzata per sostituire l’immagine nel documento originale.
        Segui queste linee guida:
        * Sii fattuale e neutrale: non dedurre nulla che non sia visibile.
        * Includi gli elementi visivi rilevanti (ad esempio persone, oggetti, testo, grafici, tabelle, diagrammi).
        * Se l’immagine contiene testo, trascrivilo esattamente.
        * Se si tratta di un grafico o di una figura, riassumi il tipo e ciò che sembra mostrare.
        * Evita descrizioni artistiche o emotive.
        * Produci solo il testo della didascalia, senza metadati o commenti aggiuntivi.
        """
    }
    user_message = {
        "en": "The following image appears in a technical document. Generate a caption that would replace the image in the text version of the document.",
        "it": "L’immagine seguente appare in un documento tecnico. Genera una didascalia che possa sostituire l’immagine nella versione testuale del documento."
    }


class PromptGenerator(ABC):
    """Classe astratta che definisce l'interfaccia delle classi usate per la generazione del prompt

    :param system_message: messaggio di sistema del prompt usato. Il messaggio di sistema è quello che consente di
        definire il ruolo ed il tono del modello.
    :param user_message: prompt vero e proprio passato al modello. Tale messaggio consente di
          definire il task o, più in generale, cosa ci si aspetta dal modello.
    :type user_message: (str, optional)
    :param language: Lingua del testo e dell'entità definita. Questo parametro consente di recuperare il prompt di
        default definito da IDPromptTemplate. Risulta, dunque, non necessario qualora vengano passati sia system message
        che user message
    """
    provider: str = None

    def __init__(self, system_message: Optional[str] = None,
                 user_message: Optional[str] = None,
                 language: Optional[Literal["en", "it"]] = None):
        self.system_message, self.user_message = self._configure_messages(system_message=system_message,
                                                                          user_message=user_message,
                                                                          language=language)

    @staticmethod
    def _configure_messages(system_message: Optional[str] = None,
                            user_message: Optional[str] = None,
                            language: Optional[Literal["en", "it"]] = None):
        """Metodo che si occupa di ottenere i messaggi da usare per il prompt

        Tale metodo va a verificare se sono stati passati i messaggi custom. In caso contrario, li recupera a partire
        dai messaggi di default, che sono definiti all'interno della classe IDPromptTemplate e dipendono dal linguaggio
        selezionato.
        """

        if not system_message:
            system_message = IDPromptTemplate.system_message[language]  # noqa
        if not user_message:
            user_message = IDPromptTemplate.user_message[language]  # noqa

        return system_message, user_message

    @abstractmethod
    def generate_messages(self, img: str) -> list[dict]:
        """Interfaccia del metodo deputato a definire il prompt nel formato adeguato al provider utilizzato"""
        pass


class OpenAIPromptGenerator(PromptGenerator):
    provider = "azure"

    def generate_messages(self, img: str) -> list[dict]:
        """Metodo che definisce il prompt nel formato adeguato per i modelli OpenAI"""
        messages = [
            {
                "role": "system",
                "name": "system",
                "content": self.system_message
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.user_message
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{img}",
                        "image_url_detail": "high"
                    }
                ]
            }
        ]

        return messages


class GeminiPromptGenerator(PromptGenerator):
    provider = "google"

    def generate_messages(self, img: str) -> list[dict]:
        """Metodo che definisce il prompt nel formato adeguato per i modelli Gemini"""
        messages = [
            {
                "role": "USER",
                "parts": [
                    {
                        "text": self.system_message
                    },
                    {
                        "type": "text",
                        "text": self.user_message
                    },
                    {
                        "mime_type": "image/png",
                        "data": img
                    }
                ]
            }
        ]

        return messages
