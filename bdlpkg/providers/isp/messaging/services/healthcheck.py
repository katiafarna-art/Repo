import logging
from bdlpkg.providers.isp.settings.services.isp_config import get_settings
from bdlpkg.providers.isp.messaging.services.mail import get_mail_client

from typing import Optional, Dict


def get_mail_healthcheck(
        settings: dict,
        mail_istance_name: Optional[str] = None) -> Dict[str, str]:
    """Healthcheck for email client

    :param settings: dict with email client settings
    :type settings: dict
    :param mail_istance_name: Mail istance name, defaults to None
    :type mail_istance_name: str, optional   
    :return: a dict with the result of connection tests
    :rtype: dict
    """

    result: Dict[str, str] = {}

    client = get_mail_client(mail_istance_name=mail_istance_name)

    if (client.helo()[0] == 250):
        result = {
            "server": settings[mail_istance_name].mail_smtp_server_host,
            "port": settings[mail_istance_name].mail_smtp_server_port,
            "address": settings[mail_istance_name].mail_address
        }

    return result


def get_mails_healthcheck() -> dict:
    """Healthcheck for all email clients

    :return: a dict with the result of connection tests for all email istances
    :rtype: dict
    """
    _result = {}
    _settings = get_settings()["mail"]

    for _mail in _settings:
        logging.info(f"Executing healthcheck for {_mail} of type mail")
        _result[_mail] = get_mail_healthcheck(_settings, _mail)
    return _result


def get_messaging_healthcheck(acronimo: str) -> dict:
    """Healthcheck for all messaging services (i.e. email and Kafka)

    :param acronimo: acronym related to Kafka topics, defaults to BDL10
    :type acronimo: str
    :return: a dict with the result of connection tests for all messaging service istances
    :rtype: dict
    """
    _result = {}
    _settings = get_settings()["messaging"]

    for ds_type in _settings:
        _result[ds_type] = {}
        for istance_name in _settings[ds_type]:
            if ds_type == "kafka":
                logging.info(f"Executing healthcheck for {istance_name} of type {ds_type}")
                from bdlpkg.providers.isp.messaging.services.kafka import get_kafka_healthcheck
                _tmp = get_kafka_healthcheck(istance_name, acronimo)

            _result[ds_type][istance_name] = _tmp

    return _result