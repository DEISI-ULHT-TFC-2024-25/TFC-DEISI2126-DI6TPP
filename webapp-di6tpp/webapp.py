# 1. Standard library
import uvicorn
import logging
import settings
import os
import subprocess
import jwt
import time, uuid
import asyncio

# 2. Third-party libraries
from fastapi import FastAPI, Request, Response,HTTPException,status,Depends,status, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware import Middleware
from sqlalchemy.orm import Session
from jwt import exceptions as jwt_exceptions
from typing import Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# 3. Local application imports
from create_vm import create_vm_entry,generate_vm,configure_vm
from attack import iniciate_the_attack
from get_webapp_config import get_webapp_config
from data_model.routers import users,vms
from data_model.database import get_mariadb, SessionLocal
from data_model import crud,security,models,schemas
from data_model.routers.users import get_current_user
from task_manager import TaskManager,TaskStatus, create_task, update_task, get_task
from data_model.crud import ValidationException

webapp_config = get_webapp_config()
LOG_LEVEL = webapp_config.get("log_level", "info")
PORT = webapp_config.get("port", 8081)

task_manager = TaskManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #executed when the app starts
    task_manager.start_workers()
    yield
    #executed when the app stops to stop the workers
    task_manager.shutdown()
    

def verify_session_and_activity(db, access_token):
    session = crud.get_sessions_by_field(db, "token", access_token)
    if not session or session.logout_timestamp is not None:
        logger.info("Sessão inválida ou já finalizada")
        return RedirectResponse("/login", status_code=302)

    now = datetime.utcnow()
    if session.last_activity is None:
        session.last_activity = now  # new session, set last_activity to now if they didnt had any

    inactivity_time = now - session.last_activity
    minimum_time= timedelta(minutes=20)#20 minutes of inactivity
    if inactivity_time > minimum_time:
        logger.info(f"Usuário inativo por mais de {minimum_time}, redirecionando para login")
        return True

    # Update last_activity to now because the user is active
    session.last_activity = now

    return False

#quando é chamado, verifica se o usuário está logado e se a sessão é válida seminte
class SessionActivityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_sessionmaker):
        super().__init__(app)
        self.db_sessionmaker = db_sessionmaker

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Ignorar paths públicos, ex: login, static, docs
        if path.startswith("/login") or path.startswith("/docs") or path.startswith("/static"):
            return await call_next(request)
        
        logger.info(f"Verificando sessão e atividade para o path: {path}")
        access_token = request.cookies.get("access_token")
        if not access_token:
            logger.info("Token ausente")
            return RedirectResponse("/login", status_code=302)

        db = self.db_sessionmaker()
        try:
            payload = users.verify_token(access_token)
            if not payload:
                logger.info("Token inválido ou expirado")
                return RedirectResponse("/login", status_code=302)

            output_session_closed=verify_session_and_activity(db, access_token)
            logger.info(f"output_session closed: {output_session_closed}")
            if output_session_closed is True:
                logger.info("Sessão inválida ou inativa, redirecionando para login")
                return RedirectResponse("/login", status_code=302)
        except HTTPException as e:
            logger.error(f"Erro de autenticação: {e.detail}")
            return Response(e.detail, status_code=e.status_code)

        finally:
            db.close()    
        return await call_next(request)


app = FastAPI(lifespan=lifespan , middleware=[
        Middleware(SessionActivityMiddleware, db_sessionmaker=SessionLocal)
    ])

logger = logging.getLogger('uvicorn.error')

#to have the database information retrieved to the requests
app.include_router(users.router, tags=["User Management"])
app.include_router(vms.router, tags=["VMS Management"])

#to be sure that the directory is the correct
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# static folder is for create CSS, JS, imagens, etc.
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")



# validation errors with query param is invalid
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # If the call is made with fetch(), it answers with JSON becuase with only html it would give a silent error
    if request.headers.get("content-type") == "application/json":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()}
        )
    
    # otherwise, it answers with HTML
    return templates.TemplateResponse(
        "error_page.html",
        {
            "request": request,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "Unprocessable Entity – Validation failed"
        },
        status_code=422
    )

#to handle any raise http exception  raise HTTPException(...) made by me in routes
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # if it is on API call
    if request.headers.get("content-type") == "application/json":
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )   
    # direct acess on web route
    return templates.TemplateResponse(
        "error_page.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )
 #404 or automatic error from framework    
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        "error_page.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )
    
def get_current_user_redirect(request: Request, db=Depends(get_mariadb), access_token: str = Cookie(None)) -> models.User | None:
    try:
        current_user = get_current_user(request, db, access_token)
        logger.info(f"acabei o current_user: {current_user}")
        return current_user
    
    except HTTPException as e:
        # if it gets a 401 error → redirects to login page
        logger.info(f"going to redirect {e.status_code}")
        if e.status_code == 401:
            return None #redirect to login
        raise e  # other errors are raised
    
@app.post("/run-task")
async def run_task(request: Request, user = Depends(get_current_user_redirect)):
    user_id = request.headers.get(user.id)
    task_id = str(uuid.uuid4())
    create_task(task_id, user_id)

    def simulated_heavy_task():
        try:
            update_task(task_id, status=TaskStatus.RUNNING)
            time.sleep(10)
            update_task(task_id, status=TaskStatus.SUCCESS, result="Task complete.")
        except Exception as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))

    task_manager.add_task(simulated_heavy_task)
    return JSONResponse(content={"task_id": task_id})

@app.get("/task-status/{task_id}")
async def task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        return JSONResponse(content={"error": "Task not found"}, status_code=404)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
    }
    

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

class AdminAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # verify all /admin routes to restrict access
        if path.startswith("/admin"):
            
            #access token is passed is the cookie name safed 
            token = request.cookies.get("access_token")
                
            if not token:
                logger.info("No token provided")
                return RedirectResponse(url="/", status_code=302) 
             
            try:
                # Decode token to get the user role on payload
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_role = payload.get("role")
            except jwt_exceptions.InvalidTokenError:
                return RedirectResponse(url="/", status_code=302)   
            # Verify if the user role is "admin"
            if user_role != "admin":
                logger.info(f"User role: {user_role}")
                return RedirectResponse(url="/", status_code=302) 
        # if the route doesnt have /admin or admin, then skips it because it is excessible for everyone
        response = await call_next(request)
        return response

app.add_middleware(AdminAccessMiddleware)


#login part
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, response: Response, db= Depends(get_mariadb)):
    try:
        
        data = await request.json()
        
        #Login using API Token instead of username/password because it also prevents from CSRF
        username = data.get("username")
        password = data.get("password")
        logger.info(f"Received username: {username}")
        logger.info(f"Received password: {password}")
        
        if not password or not username:
            raise HTTPException(status_code=400, detail="Missing username or password")
        
        user = crud.get_user_by_field(db, 'username',username)
        logger.info(f"Received user: {user}")
        if not user or not security.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        proxmox_creds = crud.get_proxmox_credential_by_promoxid(db, user.proxmox_credentials_id)
        if proxmox_creds is None:
            raise HTTPException(status_code=401, detail="Proxmox token doesn't exist")
        
        valid_creds= await users.validate_proxmox_creds(proxmox_creds.proxmox_user,proxmox_creds.token_id, proxmox_creds.token_key )
        
        logger.info(f"proxmox creds valid {valid_creds}")
        
        if valid_creds is False:
            raise HTTPException(status_code=401, detail="Invalid Proxmox token")
                    
        token = users.create_user_access_token(user, db)
        logger.info(f"Token created: {token}")
        
        response = JSONResponse(content={"message": "Login successful!", "redirect": "/"}, status_code=200)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,     # not acessable throw JS (protect against XSS attacks)
            secure=True,       # it is only sent from HTTPS
            samesite="Lax", # only throw the same domain (protect against CSRF)
            max_age=1800       # Expires after 30 min as same as the token
        )
        

        return response
        
    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

@app.get("/logout")
def logout(
    request: Request,
    response: Response,
    db = Depends(get_mariadb),
    access_token: str = Cookie(None)
):
    logger.info("starting logout")
    # 1. if doesn't have token, cleans it and redirects
    if not access_token:
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("access_token")
        return response
    
    logger.info("session token on db to insert logout timestamp")
    # 2. Try to find the session token
    session = crud.get_sessions_by_field(db,"token", access_token)

    if session:
        session.logout_timestamp = datetime.utcnow()
        db.commit()

    # 3. Removes the cookie and redirects
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response



@app.get("/")
async def home(request: Request, db: Session = Depends(get_mariadb), current_user = Depends(get_current_user_redirect)):
    
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    if current_user.role == "admin":
        vms= crud.get_vms(db)
    else:
        vms=crud.get_user_vms(db, current_user.user_id)
    # this needs to be done because Jinja sense the object has relationships and more complex items it returns an object
    # that is not serializable
    # so we need to convert it to a dict
    vms_data = [vm.to_dict() for vm in vms]
    return templates.TemplateResponse("index.html", {"request": request, "title": "itrust6g","VMs":vms_data, "username": current_user.username})

#creatingvms
@app.get("/create-vm")
async def create_vm(request: Request, current_user = Depends(get_current_user_redirect)):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("create_vm.html", {"request": request, "title": "Create VM", "username": current_user.username})

@app.post("/update_vms")
async def update_vms_endpoint(current_user = Depends(get_current_user_redirect)):
   
    # Generate a unique task ID for this operation and create a task entry
    task_id = str(uuid.uuid4())
    create_task(task_id, current_user.username,"Update VMs")
    
    async def vms_update_task():
        try:
            db = SessionLocal()
            logger.info(f"Starting VM creation task with ID: {task_id}")
            
            #update the task status to running
            update_task(task_id, status=TaskStatus.RUNNING)
            
            await vms.get_all_vms( db)

            update_task(task_id, status=TaskStatus.SUCCESS, result="VMs updated.")

        except Exception as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
        finally:
            db.close()
    task_manager.add_task(vms_update_task)

    return JSONResponse(content={"task_id": task_id})

@app.post("/create-vm-entry")
async def create_entry_endpoint(request: Request, current_user = Depends(get_current_user_redirect)): 
 
    # Generate a unique task ID for this operation and create a task entry
    task_id = str(uuid.uuid4())
    create_task(task_id, current_user.username,"Create VM in Database")
    data = await request.json()
   
    async def vm_creation_task():
        try:
            #garantee that every tasks uses diffent db session so avoids conflict with other tasks
            db = SessionLocal()
            
            logger.info(f"Starting VM creation task with ID: {task_id}")
            #update the task status to running
            update_task(task_id, status=TaskStatus.RUNNING)
            
            await create_vm_entry(data, db,current_user.user_id)

            update_task(task_id, status=TaskStatus.SUCCESS, result="VM Created successfully.")
            return JSONResponse(content={"message": "VM created on DB successfully!"}, status_code=200)
        except ValidationException as e:
            update_task(task_id, status=TaskStatus.ERROR, error=e.errors)
            logger.error(f"Validation error: {e.errors}")

        except HTTPException as e:
            update_task(task_id, status=TaskStatus.ERROR, error=e.detail)
            logger.error(f"HTTPException: {e.detail}")
            return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}  
        )

        except Exception as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            logger.exception(f"Unexpected error during VM creation: {e}")   
        finally:
            db.close()    
            
    #leaves the task to be executed by the task manager (backend) and we just have the feedback on task status
    task_manager.add_task(vm_creation_task)

    return JSONResponse(content={"task_id": task_id})

def roleback_vm(db,data):
    vm_id = data.get("vm_id")
    vm_name = data.get("vmname")
    try:
        if not vm_id or not vm_name:
            logger.error(" vm_id or vmname aren't on request")
            return
    
        logger.warning(f"Rollback da VM {vm_id} após erro de validação.")
        asyncio.run(vms.delete_vm_everywhere(db,vm_name, vm_id))
    except Exception as delete_err:
        logger.error(f"Erro ao apagar VM durante rollback: {delete_err}")


@app.post("/generate_vm")
async def generate_vm_endpoint(request: Request, current_user = Depends(get_current_user_redirect)):  
   
    task_id = str(uuid.uuid4())
    create_task(task_id, current_user.username)
    data= await request.json()
    
    async def generate_vm_endpoint_task():    
        
        try:
            db = SessionLocal()
            
            update_task(task_id, status=TaskStatus.RUNNING)
            await generate_vm(request, db, current_user.proxmox_credentials_id)
            
            update_task(task_id, status=TaskStatus.SUCCESS, result="VM generated successfully.")
            
        except ValueError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            roleback_vm(db,data)
            logger.error("Validation error: %s", e)
            return JSONResponse(content={"error": str(e)}, status_code=422)

        except subprocess.CalledProcessError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            roleback_vm(db,data)
            logger.error("Terraform subprocess failed: %s", e)
            return JSONResponse(content={"error": "Terraform failed", "details": str(e)}, status_code=500)

        except FileNotFoundError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            roleback_vm(db,data)
            logger.error("Missing file: %s", e)
            return JSONResponse(content={"error": str(e)}, status_code=404)

        except Exception as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            roleback_vm(db,data)
            logger.exception("Unexpected error during VM provisioning")
            return JSONResponse(content={"error": "Unexpected error", "details": str(e)}, status_code=500)
        
        finally:
            db.close() 
               
    task_manager.add_task(generate_vm_endpoint_task)
    return JSONResponse(content={"task_id": task_id})

@app.post("/configure-vm")
async def configure_vm_endpoint(request: Request, current_user = Depends(get_current_user_redirect)):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    task_id = str(uuid.uuid4())
    create_task(task_id, current_user.username)
    data= await request.json()
    
    async def configure_vm_task():
        try:
            db= SessionLocal()
            update_task(task_id, status=TaskStatus.RUNNING)
            logger.info(f"Starting VM configuration task with ID: {task_id}")
            
            await configure_vm(request)
            
            update_task(task_id, status=TaskStatus.SUCCESS, result="VM configured successfully.")
            
        except FileNotFoundError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            
            roleback_vm(db,data)
            logger.error("Missing file: %s", e)
            return JSONResponse(content={"error": str(e)}, status_code=404)

        except subprocess.CalledProcessError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            roleback_vm(db,data)  # Clean up the VM because it was not configured successfully
            logger.error("Script failed with return code %s", e.returncode)
            return JSONResponse(content={"error": "Script failed", "returncode": e.returncode}, status_code=500)
        except RuntimeError as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            logger.error("Runtime error during script execution %s", str(e))
            roleback_vm(db,data)
            return JSONResponse(content={"error": "Script failed", "details": str(e)}, status_code=500)
        except Exception as e:
            update_task(task_id, status=TaskStatus.ERROR, error=str(e))
            logger.exception("Unexpected error during VM setup")
            roleback_vm(db,data)
            return JSONResponse(content={"error": "Unexpected error", "details": str(e)}, status_code=500)
        finally:
            db.close()
            
    task_manager.add_task(configure_vm_task)
    logger.info(f"Configure_vm_task with id: {task_id} added to task manager for VM configuration.")
    return JSONResponse(content={"task_id": task_id})


#i dont need to add get_current args because of Dependency Injection principle. 
# FastAPI inspects the dependency function (get_current_user) first
# resolves its arguments automatically, and only then runs the admin_page.
@app.get("/admin")
async def admin_page(request: Request, current_user = Depends(get_current_user_redirect)):
    
    return templates.TemplateResponse("adminPage/admin.html", {
        "request": request,
        "username": current_user.username
    })

@app.get("/admin/create_user")
async def create_user_page(request: Request):
    
    return templates.TemplateResponse("adminPage/createUser.html", {"request": request})

@app.get("/admin/all_users")
async def all_users_page(request: Request,db: Session = Depends(get_mariadb)):    
    return templates.TemplateResponse("adminPage/allUsers.html", {"request": request,"users": crud.get_users(db)})

@app.get("/admin/all_users/edit")
async def edit_user_page(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_mariadb), current_user = Depends(get_current_user_redirect)):
    if user_id is None:
        return RedirectResponse("/admin/")
    user = crud.get_user_by_field(db, "user_id", user_id)
    if user is None:
        return RedirectResponse("/admin/all_users")
    return templates.TemplateResponse("adminPage/change_user.html", {"request": request, "user": user, "username": current_user.username})

@app.get("/admin/all_tokens_key")
async def list_proxmox_credentials(request: Request, db: Session = Depends(get_mariadb), current_user = Depends(get_current_user_redirect)):
    creds = crud.get_proxmox_credentials(db)
    print(f"all creds: {creds}")
    return templates.TemplateResponse("adminPage/all_tokens_key.html", {"request": request, "credentials": creds, "username": current_user.username})

@app.get("/admin/all_tokens_key/edit")
async def change_tokens_key_page(request: Request, proxmox_id: Optional[int] = None, db: Session = Depends(get_mariadb), current_user = Depends(get_current_user_redirect)):

    if proxmox_id is None:
        return RedirectResponse("/admin/all_tokens_key")  
    cred = crud.get_proxmox_credential_by_promoxid(db, proxmox_id)
    if cred is None:
        return RedirectResponse("/admin/all_tokens_key")  # Redirect if no credential found
    return templates.TemplateResponse("adminPage/change_apikeys.html", {"request": request, "credential": cred, "username": current_user.username})

@app.post("/admin/all_users/edit")
def edit_user(user_update: schemas.UserUpdate, db: Session = Depends(get_mariadb)):
    logger.info(f"going to update user with data: {user_update}")
    updated_user = crud.update_user(db, user_update.user_id, user_update)
    if updated_user:
        return JSONResponse(content={
            "message": "User updated successfully",
            "username": updated_user.username,
            "role": updated_user.role
        })
    else:
        return JSONResponse(content={
            "message": "User not found",
        }, status_code=404)
        
@app.post("/admin/all_tokens_key/edit")
def change_apikeys(proxmox_update: schemas.ProxmoxCredentialsUpdate, db:Session = Depends(get_mariadb), current_user = Depends(get_current_user_redirect)):
    logger.info(f"going updating proxmox with data: {proxmox_update}")
    updated_cred = crud.update_proxmox(db,proxmox_update.proxmox_id,proxmox_update)
    return JSONResponse(content={
        "message": "API keys updated successfully",
        "proxmox_user": updated_cred.proxmox_user,
        "username": current_user.username
    })

    
@app.post("/admin/all_tokens_key/delete")
def delete_apikeys(delete_request: schemas.ProxmoxDeleteRequest, db:Session = Depends(get_mariadb)):
    logger.info(f"going to delete proxmox with id: {delete_request.proxmox_id}")
    proxmox_id = delete_request.proxmox_id
    deleted_cred = crud.delete_proxmox(db,proxmox_id)
    if deleted_cred:
        return JSONResponse(content={
            "message": "API keys deleted successfully",
        })
    else:
        return JSONResponse(content={
            "message": "API keys to delete not found",
        }, status_code=404)



@app.get("/attacks")
async def attackmenu(request: Request, current_user = Depends(get_current_user_redirect),db: Session = Depends(get_mariadb)):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    vmsTarget= crud.get_user_vms_by_role(db, "target", current_user.user_id)
    vmsAttacker= crud.get_user_vms_by_role(db, "attacker", current_user.user_id)
    logger.info(f"vmsTarget: {vmsTarget}")
    logger.info(f"vmsAttacker: {vmsAttacker}")
    return templates.TemplateResponse("attack/attacks.html", {"request": request,"vmsTarget":vmsTarget, "vmsAttacker":vmsAttacker, "username": current_user.username, "title": "Attacks Menu"})

@app.post("/start-attack")
def start_attack():
   iniciate_the_attack()


if __name__ == "__main__":
    uvicorn.run(
        "webapp:app", 
        host="0.0.0.0", 
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        log_config=settings.LOGGING_CONFIG,
        workers=4,
        reload=True
    )