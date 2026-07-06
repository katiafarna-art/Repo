import os
from typing import List, Optional
from logging import basicConfig
from multiprocessing import Process
from bdlpkg.utils.metaclasses.singleton import Singleton


class JobManager(metaclass=Singleton):

    #https://docs.python.org/3.6/library/multiprocessing.html

    def __init__(self) -> None:
        self._jobs = {}

    def new_job(self,
                job_name: str,
                job_target: object,
                job_args: tuple = (),
                execution_mode: str = "localhost",
                start_now: bool = False) -> None:
        if job_name not in self._jobs:
            self._jobs[job_name] = {
                "job_target": job_target,
                "execution_mode": execution_mode,
                "job_args": job_args,
                "job_process": None
            }
            if start_now:
                self.start_job(job_name)
        else:
            raise ValueError(f"the {job_name} existing, you cannot redefine it")

    def start_job(self, job_name: str) -> None:
        if job_name in self._jobs:
            _job = self._jobs[job_name]
            if _job["execution_mode"] == "localhost":
                self._start_process(job_name)
            else:
                raise NotImplementedError(
                    f"{ _job['execution_mode']} execution mode not implemented")

        else:
            raise ValueError(f"the {job_name} doen't exists")
        
    def end_job(self, job_name: str, hard: Optional[bool] = False) -> None:
        if job_name in self._jobs:
            _job = self._jobs[job_name]
            if _job["execution_mode"] == "localhost":
                self._end_process(job_name, hard)
            else:
                raise NotImplementedError(
                    f"{ _job['execution_mode']} execution mode not implemented")

        else:
            raise ValueError(f"the {job_name} doen't exists")

    @staticmethod
    def _launchpad(target,args,env=None):
        #TODO recuperare la configurazione del log dalle configurazioni
        basicConfig(format="%(asctime)s %(levelname)s [%(module)s] (%(threadName)s) (jm: %(processName)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S.000%z",
            level=env["LOG_LEVEL"])
        target(*args)

    def _start_process(self, job_name: str) -> bool:
        if job_name in self._jobs:
            _job = self._jobs[job_name]
            if _job["job_process"] is None or not _job["job_process"].is_alive():
                _job["job_process"] = Process(
                    name=f"{job_name}-{str(_job['job_target'].__name__)}",
                    target=JobManager()._launchpad,
                    args=(_job["job_target"], _job["job_args"],),
                    kwargs={'env':{'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO')}})
                _job["job_process"].start()
                if _job["job_process"].is_alive():
                    return True
        return False
    
    def _end_process(self, job_name: str, hard: Optional[bool] = False) -> bool:
        if job_name in self._jobs:
            _job = self._jobs[job_name]
            if _job["job_process"] is not None:
                if not hard:
                    _job["job_process"].terminate()
                else:
                    _job["job_process"].kill()
                return True
        return False

    def status_process(self, job_name: str) -> bool:
        if job_name in self._jobs:
            return self._jobs[job_name]["job_process"].is_alive()
        else:
            raise ValueError(f"the {job_name} doen't exists")

    def get_process_names(self) -> List[str]:
        """
        get_process_names

        :return: list of string (jobs names)
        :rtype: list(str)
        """
        return list(self._jobs.keys())

