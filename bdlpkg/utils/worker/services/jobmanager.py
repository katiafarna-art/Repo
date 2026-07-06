from typing import List, Union, Optional
from bdlpkg.utils.worker.services.job import JobManager
from bdlpkg.utils.worker.entities.stat import Stats
from bdlpkg.utils.worker.entities.info import Job
import re


def jm_alives() -> List[str]:
    _jm = JobManager()
    _jm_jobs = []
    for _job in _jm.get_process_names():
        if _jm.status_process(_job):
            _jm_jobs.append(_job)
    return _jm_jobs


def jm_stats() -> Stats:
    _jm = JobManager()
    return Stats(jobs_total=len(_jm.get_process_names()),jobs_alive=len(jm_alives()))

def jm_info(name:str) -> Job:
    _jm = JobManager()
    try:
        _is_alive = _jm.status_process(name)
    except ValueError:
        return None
    return Job(name=name,status="RUNNING" if _is_alive else "TERMINATE")

def jm_info_group(regex:str) -> List[Job]:
    _r = []
    _jm = JobManager()
    jobs_group = [job_name for job_name in _jm.get_process_names() if re.search(regex, job_name)]
    for _job in jobs_group:
        _r.append(jm_info(_job))
    return _r

def jm_info_all() -> List[Job]:
    _r = []
    _jm = JobManager()
    for _job in _jm.get_process_names():
        _r.append(jm_info(_job))
    return _r

def jm_delete(name:str, hard:Optional[bool]=False) -> None:
    _jm = JobManager()
    _jm.end_job(name, hard)
    _jm._jobs.pop(name)

def jm_delete_group(regex:str, hard:Optional[bool]=False) -> None:
    _jm = JobManager()
    jobs_group = [job_name for job_name in _jm.get_process_names() if re.search(regex, job_name)]
    for _job in jobs_group:
        jm_delete(_job, hard)

def jm_delete_all(hard:Optional[bool]=False) -> None:
    _jm = JobManager()
    for _job in _jm.get_process_names():
        jm_delete(_job, hard)
