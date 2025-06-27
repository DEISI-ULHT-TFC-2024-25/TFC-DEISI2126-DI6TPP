import re
import ipaddress
import logging

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

logger = logging.getLogger('uvicorn.error')

class UserValidation:
    @staticmethod
    def validate_username(username: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain letters, numbers, and underscores.")
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        if len(password) <= 8:
            raise ValueError("Password must be longer than 8 characters.")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.match(r"^[a-zA-Z0-9]+$", password):
            raise ValueError("Password can only contain letters and numbers.")
        return password
    
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    proxmox_credentials_id: int

    #pydantic validator but only to things that doesnt need acess to bd
    @field_validator("username")
    @classmethod
    def validate_username(cls, username):
        return UserValidation.validate_username(username)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        return UserValidation.validate_password(password)


class UserOut(UserBase):
    proxmox_credentials_id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserDeleteRequest(BaseModel):
    user_id: int

class UserUpdate(BaseModel):
    user_id: int
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    proxmox_credentials_id: Optional[int] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, username):
        if username:
            return UserValidation.validate_username(username)
        return username
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        if password:
            return UserValidation.validate_password(password)
        return password


class VMBase(BaseModel):
    vmname: str
    vm_id: int
    vm_ip: str
    creator_id: int
    role_id: int
    born_place: str
    vm_specs: dict
    created_at: str
    active_status: str
    
    @field_validator("vmname")
    @classmethod
    def validate_vmname(cls, vmname):
        print("Name validation here:")
        if len(vmname) < 6 or len(vmname) > 50:
            raise ValueError("VM name must be between 6 and 50 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", vmname):
            raise ValueError("VM name can only contain letters, numbers, and hyphens")
        
        if not vmname[0].isalpha():
            raise ValueError("VM name must start with a letter")
        
        if vmname.endswith('-'):
            raise ValueError("VM name cannot end with a hyphen")
        
        if '--' in vmname:
            raise ValueError("VM name cannot contain consecutive hyphens")
        
        return vmname
    
    @field_validator("vm_id")
    @classmethod
    def validate_vm_id(cls, vm_id):
               
        if not isinstance(vm_id, int):
            raise ValueError("VM ID must be a number")
        if vm_id < 0:
            raise ValueError("VM ID cannot be negative")
        return vm_id
    
    @field_validator("vm_ip")
    @classmethod
    def validate_vm_ip(cls, ip):
         #even if the ip is valid in the /20 network which is, it is only accept ips that start with 10.5.32.
        try:
            #for server vms but will only accept for those because it will have a check on crud if the ip is already in use
            if ip in {"0.0.0.0", "10.5.16.100", "10.5.16.11", "10.5.16.10", "10.5.0.9"}:
                return ip
        
            ip_obj = ipaddress.IPv4Address(ip)
            in_subnet = ip_obj in ipaddress.IPv4Network("10.5.32.0/20")
            starts_with_32 = ip.startswith("10.5.32.")
            
            #on crud was already checked if the ip is already in use
            if not (in_subnet and starts_with_32):
                raise ValueError("IP must be within 10.5.32.0/20 and start with 10.5.32.*")
            return ip
        except ValueError:
            raise ValueError("Invalid IP address format")
    
    class Config:
        arbitrary_types_allowed = True

class VMCreate(VMBase):   
    pass
   
    
class VMOut(VMBase):
    class Config:
        from_attributes = True

class VMUpdate(BaseModel):
    vm_id: int
    vm_ip: int
    vmname: str

class VMRoleBase(BaseModel):
    role_type: str


class VMRoleCreate(VMRoleBase):
    pass


class VMRoleOut(VMRoleBase):
    role_id: int

    class Config:
        from_attributes = True





class WebAppLogsBase(BaseModel):
    activity_made: str
    timestamp: datetime


class WebAppLogsCreate(WebAppLogsBase):
    user_id: int
    vm_id: int


class WebAppLogsOut(WebAppLogsBase):
    logs_id: int
    user_id: int
    vm_id: int

    class Config:
        from_attributes = True






class SessionBase(BaseModel):
    token: str
    login_timestamp: datetime
    logout_timestamp: Optional[datetime]
    valid_until: datetime


class SessionCreate(SessionBase):
    user_id: int


class SessionOut(SessionBase):
    session_id: int
    user_id: int

    class Config:
        from_attributes = True




class ProxmoxCredentialsBase(BaseModel):
    token_id: str
    proxmox_user: str
    token_key: str


class ProxmoxCredentialsCreate(ProxmoxCredentialsBase):
    pass


class ProxmoxCredentialsOut(ProxmoxCredentialsBase):
    proxmox_id: int

    class Config:
        from_attributes = True

class ProxmoxCredentialsUpdate(BaseModel):
    proxmox_id: int
    proxmox_user: str
    token_id: str
    token_key: str

class ProxmoxDeleteRequest(BaseModel):
    proxmox_id: int



class LogAnalyticsBase(BaseModel):
    severity: Optional[int]


class LogAnalyticsCreate(LogAnalyticsBase):
    web_logs_id: int
    attack_instruction_id: int


class LogAnalyticsOut(LogAnalyticsBase):
    logs_analytics_id: int
    web_logs_id: int
    attack_instruction_id: int

    class Config:
        from_attributes = True







class AttackInstructionsBase(BaseModel):
    action: str
    timestamp: Optional[datetime]


class AttackInstructionsCreate(AttackInstructionsBase):
    vm_id: int


class AttackInstructionsOut(AttackInstructionsBase):
    instructions_id: int
    vm_id: int

    class Config:
        from_attributes = True






class AttackTargetBase(BaseModel):
    target_name: str
    attack_status: str


class AttackTargetCreate(AttackTargetBase):
    attack_instruction_id: int


class AttackTargetOut(AttackTargetBase):
    attack_target_id: int
    attack_instruction_id: int

    class Config:
        from_attributes = True
