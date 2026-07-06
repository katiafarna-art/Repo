from pydantic import BaseModel, Field


class FileBaseModel(BaseModel):
    filename: str = Field(..., examples=["filename.extension"])
    fullpath: str = Field(..., examples=["/tmp/filename.extension"])
    extension: str = Field(..., examples=["extension"])
