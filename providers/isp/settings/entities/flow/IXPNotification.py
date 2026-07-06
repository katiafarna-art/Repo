from typing import List, Optional, Union
from pydantic import BaseModel, EmailStr


class EmailConfig(BaseModel):
    """
    Configuration for sending an email.

    This class defines the structure of an email configuration, including recipients, subject, 
    content, and optional headers, footers, and mail instance names.

    :param to: The email recipient(s), can be a single email address or a list of email addresses.
    :type to: Union[EmailStr, List[EmailStr]]
    :param subject: The subject of the email.
    :type subject: str
    :param content: The main content of the email.
    :type content: str
    :param header: Optional header to be included at the top of the email. Defaults to "Saluti dal BDL".
    :type header: Optional[str]
    :param footer: Optional footer to be included at the bottom of the email. Defaults to "Mail from".
    :type footer: Optional[str]
    :param mail_istance_name: Optional name of the mail instance, useful for identifying different email services or configurations.
    :type mail_istance_name: Optional[str]
    """
    to: Union[EmailStr, List[EmailStr]]
    subject: str
    content: str
    header: Optional[str] = "Saluti dal BDL"
    footer: Optional[str] = "Mail from"
    mail_istance_name: Optional[str] = None