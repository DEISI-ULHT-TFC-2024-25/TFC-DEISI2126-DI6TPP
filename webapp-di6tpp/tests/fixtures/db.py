import os
import logging
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from httpx import AsyncClient

from data_model.database import Base, get_mariadb  # mantém get_mariadb para ser sobreposto
from webapp import app

logger = logging.getLogger('uvicorn.error')

# Usar ficheiro .env.test (podes mudar se quiseres usar outro)
load_dotenv(".env.test")

# Lê URL diretamente (ex: sqlite:///./test.db ou sqlite:///:memory:)
#test.db ficheiro / memory é guardado na RAM
DATABASE_URL = os.getenv("DATABASE_URL")
PROXMOX_TEST_TOKEN_ID = os.getenv("PROXMOX_TEST_TOKEN_ID")
PROXMOX_TEST_TOKEN_USER = os.getenv("PROXMOX_TEST_TOKEN_USER")
PROXMOX_TEST_TOKEN_SECRET = os.getenv("PROXMOX_TEST_TOKEN_SECRET")
USERNAME_ADMIN = os.getenv("USERNAME_ADMIN")
PASSWORD_ADMIN = os.getenv("PASSWORD_ADMIN")

if not DATABASE_URL:
    raise RuntimeError("A variável DATABASE_URL não está definida no .env.test")

# SQLite requer este argumento extra para trabalhar com múltiplas threads
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria e destrói a base de dados SQLite antes/depois dos testes
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Cria as tabelas todas no ficheiro SQLite
    Base.metadata.create_all(bind=engine)
    
    yield  # Executa os testes
    
    Base.metadata.drop_all(bind=engine)
    # Elimina o ficheiro se for uma base de dados em disco
    if DATABASE_URL.startswith("sqlite:///./") and "memory" not in DATABASE_URL:
        db_file = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_file):
            os.remove(db_file)

# Cria sessões ligadas ao SQLite
@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

# Substitui a dependência original pelo novo sessionmaker para testes
def override_get_db():
    logger.info(f"A testar com base de dados SQLite: {DATABASE_URL}")
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_mariadb] = override_get_db
