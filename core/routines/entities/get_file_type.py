"""Utility function for checking file-type from its byte content"""

import mimetypes
from filetype import filetype
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRException


def check_file_type(file_content: bytes) -> str:

    kind = filetype.guess(file_content)
    mime_type = kind.mime

    try:
        output = mimetypes.guess_extension(mime_type)

    except Exception as e:
        raise SmartOCRException(
            f"Func {get_function_name()}: exception in inferring file type - > {e}"
        )

    return output
