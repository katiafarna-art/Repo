from pydantic import AfterValidator, UrlConstraints
from pydantic_core import Url
from pydantic.networks import validate_email
from typing_extensions import Annotated

def mail_validation(v):
    try:
        _, email = validate_email(v)
        return email
    except Exception as e:
        raise ValueError(f"Errore in fase di validazione mail {e}")

HttpUrl = Annotated[Url, UrlConstraints(
    max_length=2083, allowed_schemes=['http', 'https'])]
FileUrl = Annotated[Url, UrlConstraints(allowed_schemes=['file'])]
EmailStr = Annotated[str, AfterValidator(mail_validation)]