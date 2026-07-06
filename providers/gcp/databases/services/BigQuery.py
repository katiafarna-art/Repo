from google.cloud.bigquery.client import Client as BQClient
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from bdlpkg.providers.gcp.settings.services.gcp_config import get_datasource_settings
from bdlpkg.providers.gcp.settings.entities.sa.gcp import SASettings
from typing import Optional, List

import json
import pandas as pd
import logging

class BigQuery:
    def __init__(self,
                 sa_istance_name: Optional[str] = None):
        """
        Return a BigQuery client to connect to BigQuery configured
        :param sa_istance_name: the name of the resource name of sa, optional
        :type sa_istance_name: Optional[String]
        :return: a resource to connect to BigQuery
        :rtype: Client
        """
        sai: SASettings = get_datasource_settings("service_account", sa_istance_name)
        sa_json = json.loads(sai.credentials.get_secret_value())
        self.client = BQClient.from_service_account_info(sa_json)


    def list_datasets(self) -> list:
        """
        Return the list of datasets in the project associated with client
        :return: list of datasets in the project
        :rtype: list
        """
        ds = list(self.client.list_datasets())
        datasets = [d.dataset_id for d in ds]

        return datasets
    

    def list_tables(self,
                    dataset_name: str) -> list:
        """
        Return the list of tables in the dataset
        :param dataset_name: the name of the dataset (like DB schema)
        :type dataset_name: String
        :return: list of tables in the dataset
        :rtype: list
        """
        ts = list(self.client.list_tables(dataset_name))
        tables = [t.table_id for t in ts]

        return tables
    

    def create_table(self,
                     project_name: str,
                     dataset_name: str) -> bool:
        """
        Create a table in the dataset
        :param project_name: the name of the project
        :type project_name: String
        :param dataset_name: the name of the dataset (like DB schema)
        :type dataset_name: String
        :return: True if the dataset is properly created
        :rtype: boolean
        """
        dataset = bigquery.Dataset(f"{project_name}.{dataset_name}")
        dataset.location = "europe-west12"   #Data location for ISP GCP project
        try:
            dataset = self.client.create_dataset(dataset)
            logging.info(
                "Created dataset {}.{}.{}".format(dataset.project, dataset.dataset_id)
            )
            return True
        except Exception as e:
            raise NotFound("Project doesn't exists. {}".format(e))
    

    def create_table(self,
                     project_name: str,
                     dataset_name: str,
                     table_name: str,
                     schema: Optional[List[bigquery.SchemaField]]=None) -> bool:
        """
        Create a table in the dataset
        :param project_name: the name of the project
        :type project_name: String
        :param dataset_name: the name of the dataset (like DB schema)
        :type dataset_name: String
        :param table_name: the name of the table
        :type table_name: String
        :return: True if the table is properly created
        :rtype: boolean
        """
        table = bigquery.Table(f"{project_name}.{dataset_name}.{table_name}", schema=schema)
        try:
            table = self.client.create_table(table)
            logging.info(
                "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
            )
            return True
        except Exception as e:
            raise NotFound("Project or Dataset doesn't exists. {}".format(e))


    def load_table(self,
                   df: pd.DataFrame,
                   dataset_name: str,
                   table_name: str) -> bool:
        """
        Load data in table
        :param dataset_name: the name of the dataset (like DB schema)
        :type dataset_name: String
        :param table_name: the name of the table
        :type table_name: String
        :return: True if the data are properly loaded
        :rtype: boolean
        """
        try:
            self.client.load_table_from_dataframe(dataframe=df, destination=f"{dataset_name}.{table_name}")
            return True
        except Exception as e:
            raise ValueError("Error in loading table. {}".format(e))


    def execute_query(self,
                      str_query: str) -> pd.DataFrame:
        """
        Return the list of tables in the dataset
        :param str_query: the query to be executed
        :type str_query: String
        :return: Pandas DataFrame result of the query
        :rtype: Pandas DataFrame
        """
        rowiter = self.client.query_and_wait(str_query)
        df_out = rowiter.to_dataframe()

        return df_out
    

def get_bigquery_healthcheck(sa_istance_name: Optional[str] = None) -> dict:
    """
    Performe the healthcheck on the BigQuery to check its status, 
    giving back the list of datasets and tables for each dataset

    :param bucket_name: the name of the bucket
    :type bucket_name: String
    :param sa_istance_name: the name of the GCP sa istance, optional
    :type sa_istance_name: Optional[str]
    :return: a dictionary having all the blobs in the gcs bucket
    :rtype: dict
    """
    try:
        bq = BigQuery(sa_istance_name)
        _datasets = bq.list_datasets()
        _tables = {}
        for _dt in _datasets:
            _tables[_dt] = bq.list_tables(_dt)
        
        result = {"datasets": _datasets, "tables": _tables}
    except Exception as e:
        result = {
            "online": False,
            "message": "Failed with uncaught exception 🥦 " + str(e) + " 🥦",
        }

    return result
