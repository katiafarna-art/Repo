from config.input_models.image_description import ImageDescriptionParams


class PayloadGenerator(object):
    """Classe che si occupa di generare il payload da passare al LayerAI.

    La classe prende in input i parametri di generazione, l'use_case_id, il provider ed il modello da utilizzare. Tali
    oggetti vengono combinati per generare un dizionario di parametry (payload) con il formato corretto da passare al
    LayerAI.

    :param generation_params: Oggetto contenente le valorizzazioni relative ai vari parametri per lo svolgimento
        dell'estrazione di entità, come `temperature` e `max_output_token`.
    :type generation_params: ImageDescriptionParams
    :param use_case_id: Identificativo univoco associato al caso d'uso.
    :type use_case_id: str
    :param provider: Nome del provider del modello. Valori ammessi: "openai" e "gemini".
    :type provider: str
    :param model: nome del modello VLM da utilizzare per l'estrazione delle descrizioni
    :type model: str
    """

    def __init__(self, generation_params: ImageDescriptionParams, use_case_id: str, provider: str, model: str):
        self.generation_params = generation_params
        self.use_case_id = use_case_id
        self.provider = provider
        self.model = model

    def generate_payload(self, messages: list[dict]) -> dict:
        """Metodo effettivamente responsabile della generazione del payload da passare al LayerAI."""
        payload = {
            "provider": self.provider,
            "use_case_id": self.use_case_id,
            "generation_params": {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "timeout": 900,
                "include_usage": True,
                **self.generation_params.model_dump(exclude_unset=True)
            }
        }

        return payload
