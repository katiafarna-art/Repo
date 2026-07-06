from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings
from bdlpkg.providers.isp.settings.entities.messaging.kafka import KafkaSettings
from typing import Optional, Dict
from confluent_kafka import Consumer, Producer

key_mapping = {'brokers':'bootstrap.servers', 'principal':'sasl.kerberos.principal', 'file_path':'sasl.kerberos.keytab',
               'security_protocol':'security.protocol', 'service_name':'sasl.kerberos.service.name',
               'session_timeout':'session.timeout.ms','mechanisms':'sasl.mechanisms'}

def get_kafka_consumer(group_id: str, kafka_istance_name: Optional[str] = None, custom_config: Optional[Dict] = None) -> Consumer:
    """Create kafka consumer

    :param group_id: group_id
    :type group_id: str
    :param kafka_istance_name: istance name used in 'configuration.yml' to define the mounted secret, defaults to None (the first)
    :type kafka_istance_name: Optional[str], optional
    :param custom_config: custom configuration for kafka consumer
    :type custom_config: Optional[dict], optional
    :return: Kafka consumer
    :rtype: Consumer
    """
    ki: KafkaSettings = get_datasource_settings("messaging", "kafka", kafka_istance_name)
    dict_config = map_keys_to_new(ki.model_dump(), key_mapping)
    dict_config['group.id'] = group_id  #aggiunto il riferimento al group_id 
    dict_config['auto.offset.reset']='earliest'
    if custom_config is not None:
        dict_config = dict_config | custom_config

    return Consumer(dict_config)

def get_kafka_producer(kafka_istance_name: Optional[str] = None, custom_config: Optional[Dict] = None) -> Producer:
    """Create kafka producer

    :param kafka_istance_name: istance name used in 'configuration.yml' to define the mounted secret, defaults to None (the first)
    :type kafka_istance_name: Optional[str], optional
    :param custom_config: custom configuration for kafka producer
    :type custom_config: Optional[dict], optional
    :return: Kafka producer
    :rtype: Producer
    """
    ki: KafkaSettings = get_datasource_settings("messaging", "kafka", kafka_istance_name)
    dict_config = map_keys_to_new(ki.model_dump(), key_mapping)
    if custom_config is not None:
        dict_config = dict_config | custom_config

    return Producer(dict_config)

def map_keys_to_new(dict_to_map: dict, key_mapping: dict) -> dict:
    """Mapping from existing to new keys

    :param dict_to_map: dict that contains keys to be mapped
    :type dict_to_map: dict
    :param key_mapping: dict that contains the mapping from existing to new keys
    :type key_mapping: dict
    :return: dict with mapped keys
    :rtype: dict
    """
    if not isinstance(key_mapping, dict):
        raise("Il mapping delle chiavi deve essere un dizionario.")
    # Crea un nuovo dizionario con le chiavi nuove e i valori corrispondenti
    mapped_dict = {key_mapping[k]: dict_to_map[k]  for k in key_mapping.keys()}
    return mapped_dict


def get_kafka_healthcheck(kafka_istance_name: Optional[str] = None, acronimo: str="BDL10") -> dict:
    """Healtcheck for Kafka

    :param kafka_istance_name: Kafka istance to test, defaults to None
    :type kafka_istance_name: str, optional
    :param acronimo: acronym related to Kafka topics, defaults to BDL10
    :type acronimo: str
    :return: a dict with the result of connection tests
    :rtype: dict
    """
    result: dict = {}
    
    try:
        p = get_kafka_producer(kafka_istance_name)
        topics = list(p.list_topics().topics.keys())
        topics_acr = [t for t in topics if acronimo in t]    #filter on topics related to acronym

        result["Topics"] = topics_acr

    except Exception as e:
        result["Error"] = "{}".format(e)

    return result