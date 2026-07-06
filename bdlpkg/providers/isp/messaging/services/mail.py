import smtplib
from datetime import datetime
import pytz
from typing import Union, List, Optional
from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings
from bdlpkg.providers.isp.settings.entities.messaging.mail import MailSettings
from bdlpkg.utils.health.services.healthcheck import healthcheck
from email.message import EmailMessage
from email import encoders
from email.mime.base import MIMEBase
from email.utils import make_msgid
import os



def get_mail_client(mail_istance_name: Optional[str] = None) -> smtplib.SMTP:
    """Initialize connection to SMTP server

    :param mail_istance_name: Mail istance name, defaults to None
    :type mail_istance_name: str, optional   
    :return: an object that handles the connection to SMTP server
    :rtype: smtplib.SMTP
    """

    mi: MailSettings = get_datasource_settings("mail", None, mail_istance_name)
    client = smtplib.SMTP()
    client.connect(host=mi.mail_smtp_server_host, port=mi.mail_smtp_server_port)

    if mi.authenticated:
        client.login(user=mi.mail_username,
                     password=mi.mail_password.get_secret_value())

    return client


def send_mail(
        to: Union[str, List[str]],
        subject: str,
        content: str,
        header: str = "Saluti dal BDL",    #inserimento header
        footer: str = "Mail from",    #inserimento footer
        mail_istance_name: Optional[str] = None,
        attachments: Optional[List[str]] = None) -> None:
    """Send an e-mail

    :param to: receiver or list of receivers
    :type to: str or str list
    :param subject: e-mail subject
    :type subject: 
    :param content: e-mail content
    :type content: str
    :param header: e-mail header, filled with a default text
    :type header: str
    :param footer: e-mail footer, filled with a default text
    :type footer: str
    :param mail_istance_name: Mail istance name, defaults to None
    :type mail_istance_name: str, optional
    :param attachments: List of file paths to attach, defaults to None
    :type attachments: List[str], optional
    """

    with get_mail_client(mail_istance_name) as client:

        mi: MailSettings = get_datasource_settings("mail", None,
                                                   mail_istance_name)
        project = healthcheck()["title"]
        version = healthcheck()["version"]
        hostname = healthcheck()["hostname"]

        msg = EmailMessage()
        msg['From'] = f"{hostname} <{mi.mail_address}>"
        msg['To'] = to

        msg['Subject'] = f"[{project}] - {subject}"

        header = f"{datetime.now(pytz.timezone('Europe/Rome')).strftime('%d/%m/%Y %H:%M:%S')} - {header}"
        footer = f"{footer} {hostname} of project {project} ({version})"
        body = f"{header}\n\n{content}\n\n{footer}"
        msg.set_content(body)

        #Gestione allegati
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(filepath)
                        maintype, subtype = ('application', 'octet-stream')

                        # Aggiunta allegato
                        file_mime = MIMEBase(maintype, subtype)
                        file_mime.set_payload(file_data)
                        encoders.encode_base64(file_mime)
                        file_mime.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
                        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
                else:
                    print(f"File {filepath} not found. Email not sent")
                    return

        client.send_message(msg)
