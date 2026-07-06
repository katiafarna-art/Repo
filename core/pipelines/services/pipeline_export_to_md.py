import logging
from typing import Optional, Literal
from config.parameters import ETA_PAGE_DEFAULT
from core.routines.services import track_and_save_results
from core.pipelines.entities.export import *

EXPORT_PIPELINES = {
    "text_export": MDTextExporter(),
    "table_export": MDTablesExporter(),
    "img_export": ImagesExporter(),
    "element_export": ElementsExporter()
}


def export_to_md(file,
                 task: Literal["text_export", "img_export", "table_export", "element_export"],
                 params: dict = None,
                 job_id: Optional[str] = None,
                 expected_eta: Optional[float] = ETA_PAGE_DEFAULT):

    logging.info(f"Starting markdown extraction from file")
    exporter = EXPORT_PIPELINES.get(task)

    func_kwargs = {
        "file": file,
        "params": params,
        "job_id": job_id
    }

    return track_and_save_results(
        callable_func=exporter.export,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta
    )
