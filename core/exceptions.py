"""SmartOCR custom exceptions suite"""


class SmartOCRException(Exception):
    """General exception directly raised or caught by SmartOCR"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"{self.__class__.__name__}  : ->  {self.msg}"


class SmartOCRInputError(SmartOCRException):
    """Input exception directly raised or caught by SmartOCR"""
    pass


class SmartOCRLayeraiException(SmartOCRException):
    """Exception imputable from LayerAI directly caught by SmartOCR"""

    def __init__(self, msg, status_code):
        self.msg = msg
        self.status_code = status_code


class SmartOCRInvalidOutputException(SmartOCRException):
    """Output exception directly raised or caught by SmartOCR"""
    pass


class SmartOCRDoclingException(SmartOCRException):
    """Exception imputable from LayerAI directly caught by SmartOCR"""

    pass
