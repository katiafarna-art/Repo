from pydantic import BaseModel, Field


class IXPRequest(BaseModel):
    """
    A model representing file information for IXP (data exchange platform) requests.

    This class defines the structure of a request related to file upload or transfer,
    including details about the file's name, chunked parts, and integrity verification through SHA.

    :param filename: The name of the file being processed.
    :type filename: str
    :param chunk_filename: The name of the file chunk, used for chunked uploads.
    :type chunk_filename: str
    :param sha: The SHA hash for verifying the integrity of the file or chunk.
    :type sha: str
    :param total_parts: The total number of parts in a chunked upload.
    :type total_parts: str
    :param part_number: The part number of the current chunk in a chunked upload.
    :type part_number: str
    """
    filename: str = Field(...)
    chunk_filename: str = Field(...)
    sha: str = Field(...)
    total_parts: str = Field(...)
    part_number: str = Field(...)
