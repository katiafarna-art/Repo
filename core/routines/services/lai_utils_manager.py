"""Modulo contenente una classe ausiliaria per l'interazione con il LayerAI."""

import os
import time
import logging
from typing import Any, Literal
from config.parameters import dispatcher_gateway_url, RetryDefaultConfig
from core.routines.entities import session, check_file_type, get_function_name
from core.exceptions import SmartOCRLayeraiException, SmartOCRException


class LAIUtilitiesManager(object):
    """Utility manager for interacting with LayerAI to handle jobs and file uploads."""

    file_type_to_payload = {
        "img": ("uploaded_file.png", "application/octet-stream"),
        "pdf": ("uploaded_file.pdf", "application/pdf"),
    }

    def __init__(self, token: str, use_case: str, version: Literal[1, 2] = 2):
        """
        Initializes the LAIUtilitiesManager with the provided token and use case ID. The attribute 'dispacher_url'
        is parametrically choosen from environmental variable 'ISP_AMBIENTE'.

        :param token: The bearer token required for API authorization.
        :type token: str
        :param use_case: The use case identifier for the job.
        :type use_case: str
        """
        self.token = token
        self.use_case = use_case
        current_env = os.getenv("ISP_AMBIENTE", "svis")

        dispatcher_url_template = dispatcher_gateway_url.get(
            current_env, dispatcher_gateway_url["prod"]
        )

        self.dispatcher_url = dispatcher_url_template.substitute(version=version)

        self.dispatcher_url_v1 = dispatcher_url_template.substitute(version=1)

    def initiate_job(self) -> str:
        """
        Initiates a job on the dispatcher API using the use case ID provided during initialization. It retries the
        request if it encounters specific error responses.

        :return: A unique job ID.
        :rtype: str
        """
        uid = ""
        max_retry = RetryDefaultConfig.max_retry_init
        init_completed = False
        init_response = None
        exception_text = ""

        while max_retry > 0 and not init_completed:

            try:
                init_response = session.post(
                    f"{self.dispatcher_url_v1}plt/init/",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"use_case_id": self.use_case},
                    verify=False,
                )

                if init_response.status_code == 200:
                    file_key = init_response.json()["id"]
                    uid = file_key.split("/")[-1]
                    logging.info(f"Layer id: {uid} - Job initialized")
                    init_completed = True

                elif init_response.status_code == 500:
                    logging.error(
                        f"Error response in dispatcher init: {init_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    init_completed = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                            f"response error in dispatcher init - > {init_response.text}.",
                        status_code=init_response.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Exception occurred in dispatcher init: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not uid:
            if init_response is None:
                raise SmartOCRException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                        f"ERROR - > Failed to init the job after all retries!" 
                        f"due to the following exception: {exception_text}",
                )
            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR: Failed to start the async process after all retries "
                        f"due to the following error response in init endpoint {init_response.text}",
                    status_code=init_response.status_code
                )
        else:
            return uid

    def _get_file_metadata(self, file: bytes, file_type: str) -> tuple[str, str]:
        """Returns the file name and content type based on the file type."""
        file_name, content_type = self.file_type_to_payload[file_type]
        if file_type == "img":
            file_name = f"uploaded_file{check_file_type(file_content=file)}"
        return file_name, content_type

    def upload_file(
        self, uid: str, file: bytes, file_type: Literal["pdf", "img"]
    ) -> str:
        """
        Uploads a file to the dispatcher API for the initiated job.

        :param uid: The unique identifier of the job.
        :rtype uid: str
        :param file: The file content to be uploaded.
        :rtype file: bytes
        :param file_type: The file type being uploaded, e.g., "pdf" or "img".
        :rtype file_type: Literal["pdf", "img"]

        :return: The name of the uploaded file on the server.
        :rtype: str
        """

        request = {"id": uid, "use_case_id": self.use_case}
        file_name, content_type = self._get_file_metadata(file=file, file_type=file_type)
        files = [("file", (file_name, file, content_type))]

        max_retry = RetryDefaultConfig.max_retry_upload
        upload_response = None
        exception_text = ""

        for _ in range(max_retry):

            try:
                upload_response = session.post(
                    f"{self.dispatcher_url_v1}plt/upload/",
                    files=files,
                    params=request,
                    headers={"Authorization": f"Bearer {self.token}"},
                    verify=False,
                )

                if upload_response.status_code == 200 and upload_response.json()["success"]:
                    logging.info(
                        f"Layer id: {uid} - Correctly uploaded file {upload_response.json()['key']}"
                    )
                    return upload_response.json()["key"]

                elif upload_response.status_code == 200 and not upload_response.json()["success"]:
                    logging.error(
                        f"Layer id: {uid} - Unsuccessful file upload \n Try Again!"
                    )
                    time.sleep(RetryDefaultConfig.sleep_default)

                elif upload_response.status_code == 500:
                    logging.error(
                        f"Layer id: {uid} - Error response upload: {upload_response.text} \n Try Again!"
                    )
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    raise SmartOCRLayeraiException(
                        msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                            f"Layer id: {uid} - Error response upload: {upload_response.text}.",
                        status_code=upload_response.status_code  
                    )

            except SmartOCRLayeraiException as e:
                raise e

            except Exception as e:
                logging.error(
                    f"Layer id: {uid} - Exception occurred on response upload: {str(e)} \n Try Again!"
                )
                time.sleep(RetryDefaultConfig.sleep_default)
                exception_text = str(e)

        if upload_response is None:
            raise SmartOCRException(
                msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                    f"ERROR - > Failed to upload the file after all retries!"
                    f"due to the following exception: {exception_text}"
            )
        else:
            raise SmartOCRLayeraiException(
                msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                    f"Layer id: {uid} - ERROR: Failed to upload the file after all retries!"
                    f"{upload_response.text}",
                status_code=upload_response.status_code
            )

    def check_status(self, uid: str) -> tuple[int, dict[str, Any]]:
        """
        Checks the status of an ongoing job on the dispatcher API.

        :param uid: The unique identifier of the job.
        :type uid: str

        :return: The job status code and the content as a dictionary.
        :rtype: tuple[int, dict[str, Any]
        """

        max_retry = RetryDefaultConfig.max_retry_status
        status_ready = False
        last_status = 10
        last_content = ""
        last_status_response = None
        exception_text = ""

        while max_retry > 0 and not status_ready:

            try:
                last_status_response = session.get(
                    f"{self.dispatcher_url_v1}plt/get_last_status/{uid}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    verify=False,
                )

                if last_status_response.status_code == 200:
                    status_ready = True
                    last_status = last_status_response.json()["status"]
                    last_content = last_status_response.json()
                    logging.debug(
                        f"Layer id: {uid} - Correctly retrieved status {last_status}"
                    )

                elif last_status_response.status_code == 500:
                    logging.error(
                        f"Layer id: {uid} - Error response get last status: {last_status_response.text} "
                        f"\n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    status_ready = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method {self.__class__.__name__}.{get_function_name()}:"
                            f" Layer id: {uid} - Error response get last status:"
                            f" {last_status_response.text}.",
                            status_code=last_status_response.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Layer id: {uid} - Exception occurred on response get last status: {exception_text} "
                    f"\n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not status_ready:
            if last_status_response is None:
                raise SmartOCRException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                        f"Layer id: {uid} - ERROR: Failed to check the status after all retries" 
                        f"due to the following exception: {exception_text}",
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR: Failed to start the async process after all retries!"
                        f"due to the following error response in get status endpoint {last_status_response.text}",
                    status_code=last_status_response.status_code
                )

        return last_status, last_content

    def retrieve_content(self, uid: str) -> dict[str, Any]:
        """
        Retrieves the content for a completed job.

        :param uid: The unique identifier of the job.
        :type uid: str

        :return: The retrieved job content
        :rtype: dict[str, Any]
        """

        max_retry = RetryDefaultConfig.max_retry_retrieve
        response_out = ""
        content_retrieved = False
        response_retrieve = None
        exception_text = ""

        while max_retry > 0 and not content_retrieved:

            try:
                response_retrieve = session.get(
                    f"{self.dispatcher_url_v1}plt/retrieve/{self.use_case}/{uid}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    verify=False,
                )

                if response_retrieve.status_code == 200:
                    logging.info(
                        f"Layer id: {uid} - Job response retrieved with success!"
                    )
                    response_out = response_retrieve
                    content_retrieved = True

                elif response_retrieve.status_code == 500:
                    logging.error(
                        f"Layer id: {uid} - Error response retrieve: {response_retrieve.text} \n Try Again!"
                    )
                    max_retry -= response_retrieve
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    content_retrieved = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                            f"Layer id: {uid} - Error response retrieve - > "
                            f"{response_retrieve.text}.",
                        status_code=response_retrieve.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Layer id: {uid} - Exception occurred on response retrieve: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not response_out:
            if response_retrieve is None:
                raise SmartOCRException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR - > Failed to retrieve the result after all retries " 
                        f" due to the following exception: {exception_text}",
                )
            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR - > "
                        f"Failed to retrieve the result after all retries!"
                        f"{response_retrieve.text}",
                    status_code=response_retrieve.status_code
                )

        return response_out

    def check_status_and_retrieve(self, uid: str) -> dict[str, Any]:
        """
        Checks the job status and retrieves content if ready.

        :param uid: The unique identifier of the job.
        :type uid: str

        :return: The retrieved job content
        :rtype: dict[str, Any]
        """

        max_retry = RetryDefaultConfig.max_retry_pipeline
        content_retrieved = False
        output = ""
        last_status, last_content = None, None

        while max_retry > 0 and not content_retrieved:

            try:
                last_status, last_content = self.check_status(uid)

                if last_status == 15:
                    logging.info(f"Layer id: {uid} - Status ready for retrieve")
                    content_retrieved = True
                    output = self.retrieve_content(uid)

                elif 10 < last_status < 15:
                    max_retry -= 1
                    logging.info(
                        f"Layer id: {uid} - Status not ready yet: code {last_status}. Retrying..."
                    )
                    time.sleep(RetryDefaultConfig.sleep_retry)

                else:
                    raise SmartOCRLayeraiException(
                        msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                            f"Layer id: {uid} - error with check status. "
                            f"Last content is {last_content}",
                        status_code=last_status
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                raise SmartOCRException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}:"
                        f"Layer id: {uid} - Exception {str(e)}",
                )

        if not content_retrieved:
            if last_status and last_content:
                raise SmartOCRLayeraiException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                        f"Layer id: {uid} - error no data received after all retries "
                        f"Last content is {last_content}",
                    status_code=last_status
                )

            # Probabilmente non entra mai qua
            else:
                raise SmartOCRException(
                    msg=f"Method {self.__class__.__name__}.{get_function_name()}: "
                        f"Layer id: {uid} - ERROR: No Data Received after all retries",
                )

        return output
