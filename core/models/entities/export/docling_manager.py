import os
from typing import Literal
from docling.datamodel.pipeline_options import PdfPipelineOptions, PaginatedPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    PdfFormatOption,
    ImageFormatOption,
    CsvFormatOption,
    ExcelFormatOption,
    WordFormatOption,
    PowerpointFormatOption,
    AsciiDocFormatOption,
    HTMLFormatOption
)

PATH_DOCLING_MODELS_LOCAL = os.environ["DOCLING_MODELS_DIR"] if "ISP_AMBIENTE" in os.environ else "./docling_models"


class DoclingManager:

    def __init__(self, task: Literal["text_export", "img_export", "table_export"]):
        self.task = task
        self.pipeline = {
            "text_export": self._get_text_export_pipelines(),
            "img_export": self._get_img_export_pipelines(),
            "table_export": self._get_table_export_pipelines()
        }

    @staticmethod
    def _get_text_export_pipelines():
        pdf_docl_pipeline = PdfPipelineOptions(artifacts_path=PATH_DOCLING_MODELS_LOCAL)
        generic_docl_pipeline = PaginatedPipelineOptions(artifacts_path=PATH_DOCLING_MODELS_LOCAL)

        docl_pipelines = {"pdf": pdf_docl_pipeline, "generic": generic_docl_pipeline}

        return docl_pipelines

    @staticmethod
    def _get_table_export_pipelines():
        pdf_docl_pipeline = PdfPipelineOptions(artifacts_path=PATH_DOCLING_MODELS_LOCAL)
        return {"pdf": pdf_docl_pipeline}

    @staticmethod
    def _get_img_export_pipelines():
        pdf_docl_pipeline = PdfPipelineOptions(artifacts_path=PATH_DOCLING_MODELS_LOCAL)
        pdf_docl_pipeline.generate_picture_images = True
        # pdf_docl_pipeline.images_scale = 1.0
        return {"pdf": pdf_docl_pipeline}

    def get_pipelines(self) -> dict:

        pipeline_getter = self.pipeline.get(self.task)

        if pipeline_getter is None:
            raise ValueError(
                f"Invalid task: {self.task}. Supported tasks are: 'text_export', 'img_export', 'table_export'."
            )

        return pipeline_getter

    def get_format_options(self, pipelines: dict):
        pdf_options = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipelines["pdf"])}

        if self.task != "text_export":
            return pdf_options

        other_options = {
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipelines["pdf"]),
            InputFormat.CSV: CsvFormatOption(pipeline_options=pipelines["generic"]),
            InputFormat.XLSX: ExcelFormatOption(pipeline_options=pipelines["generic"]),
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipelines["generic"]),
            InputFormat.PPTX: PowerpointFormatOption(pipeline_options=pipelines["generic"]),
            InputFormat.ASCIIDOC: AsciiDocFormatOption(pipeline_options=pipelines["generic"]),
            InputFormat.HTML: HTMLFormatOption(pipeline_options=pipelines["generic"]),
        }

        return {**pdf_options, **other_options}




