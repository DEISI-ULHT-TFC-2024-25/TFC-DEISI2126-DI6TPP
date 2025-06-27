from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .database import Base


class WebAppLogs(Base):
    __tablename__ = "webapp_logs"
    
    logs_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    vm_id = Column(Integer, ForeignKey("vms.vm_id", ondelete="CASCADE"), nullable=False)
    activity_made = Column(String(400), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    
    user = relationship("User", back_populates="webapp_logs")
    vm = relationship("VM", back_populates="webapp_logs")
    log_analytics = relationship("LogAnalytics", back_populates="webapp_logs")


class VM(Base):
    __tablename__ = "vms"
    
    vm_id = Column(Integer, primary_key=True, index=True)
    vmname = Column(String(50), unique=True, nullable=False)
    vm_ip = Column(String(50), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("vm_roles.role_id", ondelete="CASCADE"), nullable=False)
    active_status = Column(String(50), nullable=False)
    vm_specs = Column(JSON, nullable=True)
    born_place = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    
    user = relationship("User", back_populates="vms")
    role = relationship("VMRole", back_populates="vms")
    webapp_logs = relationship("WebAppLogs", back_populates="vm")
    attack_instructions = relationship("AttackInstructions", back_populates="vm")

    def to_dict(self):
        return {
            "vm_id": self.vm_id,
            "vmname": self.vmname,
            "vm_ip": self.vm_ip,
            "creator_id": self.creator_id,
            "role_id": self.role_id,
            "active_status": self.active_status,
            "vm_specs": self.vm_specs,
            "born_place": self.born_place,
            "created_at": self.created_at,
        }

class VMRole(Base):
    __tablename__ = "vm_roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    role_type = Column(String(50), nullable=False)  

    vms = relationship("VM", back_populates="role")


class User(Base):
    __tablename__ = "users"
    
    #creates a index in the db column that allows fast lookups. ex: prevents the need to go line by line 
    #but pk already have them so it is great to use in fields that we use a lot for queries like role and username
    user_id = Column(Integer,primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    proxmox_credentials_id = Column(Integer, ForeignKey("proxmox_credentials.proxmox_id"), nullable=False)
    
    #relationship(what is the table that we want to have the relationship, the variables name that we used to do the relationship)
    proxmox_credentials = relationship("ProxmoxCredentials", back_populates="users")
    vms = relationship("VM", back_populates="user")
    webapp_logs = relationship("WebAppLogs", back_populates="user")
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), unique=True, nullable=False) #tokens is normally around 150 to 300 caracters
    login_timestamp = Column(TIMESTAMP, nullable=False)
    logout_timestamp = Column(TIMESTAMP, nullable=True)
    last_activity = Column(TIMESTAMP, nullable=False)  # Used to track user activity
    valid_until = Column(TIMESTAMP, nullable=False)
    
    user = relationship("User", back_populates="sessions")


class ProxmoxCredentials(Base):
    __tablename__ = "proxmox_credentials"
    
    proxmox_id = Column(Integer, primary_key=True, index=True)
    proxmox_user = Column(String(100), nullable=True)
    token_id = Column(String(50), nullable=False)
    token_key = Column(String(100), nullable=True)
    
    users = relationship("User", back_populates="proxmox_credentials")


class LogAnalytics(Base):
    __tablename__ = "log_analytics"
    
    logs_analytics_id = Column(Integer, primary_key=True, index=True)
    web_logs_id = Column(Integer, ForeignKey("webapp_logs.logs_id", ondelete="CASCADE"), nullable=False)
    attack_instruction_id = Column(Integer, ForeignKey("attack_instructions.instructions_id", ondelete="CASCADE"), nullable=False)
    severity = Column(Integer, nullable=True)
    
    webapp_logs = relationship("WebAppLogs", back_populates="log_analytics")
    attack_instructions = relationship("AttackInstructions", back_populates="log_analytics")


class AttackInstructions(Base):
    __tablename__ = "attack_instructions"
    
    instructions_id = Column(Integer, primary_key=True, index=True)
    vm_id = Column(Integer, ForeignKey("vms.vm_id", ondelete="CASCADE"), nullable=False)
    action = Column(String(200), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=True)
    
    vm = relationship("VM", back_populates="attack_instructions")
    log_analytics = relationship("LogAnalytics", back_populates="attack_instructions")
    attack_targets = relationship("AttackTarget", back_populates="attack_instructions")


class AttackTarget(Base):
    __tablename__ = "attack_targets"
    
    attack_target_id = Column(Integer, primary_key=True, index=True)
    attack_instruction_id = Column(Integer, ForeignKey("attack_instructions.instructions_id", ondelete="CASCADE"), nullable=False)
    target_name = Column(String(20), nullable=False)
    attack_status = Column(String(20), nullable=False)
    
    attack_instructions = relationship("AttackInstructions", back_populates="attack_targets")
