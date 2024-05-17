import json
import os

import uvicorn
from fastapi import FastAPI, UploadFile, Path, File, APIRouter, Depends, HTTPException, status, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, UJSONResponse
from starlette.responses import JSONResponse

HOST = os.getenv("HOST", '')
PORT = int(os.getenv("PORT", 0))
DOWNLOAD_DIR = os.path.dirname(os.getenv("DOWNLOAD_DIR", ''))

LOGIN = os.getenv("LOGIN", '')
PASSWORD = os.getenv("PASSWORD", '')

app = FastAPI(
    title="File Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    default_response_class=UJSONResponse,
)
security = HTTPBasic()

files_router = APIRouter()

templates = Jinja2Templates(directory="templates")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == LOGIN
    correct_password = credentials.password == PASSWORD
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def create_folder(workspace, folder):
    path = os.path.join(workspace, folder)
    if not os.path.exists(path):
        os.makedirs(path)
        print("create folder with path {0}".format(path))
    else:
        print("folder exists {0}".format(path))

    return path


@app.get("/openapi.json", response_class=JSONResponse)
async def get_openapi_json(current_user: str = Depends(verify_credentials)) -> JSONResponse:
    openapi_schema = get_openapi(
        title="File server",
        version="2.0.0",
        openapi_version="3.0.0",
        description="API documentation",
        routes=app.routes,
    )
    return JSONResponse(openapi_schema)


@app.get("/docs", response_class=HTMLResponse)
async def get_docs(username: str = Depends(verify_credentials)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs", swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/swagger-ui-bundle.js")


@app.get("/redoc", response_class=HTMLResponse)
async def get_redoc(username: str = Depends(verify_credentials)) -> HTMLResponse:
    return get_redoc_html(openapi_url="/openapi.json", title="redoc")


@files_router.post("/upload-file/{file_path:path}")
async def upload_file(file_path: str = Path(..., description="The path of the file"), file: UploadFile = File(...),
                      _: str = Depends(verify_credentials), response_class=JSONResponse):
    try:
        path = create_folder(DOWNLOAD_DIR, file_path)
        if not path.startswith(DOWNLOAD_DIR):
            return json.dumps({"status": "Failed: wrong filepath"})

        file_path = os.path.join(str(path), file.filename)

        with open(file_path, 'wb') as out_file:
            out_file.write(file.file.read())

    except Exception as ex:
        print(ex)

    return json.dumps({"status": "Success"})


@files_router.get(path='/get-file/{file_path:path}', response_class=HTMLResponse)
async def get_file(request: Request, file_path: str = Path(..., description="The path of the file")):
    if not file_path:
        return templates.TemplateResponse(request=request, name='files.html',
                                          context={'files_path': [], 'base_path': file_path,
                                                   'error': 'Directory doesnot set'})

    try:
        if not os.path.join(DOWNLOAD_DIR, file_path).startswith(DOWNLOAD_DIR):
            return templates.TemplateResponse(request=request, name='files.html',
                                              context={'files_path': [], 'base_path': file_path,
                                                       'error': 'Directory set wrong'})

        if file_path[-1] != '/':
            file_path += '/'

        if file_path.endswith('.html/'):
            with open(os.path.join(DOWNLOAD_DIR, file_path[:-1]), 'r') as html:
                file_data = html.read()
            return file_data

        onlyfiles = [f for f in os.listdir(os.path.join(DOWNLOAD_DIR, file_path))]
        onlyfiles.append('..')
        onlyfiles = onlyfiles[::-1]

        return templates.TemplateResponse(request=request, name='files.html',
                                          context={'files_path': onlyfiles, 'base_path': file_path,
                                                   'error': ''})  # FileResponse(path=str(path), filename=str(path))
    except Exception as ex:
        return templates.TemplateResponse(request=request, name='files.html',
                                          context={'files_path': [], 'base_path': file_path, 'error': ex})


app.include_router(files_router, prefix='/files')

if __name__ == '__main__':
    if LOGIN == '':
        raise Exception("LOGIN not set")

    if PASSWORD == '':
        raise Exception("PASSWORD not set")

    if HOST == '':
        raise Exception("HOST not set")

    if PORT == 0:
        raise Exception("PORT not set")

    if DOWNLOAD_DIR == '':
        raise Exception("DOWNLOAD_DIR not set")

    uvicorn.run(app, host=HOST, port=PORT)
