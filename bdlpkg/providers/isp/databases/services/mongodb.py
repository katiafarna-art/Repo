import pymongo
from typing import Optional, Union
from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings


def get_mongo_client(
        mongo_istance_name: Optional[str] = None,
        use_first_db: bool = False) -> Union[pymongo.MongoClient, pymongo.synchronous.database.Database]:
    """Return a Connection object to handle connection to Mongo 

    :param mongo_istance_name: istance name used in 'configuration.yml' to define the mounted secret, defaults to None (the first)
    :type mongo_istance_name: str, optional
    :param use_first_db: If True, return the client connected to the first available database instead of the raw client.
    :type use_first_db: bool, optional
    :return: the Mongo client or the first database object if use_first_db is True
    :rtype: Union[pymongo.MongoClient, pymongo.database.Database]
    """
    mi = get_datasource_settings("database", "mongo", mongo_istance_name)

    if mi.resource_name == "mockupdb":
        #from dependencies.database.mongo.mockup.mockupdb import MongoMockup
        #db = MongoMockup()
        #mongo_istances[mi].url = db.get_uri()
        pass

    client = pymongo.MongoClient(mi.url,
                               username=mi.name,
                               password=mi.password.get_secret_value(),
                               maxPoolSize=mi.max_pool_size,
                               minPoolSize=mi.min_pool_size,
                               connectTimeoutMS=mi.connection_timeout)

    if use_first_db:
        first_db_name = client.list_database_names()[0] if client.list_database_names() else None
        return client[first_db_name] if first_db_name else client

    return client


def get_mongo_healthcheck(mongo_istance_name: Optional[str] = None) -> dict:
    """Healtcheck for Mongo

    :param mongo_istance_name: Mongo istance to test, defaults to None
    :type mongo_istance_name: str, optional
    :return: a dict with the result of connection tests
    :rtype: dict
    """
    _client = get_mongo_client(mongo_istance_name)
    _dbs = _client.list_database_names()
    _collections = {}
    filter = {"name": {"$regex": r"^(?!system\.)"}}
    for _db in _dbs:
        _collections[_db] = _client[_db].list_collection_names(filter=filter)

    return {"databases": _dbs, "collections": _collections}
