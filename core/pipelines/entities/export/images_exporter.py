from core.routines.entities import get_function_name
from core.models.entities.export.docling_exporter import DoclingExporter
from core.exceptions import SmartOCRDoclingException


class ImagesExporter:

    def _postprocess_output(
            self, raw_output: dict
    ) -> dict:

        dct_out = {"images": raw_output,
                   "extra": dict()}
        return dct_out

    def export(self, file: bytes, job_id:str, **kwargs): # noqa

        try:
            raw_output = DoclingExporter(task="img_export").export(file=file, job_id=job_id)

        except Exception as e:
            raise SmartOCRDoclingException(
                f"Func {get_function_name()}: Error {e}"
            )

        return self._postprocess_output(raw_output)
