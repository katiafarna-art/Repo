#https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
from typing import Any


class Singleton(type):
    """The singleton is a creational design pattern whose purpose is to ensure 
    that of a given class is created one and only one instance, and to provide 
    a global access point to that instance. 
    """
    _instances: dict = {}

    def __call__(cls, *args: list, **kwargs: dict) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NamedSingleton(type):
    """The singleton is a creational design pattern whose purpose is to ensure 
    that of a given class is created one and only one instance, and to provide 
    a global access point to that instance. 
    In this case, a Singleton for each __name__ is created.
    """
    _instances: dict = {}

    def __call__(cls, *args: list, **kwargs: dict) -> Any:
        _cls_name = f"{cls.__name__}-{args[0]}"
        if _cls_name not in cls._instances:
            cls._instances[_cls_name] = super(NamedSingleton,
                                              cls).__call__(*args, **kwargs)
        else:
            cls._instances[_cls_name].__init__(*args, **kwargs)
        return cls._instances[_cls_name]