from typing import Optional
from core.exceptions import SmartOCRInputError
from core.routines.entities import get_function_name
from core.models.entities.export.docling_exporter import DoclingExporter
from core.exceptions import SmartOCRDoclingException


class MDTextExporter:

    def _extract_params(self, params: Optional[dict] = None):
        if not params:
            params = dict()

        docling_params = params.get("docling_params", dict())
        dct_out = dict()
        dct_out["docling_params"] = docling_params

        pdf_scanned = params.get("pdf_scanned", None)

        if pdf_scanned:
            if pdf_scanned not in {"True", "False"}:
                raise SmartOCRInputError(
                    f"Method {self.__class__.__name__}.{get_function_name()}: "
                    "Error in extracting configuration: if specified, 'pdf_scanned' must be of str-type and either "
                    "'True' or 'False'"
                )

            pdf_scanned = True if pdf_scanned.lower() == "true" else False # noqa
            dct_out.update({"pdf_scanned": pdf_scanned})

        return dct_out

    @staticmethod
    def postprocess_raw_output(raw_output: dict, params: dict = None):

        dct_out = dict()

        if "pdf_scanned" in params:
            params["pdf_scanned"] = str(params["pdf_scanned"])

        dct_out["texts"] = raw_output
        dct_out["extra"] = params

        return dct_out

    def export(
            self, file: bytes, params: Optional[dict] = None, job_id: Optional[str] = None, **kwargs # noqa
    ):

        extraction_to_md_params = self._extract_params(params)

        try:
            raw_output = DoclingExporter(task="text_export").export(file=file, job_id=job_id)

        except Exception as e:
            raise SmartOCRDoclingException(
                f"Func {get_function_name()}: Error {e}"
            )

        return self.postprocess_raw_output(raw_output=raw_output, params=extraction_to_md_params)
