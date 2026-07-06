import sys
from abc import ABC, abstractmethod
from core.data.services import get_pdf_len

# immagini: 30 s per mega
# pdf nativi: 5 s per pagina
# pdf non nativi: 60 s per pagina
# altro 3 s per mega


class EtaEvaluator(ABC):

    eta_default = 1

    def __init__(self, file_content: bytes):
        self.file = file_content

    @abstractmethod
    def evaluate_expected_eta(self):
        pass

    def evaluate_per_mega(self):
        return self.eta_default * sys.getsizeof(self.file) / 1000000.0

    def evaluate_per_page(self):
        return self.eta_default * get_pdf_len(self.file)


class EtaBasic(EtaEvaluator):

    eta_default = 3

    def evaluate_expected_eta(self):
        return super().evaluate_per_mega()


class EtaImage(EtaEvaluator):

    eta_default = 30

    def evaluate_expected_eta(self):
        return super().evaluate_per_mega()


class EtaNativePDF(EtaEvaluator):

    eta_default = 5

    def evaluate_expected_eta(self):
        return super().evaluate_per_page()


class EtaPDFScan(EtaEvaluator):

    eta_default = 60

    def evaluate_expected_eta(self):
        return super().evaluate_per_page()


dct_eta_evaluators = dict()
dct_eta_evaluators["basic"] = EtaBasic
dct_eta_evaluators["image"] = EtaImage
dct_eta_evaluators["native_pdf"] = EtaNativePDF
dct_eta_evaluators["scanned_pdf"] = EtaPDFScan
