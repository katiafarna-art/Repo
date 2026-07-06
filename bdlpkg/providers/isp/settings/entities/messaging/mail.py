from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings
from bdlpkg.utils.bdlfile.entities.annotated import EmailStr


class MailSettings(BaseSettings):
    """
    This class handles the configuration details required to send emails using an SMTP server, 
    including the server's host and port, authentication credentials, and sender email address.

    :param mail_smtp_server_host: The hostname of the SMTP server (default is "smtp.intesasanpaolo.com").
    :type mail_smtp_server_host: str
    :param mail_smtp_server_port: The port of the SMTP server (default is 25).
    :type mail_smtp_server_port: int
    :param mail_username: The username used for SMTP server authentication.
    :type mail_username: str
    :param mail_password: The password used for SMTP server authentication, stored as a SecretStr.
    :type mail_password: SecretStr
    :param mail_address: The email address of the sender.
    :type mail_address: EmailStr
    :param resource_name: The name of the email resource being configured.
    :type resource_name: str
    :param authenticated: A flag indicating whether authentication is required (default is True).
    :type authenticated: bool
    """
    mail_smtp_server_host: str = Field("smtp.intesasanpaolo.com")
    mail_smtp_server_port: int = Field(25)
    mail_username: str
    mail_password: SecretStr
    mail_address: EmailStr
    resource_name: str
    authenticated: bool = Field(True)
