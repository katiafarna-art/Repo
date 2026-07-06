import io
import logging
from io import BytesIO
from typing import Literal
from core.exceptions import SmartOCRException
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from docling_core.types.doc import PictureItem
from core.models.entities.export.docling_manager import DoclingManager
from core.data.entities.utils_storage import save_file_on_bucket, get_presigned_url_from_bucket


class DoclingExporter:

    def __init__(self, task: Literal["text_export", "img_export", "table_export"]):
        self.cache_conversion = None
        self.task = task
        self.export_strategies = {
            "text_export": self._export_text_to_md,
            "table_export": self._export_tables_to_md,
            "img_export": self._export_images
        }

    @staticmethod
    def get_document_stream(file: bytes):
        stream = DocumentStream(**{"name": "def", "stream": BytesIO(initial_bytes=file)})
        return stream

    def convert(self, file: bytes):
        docl_manager = DoclingManager(task=self.task)
        pipelines = docl_manager.get_pipelines()
        format_options = docl_manager.get_format_options(pipelines=pipelines)

        converter = DocumentConverter(format_options=format_options)

        conversion_result = converter.convert(source=self.get_document_stream(file=file))
        self.cache_conversion = conversion_result

        return conversion_result

    def _export_text_to_md(self, file: bytes, **kwargs):
        conversion_result = self.convert(file=file)
        dct_output = dict()

        if not conversion_result.document.pages:
            return {"pag_1": conversion_result.document.export_to_markdown()}

        for i in range(len(conversion_result.document.pages)):
            dct_output.update({f"pag_{i + 1}": conversion_result.document.export_to_markdown(page_no=i + 1)})

        return dct_output

    def _export_tables_to_md(self, file: bytes, load_from_cache: bool = False, **kwargs):
        if load_from_cache and self.cache_conversion is not None:
            conversion_result = self.cache_conversion
        else:
            conversion_result = self.convert(file=file)

        table_dict = dict({f"pag_{i+1}": [] for i in range(len(conversion_result.document.pages))})

        # Export tables
        for table_ix, table in enumerate(conversion_result.document.tables):
            table_df = table.export_to_dataframe()
            table_dict[f"pag_{table.prov[0].page_no}"].append(table_df.to_markdown())

        return table_dict

    def _export_images(self, file: bytes, job_id: str, load_from_cache: bool = False, **kwargs):

        if load_from_cache and self.cache_conversion is not None:
            conversion_result = self.cache_conversion
        else:
            conversion_result = self.convert(file=file)

        picture_counter = 0
        img_dict = dict()
        for element, _level in conversion_result.document.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                img_path = f"{job_id}/exported_images"
                img_name = f"page_{element.prov[0].page_no}_image_{picture_counter}.png"

                max_retry = 10
                img_saved = False
                while max_retry and not img_saved:
                    buffer = io.BytesIO()

                    try:
                        element.get_image(conversion_result.document).save(buffer, format='PNG')

                    except Exception as e:
                        logging.error(f"Job-ID: {job_id}. Failed saving the image {img_name} on buffer: {e}. "
                                      f"Retrying...")
                        max_retry -= 1
                        continue

                    buffer.seek(0)

                    if save_file_on_bucket(file_name=img_name,
                                           input_file=buffer.getvalue(),
                                           s3_path=img_path):
                        img_url = get_presigned_url_from_bucket(file_path=f"{img_path}/{img_name}")
                        if img_url is None:
                            logging.error(f"Job-ID: {job_id}. "
                                          f"Failed generating the presigned-url for file {img_path}/{img_name}."
                                          f"Either the file does not exsist or an Error has occurred. Retrying...")
                            max_retry -= 1
                            continue

                        img_dict[img_name] = img_url
                        img_saved = True

                    else:
                        logging.error(f"Job-ID: {job_id}. "
                                      f"Failed saving the image {img_path}/{img_name} on bucket. Retrying...")
                        max_retry -= 1
                        continue

                if not max_retry:
                    raise SmartOCRException(f"Job-ID: {job_id}. Failed saving image file after all retries.")

        return img_dict

    def export_elements(self, file: bytes, job_id: str):
        dct_elements = {"tables": self._export_tables_to_md(file=file),
                        "images": self._export_images(file=file, job_id=job_id, load_from_cache=True)}

        return dct_elements

    def export(self, file: bytes, job_id: str):
        if self.task not in self.export_strategies:
            raise ValueError(f"Unsupported task: {self.task}. Supported tasks are: {list(self.export_strategies.keys())}")

        return self.export_strategies[self.task](file=file, job_id=job_id) # noqa