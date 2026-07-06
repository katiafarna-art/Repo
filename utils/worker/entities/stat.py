from pydantic import BaseModel

class Stats(BaseModel):
    """
    Stat
    statistics about a jobs
    """
    jobs_total:int 
    jobs_alive:int
