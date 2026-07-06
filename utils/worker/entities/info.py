from pydantic import BaseModel

class Job(BaseModel):
    """
    Stat
    statistics about a jobs
    """
    name: str
    status: str
