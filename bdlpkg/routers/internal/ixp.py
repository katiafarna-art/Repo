# coding: utf-8
import json
import os
import shutil
import zipfile
from typing import Dict
import httpx

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Response,
                     UploadFile, BackgroundTasks, status)
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from bdlpkg.providers.isp.settings.entities.flow.IXPRequest import IXPRequest
from bdlpkg.providers.isp.settings.entities.flow.IXPConfig import (IXPReceiveConfig,
                                                  IXPS3Config, IXPSendConfig)
from bdlpkg.providers.isp.settings.entities.flow.IXPNotification import EmailConfig
from bdlpkg.providers.isp.flows.services.ixpEngine import (generate_random_string, merge_files,
                                                   list_file_to_send, save_files,
                                                   split_file, start_job_download, sha256_generation)
from starlette.responses import FileResponse

from bdlpkg.providers.isp.messaging.services.mail import send_mail
from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
from bdlpkg.utils.bdlfile.services.bdlfile import get_obj_from_config_path
from bdlpkg.utils.worker.services.job import JobManager

IXP_TMP_FOLDER = "temp/ixp/"
HIDDEN_APIs = True # set false to hidden apis

router = APIRouter(default_response_class=JSONResponse)

job = JobManager()

temp_dir = './temp'
out_dir = './output'
task_status: Dict[str, str] = {}

######API per gestione flusso RECEIVE "ext 2 BDL10"######
def get_request(filename: str = Form(...),
                chunk_filename: str = Form(...),
                sha: str = Form(...),
                total_parts: str = Form(...),
                part_number: str = Form(...)) -> IXPRequest:
    return IXPRequest(filename=filename,
                      chunk_filename=chunk_filename,
                      sha=sha,
                      total_parts=total_parts,
                      part_number=part_number)


def get_receive_config(config_name: str = Form(...)) -> IXPReceiveConfig:
    obj = get_obj_from_config_path(os.path.join("ixp", "config.yaml"))
    return IXPReceiveConfig(s3=obj[config_name]['s3'],
                            api_callback=obj[config_name]['api_callback'])


@router.post("/save_ixp", status_code=200, include_in_schema=HIDDEN_APIs)
async def save_file(item: UploadFile = File(...),
                    request: IXPRequest = Depends(get_request)) -> dict[str, str]:
    # 1. Legge il file caricato
    file = await item.read()

    # 2. Salva il file nella directory temporanea
    save_files(file, request.chunk_filename, temp_dir)

    # 3. Se il file è stato diviso in più parti
    if int(request.total_parts) > 1:
        # 3.1. Se questa è l'ultima parte del file, unisci tutte le parti
        if int(request.part_number) == int(request.total_parts):
            # 3.1.1. Unisci tutte le parti
            merge_files(request.filename, temp_dir)
        # 3.2. Se questa non è l'ultima parte del file, aspetta le altre parti
        else:
            return {"status": f"{request.filename} chunk sent"}

    unzipped_filepath = os.path.join(temp_dir, request.filename)
    zip_file_path = f"{unzipped_filepath}.zip"

    # 4. Estrai il file zip
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # 5. Genera lo sha256 del file
    received_file_sha = sha256_generation(unzipped_filepath)

    # 6. Controlla che lo sha256 del file ricevuto corrisponda a quello inviato
    if request.sha == received_file_sha:
        return {"status": f"{request.filename} sent"}        
    else:
        raise HTTPException(status_code=422,
                            detail="sha256 not matching, cannot send file")
    

def send_file(filename: str,
              rcv_config: IXPReceiveConfig,
              task_id: str):
    # Funzione per eseguire il task di invio del file su S3
    task_status[task_id] = "In esecuzione"
    bm = BucketManager()
    try:
        response = bm.upload_file_from_path(
                    file_path=os.path.join(temp_dir, filename),
                    resource_name=rcv_config.s3.s3_resource,
                    destination_path=rcv_config.s3.s3_input_folder)
    except Exception as e:
            raise HTTPException(status_code=404,
                                detail=str(e))
    if response:
        shutil.rmtree(temp_dir)
        task_status[task_id] = "Terminato"
        if rcv_config.api_callback:
            job.new_job(
                job_name=f"callback_{task_id}",
                job_target=call_api_callback,
                job_args=(rcv_config.api_callback, filename),
                start_now=True
            )
    else:
        raise HTTPException(status_code=430, detail="file not sent")


def call_api_callback(api_callback: str, filename: str):
    port = os.getenv("BIND", ":8080").split(":")[1]
    url = f"http://localhost:{port}{api_callback}"
    try:
        httpx.get(url, params={"file_name": filename})
    except Exception as e:
        print(f"Errore nella chiamata API di callback: {e}")


@router.post("/upload_ixp", status_code=200)
async def upload_to_endpoint(background_tasks: BackgroundTasks, 
                             filename: str = Form(...),
                             rcv_config: IXPReceiveConfig = Depends(get_receive_config)):
    task_id = generate_random_string(10)
    background_tasks.add_task(send_file,filename,rcv_config,task_id)    #background task to file sending
    output = {"task_id": task_id, "message": "Task in the background"}
    return json.dumps(output)


@router.get("/task_status", status_code=202)
async def get_task_status(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="task not found")
    if task_status[task_id] == "Terminato":
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"detail": "OK"})
    

######API per gestione flusso SEND "BDL10 2 ext"######
def get_send_config(config_name: str = Form(...)) -> IXPSendConfig:
    # Carica il contenuto del file YAML nel dizionario obj.
    obj = get_obj_from_config_path(os.path.join("ixp", "config.yaml"))

    s3_config = IXPS3Config(
        s3_resource=obj[config_name]['s3']['s3_resource'],
        s3_input_folder=obj[config_name]['s3']['s3_input_folder'],
        s3_output_folder=obj[config_name]['s3']['s3_output_folder'])

    return IXPSendConfig(s3_config=s3_config,
                         ixp_output_folder=obj[config_name]['ixp_output_folder'])


@router.post("/submit_request_download",
             status_code=200, include_in_schema=HIDDEN_APIs)    # mettere status code adeguato
async def submit_request_download(s3_config: IXPSendConfig = Depends(
    get_send_config)) -> str:

    # Ottieni la lista dei file per ogni configurazione
    return json.dumps(list_file_to_send(s3_config))


@router.post("/job_files_action",
             status_code=200, include_in_schema=HIDDEN_APIs)    # mettere status code adeguato
async def job_files_action(s3_config: IXPSendConfig = Depends(
    get_send_config)) -> str:
    uuid = generate_random_string(10)
    job.new_job(job_name=uuid,
                job_target=list_file_to_send,
                job_args=(
                    s3_config,
                    True,
                    uuid,
                ),
                start_now=True)
    return str(uuid)


@router.post("/job_files_status",
             status_code=200, include_in_schema=HIDDEN_APIs)    # mettere status code adeguato
async def job_files_status(
    response: Response,
    s3_config: IXPSendConfig = Depends(get_send_config),
    uuid: str = Form(...)
    ):
    try:
        status = job.status_process(uuid)
    except ValueError:
        response.status_code = 404
        return {"status": "Not found"}
    
    if not status:
        bm = BucketManager()
        byte_stream = bm.download_file_in_memory(f"{uuid}.json",s3_config.s3_config.s3_resource)
        bm.delete_file(f"{uuid}.json",s3_config.s3_config.s3_resource)
    
        return json.dumps(json.load(byte_stream))


@router.post("/job_action", status_code=200, include_in_schema=HIDDEN_APIs)
async def job_action(filepath: str = Form(...),
                     s3_resource: str = Form(...)) -> str:
    uuid = generate_random_string(10)
    job.new_job(job_name=uuid,
                job_target=start_job_download,
                job_args=(
                    filepath,
                    s3_resource,
                    uuid,
                ),
                start_now=True)
    return str(uuid)


@router.post("/job_status", status_code=200, include_in_schema=HIDDEN_APIs)
async def job_status(
    response: Response, uuid: str = Form(...),
    filename: str = Form(...)) -> dict:
    filepath = os.path.join(IXP_TMP_FOLDER, uuid, filename)

    try:
        status = job.status_process(uuid)
    except ValueError:
        response.status_code = 404
        return {"status": "Not found"}

    if not status:
        filesha = sha256_generation(filepath)
        total_parts = split_file(filepath)
        return {
            "status": "done",
            "total_parts": total_parts,
            "sha": filesha
        }    # output da definire del config.yaml?

    return {"status": "alive"}


@router.post("/download_file", status_code=200, include_in_schema=HIDDEN_APIs)
async def download_file(uuid: str = Form(default=""),
                        filename: str = Form(...)) -> FileResponse:
    filepath = os.path.join(IXP_TMP_FOLDER, uuid, filename)

    return FileResponse(filepath)


@router.delete("/delete_file", status_code=204, include_in_schema=HIDDEN_APIs)
async def delete_file(
    response: Response,
    uuid: str = Form(default=""),
    s3_folder_path: str = Form(...)
) -> None:
    filepath = os.path.join(IXP_TMP_FOLDER, uuid)
    bucket_manager = BucketManager()

    deletion = bucket_manager.delete_file(s3_folder_path)

    if deletion and os.path.exists(filepath):
        shutil.rmtree(filepath)

    response.status_code = 204 if deletion else 411


def get_notification_config(request_name: str = Form(...)) -> EmailConfig:
    obj = get_obj_from_config_path(os.path.join("ixp", "notification.yaml"))
    return EmailConfig.model_validate(obj[request_name])


@router.post("/notify_users", status_code=200, include_in_schema=HIDDEN_APIs)
async def notify_users(mail_config: EmailConfig = Depends(get_notification_config), 
                       custom_msg: str = Form(default="")) -> None:
    try:
        send_mail(to=mail_config.to, subject=mail_config.subject, content=f"{mail_config.content}\n\n{custom_msg}",
                  header=mail_config.header, footer=mail_config.footer, mail_istance_name= mail_config.mail_istance_name)
    except Exception as e:
            raise HTTPException(status_code=500,
                                detail=str(e))