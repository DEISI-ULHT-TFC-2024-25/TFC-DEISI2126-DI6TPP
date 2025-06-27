import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from data_model import models, schemas
from sqlalchemy.sql.expression import func
from .security import hash_password #relative path using "."

logger = logging.getLogger('uvicorn.error')

def get_users(db: Session):
    return db.query(models.User).all()

def get_user_by_field(db: Session, field: str, value: str | int):
    field_obj = getattr(models.User, field, None)
    if field_obj is None:
        raise ValueError(f"Field '{field}' does not exist on User model")
    
    return db.query(models.User).filter(field_obj == value).first() 

def get_random_user_id(db: Session):
    return db.query(models.User).order_by(func.rand()).first().user_id

def create_user(db: Session, user: schemas.UserCreate):
    if get_user_by_field(db,"username", user.username) is not None:
        #this is the only option to be sure that will fall on the ValidationError with the pydantic errors 
        # to be treated all together on the error messages
        raise HTTPException(
            status_code=422,
            detail=[{
                "loc": ["body", "username"],
                "msg": "Name is already in use",
                "type": "value_error"
            }]
        )
    # Encrypt the password using Argon2
    hashed_password = hash_password(user.password)
    
    db_user = models.User(
        username=user.username,
        role=user.role,
        hashed_password=hashed_password,
        proxmox_credentials_id=user.proxmox_credentials_id 
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserCreate):
    db_user = get_user_by_field(db,"user_id", user_id)
    
    hashed_password = hash_password(user_update.password)
    
    if db_user:
        db_user.username = user_update.username
        db_user.role = user_update.role
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user_by_field(db,"user_id", user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def is_username_taken(db: Session, username: str) -> bool:
    return db.query(models.User).filter(func.binary(models.User.username) == username).first() is not None





def get_vms(db: Session):
    return db.query(models.VM).all()

def get_user_vms(db: Session, user_id: int):
    return db.query(models.VM).filter(models.VM.creator_id == user_id).all()

def get_user_vms_by_role(db: Session, role_vm_str: str, user_id: int):
    user= get_user_by_field(db, "user_id", user_id)
    id_role= get_id_by_role(db, role_vm_str)
    
    if id_role == -1 or user == None:
        return []    
    
    if user.role == "admin":
        return db.query(models.VM).filter(models.VM.role_id == id_role).all()
    
    return db.query(models.VM).filter(models.VM.creator_id == user_id, models.VM.role_id == id_role).all()
    

def get_vm_by_field(db: Session, field: str, value: str | int):
    field_obj = getattr(models.VM, field, None)
    if field_obj is None:
        raise ValueError(f"Field '{field}' does not exist on VM model")
    
    return db.query(models.VM).filter(field_obj == value).first() 

class ValidationException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Validation failed")
        

def create_vm(db: Session, vm: schemas.VMCreate):
    logger.info(f"Creating VM with data: {vm}")
    vmname= vm.vmname
    vm_ip= vm.vm_ip
    vm_id = vm.vm_id
    
    errors = []

    if get_vm_by_field(db, "vm_id", vm_id) is not None:
        logger.error(f"VM with id {vm_id} from vm {vmname} already exists on proxmox, change it as soon as possible.")
        errors.append({
            "loc": ("vm_id",),
            "msg": f"VM with id {vm_id} already exists",
            "type": "value_error",
        })

    if get_vm_by_field(db, "vmname", vmname) is not None:
        logger.error(f"VM with name {vmname} already exists on proxmox, change it as soon as possible.")
        errors.append({
            "loc": ("vmname",),
            "msg": f"VM with name {vmname} already exists",
            "type": "value_error",
        })

    if get_vm_by_field(db, "vm_ip", vm_ip) is not None and vm_ip != "0.0.0.0":
        logger.error(f"VM with ip {vm_ip} from vm {vmname} already exists on proxmox, change it as soon as possible.")
        errors.append({
            "loc": ("vm_ip",),
            "msg": "VM with this IP already exists",
            "type": "value_error",
        })

    if errors:
        raise ValidationException(errors)
        
    db_vm = models.VM(
        vmname=vm.vmname,
        vm_id=vm.vm_id,
        vm_ip=vm.vm_ip,
        creator_id=vm.creator_id,
        role_id=vm.role_id,
        active_status=vm.active_status,
        vm_specs=vm.vm_specs,
        born_place=vm.born_place,
        created_at=datetime.utcnow()
    )
    db.add(db_vm)
    db.commit()
    db.refresh(db_vm)
    return db_vm

def update_vm_status(db: Session, vm_id: int, status: bool):
    db_vm = get_vm_by_field(db,"vm_id", vm_id)
    if db_vm and db_vm.active_status != status:
        db_vm.active_status = status
        db.commit()
        db.refresh(db_vm)
    return db_vm


def delete_vm(db: Session, vm_id: int):
    db_vm = get_vm_by_field(db, "vm_id",vm_id)
    if db_vm:
        db.delete(db_vm)
        db.commit()
        return True
    return False

def update_vm(db: Session, vm_id: int, vm_update: schemas.VMCreate):
    db_vm = get_vm_by_field(db, "vm_id", vm_id)
    if db_vm:
        db_vm.vmname = vm_update.vmname
        db_vm.vm_ip = vm_update.vm_ip
        db.commit()
        db.refresh(db_vm)
    return db_vm

def get_logs_by_vm(db: Session, vm_id: int):
    return db.query(models.WebAppLogs).filter(models.WebAppLogs.vm_id == vm_id).all()

def create_log(db: Session, log: schemas.WebAppLogsCreate):
    db_log = models.WebAppLogs(
        user_id=log.user_id,
        vm_id=log.vm_id,
        activity_made=log.activity_made,
        timestamp=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_sessions_by_field(db: Session, field:str, value: str | int):
    field_obj = getattr(models.Session, field, None)
    if field_obj is None:
        raise ValueError(f"Field '{field}' does not exist on User model")
    
    return db.query(models.Session).filter(field_obj == value).first() 

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(
        user_id=session.user_id,
        token=session.token,
        login_timestamp=datetime.utcnow(),
        logout_timestamp=None,
        last_activity=datetime.utcnow(), 
        valid_until=session.valid_until
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session



#dont forget that exists credentials without password!
def get_proxmox_credentials(db: Session):
    return db.query(models.ProxmoxCredentials).all()

def get_proxmox_credential_by_promoxid(db: Session, proxmox_id:int):
    return db.query(models.ProxmoxCredentials).filter(models.ProxmoxCredentials.proxmox_id == proxmox_id).first()

def get_proxmox_credential_by_field(db: Session, field: str, value: str | int):
    field_obj = getattr(models.ProxmoxCredentials, field, None)
    if field_obj is None:
        raise ValueError(f"Field '{field}' does not exist on ProxmoxCredentials model")
    
    return db.query(models.ProxmoxCredentials).filter(field_obj == value).first()

def create_proxmox_credentials(db: Session, credentials: dict):
    db_cred = models.ProxmoxCredentials(
        token_id=credentials['token_id'],
        proxmox_user=credentials['proxmox_user'],
        token_key=credentials['token_key']
    )
    db.add(db_cred)
    db.commit()
    db.refresh(db_cred)
    return db_cred

def is_proxmox_token_id_taken(db: Session, username: str) -> bool:
    return db.query(models.ProxmoxCredentials).filter(func.binary(models.ProxmoxCredentials.token_id) == username).first() is not None

def delete_proxmox(db: Session, proxmox_id: int):
    db_user = get_proxmox_credential_by_promoxid(db, proxmox_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def update_proxmox(db: Session, proxmox_id: int, proxmox_update: schemas.ProxmoxCredentialsCreate):
    db_user = get_proxmox_credential_by_promoxid(db, proxmox_id)
    logger.info(f"Updating Proxmox with data: {proxmox_update}")
    if db_user:
        db_user.token_id = proxmox_update.token_id
        db_user.proxmox_user = proxmox_update.proxmox_user
        db_user.token_key = proxmox_update.token_key
        db.commit()
        db.refresh(db_user)
    return db_user
    

def get_attack_instructions(db: Session):
    return db.query(models.AttackInstructions).all()

def create_attack_instruction(db: Session, instruction: schemas.AttackInstructionsCreate):
    db_instruction = models.AttackInstructions(
        vm_id=instruction.vm_id,
        action=instruction.action,
        timestamp=datetime.utcnow()
    )
    db.add(db_instruction)
    db.commit()
    db.refresh(db_instruction)
    return db_instruction





def get_attack_targets(db: Session):
    return db.query(models.AttackTarget).all()

def create_attack_target(db: Session, target: schemas.AttackTargetCreate):
    db_target = models.AttackTarget(
        attack_instruction_id=target.attack_instruction_id,
        target_name=target.target_name,
        attack_status=target.attack_status
    )
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


def create_vm_role(db: Session, role_type: str):
    db_role = models.VMRole(
        role_type= role_type
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def role_exists(db: Session, role:str):
    return db.query(models.VMRole).filter(models.VMRole.role_type == role).first() is not None

def get_id_by_role(db: Session, vm_role: str):
    
    vm_role= db.query(models.VMRole).filter(models.VMRole.role_type == vm_role).first()
    
    if vm_role is not None:
        return vm_role.role_id
    
    return -1

