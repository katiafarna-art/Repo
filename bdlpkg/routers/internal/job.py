from typing import Union, List, Optional
from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from bdlpkg.utils.worker.entities.stat import Stats
from bdlpkg.utils.worker.entities.info import Job
from bdlpkg.utils.worker.services.jobmanager import jm_stats,jm_info,jm_info_group,jm_info_all,jm_delete,jm_delete_group,jm_delete_all

router = APIRouter(default_response_class=JSONResponse)

# demo APS scheduler
#https://apscheduler.readthedocs.io/en/3.x/userguide.html

#jm
#migrate from  https://bitbucket.intesasanpaolo.com/projects/BDL10/repos/cco-red/browse

@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Statistics",
    description="Retrieve stats about jobs",
)
def jm_stats_endpoint() -> Stats:
    return jm_stats()

@router.get(
    "/job/{job_name}",
    status_code=status.HTTP_200_OK,
    summary="Info about single job",
    description="Retrieve info about job"
)
def jm_get(job_name: Union[None,str]) -> Union[Job,List[Job]]:
    if job_name is not None:
        _j = jm_info(job_name)
        if _j is None:
            raise HTTPException(status_code=404, detail="Job not found")
        else:
            return _j
    else:
        raise HTTPException(status_code=400, detail="Invalid parameter")
    
@router.get(
    "/jobs/{regex}",
    status_code=status.HTTP_200_OK,
    summary="Info about jobs group",
    description="Retrieve info about a group of jobs according to a regex"
)
def jm_get_group(regex: Union[None,str]) -> Union[Job,List[Job]]:
    if regex is not None:
        _l_j = jm_info_group(regex)
        if len(_l_j) > 0:
            return _l_j
        else:
            raise HTTPException(status_code=404, detail="Jobs not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid parameter")
        
@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    summary="Info about all jobs",
    description="Retrieve info about all jobs"
)
def jm_get_all() -> Union[Job,List[Job]]:
    _l_j = jm_info_all()
    if len(_l_j) > 0:
        return _l_j
    else:
        raise HTTPException(status_code=404, detail="Jobs not found")

@router.put(
    "/{job_name}",
    status_code=status.HTTP_201_CREATED,
    summary="New job",
    description="Create a new job"
)
def jm_new(job_name: Union[None,str]) -> Job:
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.delete(
    "/job/{job_name}",
    status_code=status.HTTP_200_OK,
    summary="Delete job",
    description="Delete a job"
)
def jm_delete_endpoint(job_name:str, hard: Optional[bool] = False) -> Job:
    if job_name is not None:
        _j = jm_info(job_name)
        if _j is None:
            raise HTTPException(status_code=404, detail="Job not found")
        else:
            jm_delete(job_name, hard)
            return Job(name=job_name,status="DELETED")
    else:
        raise HTTPException(status_code=400, detail="Invalid parameter")
    
@router.delete(
    "/jobs/{regex}",
    status_code=status.HTTP_200_OK,
    summary="Delete jobs group",
    description="Delete a group of jobs according to a regex"
)
def jm_delete_group_endpoint(regex:str, hard: Optional[bool] = False) -> Union[Job,List[Job]]:
    if regex is not None:
        _l_j = [c.name for c in jm_info_group(regex)]   
        if len(_l_j) > 0:
            _r = []
            jm_delete_group(regex, hard)
            for _j in _l_j:
                _r.append(Job(name=_j,status="DELETED"))
            return _r
        else:
            raise HTTPException(status_code=404, detail="Jobs not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid parameter")
   
@router.delete(
    "/all",
    status_code=status.HTTP_200_OK,
    summary="Delete all jobs",
    description="Delete existing jobs"
)
def jm_delete_all_endpoint(hard: Optional[bool] = False) -> Union[Job,List[Job]]:
    _l_j = [c.name for c in jm_info_all()]   
    if len(_l_j) > 0:
        _r = []
        jm_delete_all(hard)
        for _j in _l_j:
            _r.append(Job(name=_j,status="DELETED"))
        return _r
    else:
        raise HTTPException(status_code=404, detail="Jobs not found")
