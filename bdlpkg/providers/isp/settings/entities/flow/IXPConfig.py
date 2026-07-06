from typing import Optional
from pydantic import BaseModel


class IXPS3Config(BaseModel):
    """
    Configuration mapping for S3 in IXP context.

    This class defines the configuration for S3 resources related to IXP, 
    including the input and output folders where files are transferred.

    :param s3_resource: The name of the S3 resource as defined within the microservice.
    :type s3_resource: Optional[str]
    :param s3_input_folder: The folder where files transferred from the IXP layer to S3 are stored.
    :type s3_input_folder: str
    :param s3_output_folder: The folder where files to be transferred from S3 to the IXP layer are stored.
    :type s3_output_folder: str
    """
    s3_resource: Optional[str] = None
    s3_input_folder: str
    s3_output_folder: str


class IXPSendConfig(BaseModel):
    """
    Configuration for the 'Send' operation in the IXP-S3 context.

    This class defines the configuration for sending data from IXP to S3, 
    including the S3 configuration and the local folder on the IXP layer where files are temporarily stored.

    :param s3_config: The base configuration for the IXP-S3 transfer route.
    :type s3_config: IXPS3Config
    :param ixp_output_folder: The folder on the IXP layer where files are temporarily stored before being sent to S3.
    :type ixp_output_folder: str
    """
    s3_config: IXPS3Config
    ixp_output_folder: str   


class IXPReceiveConfig(BaseModel):
    """
    Configuration for the 'Receive' operation in the IXP context (from external to BDL10).

    This class defines the configuration for receiving data from external sources to the IXP layer,
    including optional S3 configuration and an API callback.

    :param s3: Optional S3 configuration for the IXP transfer route.
    :type s3: Optional[IXPS3Config]
    :param api_callback: Optional callback URL for notifying the completion of the file reception.
    :type api_callback: Optional[str]
    """
    s3: Optional[IXPS3Config] = None
    api_callback: Optional[str] = None
