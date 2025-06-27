import pytest
from httpx import AsyncClient
from data_model import crud, schemas
from tests.fixtures.db import PROXMOX_TEST_TOKEN_ID, PROXMOX_TEST_TOKEN_USER, PROXMOX_TEST_TOKEN_SECRET, USERNAME_ADMIN, PASSWORD_ADMIN

@pytest.fixture
async def add_proxmox_credential_fixture(): 
    async def _add_proxmox(db_session, token: str, user: str, secret: str):
        data = {
            "token_id": token,
            "proxmox_user": user,
            "token_key": secret
        }
        proxmox=crud.create_proxmox_credentials(db_session, data)
        
        assert proxmox.proxmox_user == user 
        assert proxmox.token_id == token
        assert proxmox.token_key == secret
        return proxmox.proxmox_id
    return _add_proxmox


@pytest.fixture
def create_user_fixture():
    async def _create_user(db_session ,username: str, password: str, role: str, proxmox_cred_Id: int):
        data={
            "username": username,
            "password": password,
            "role": role,
            "proxmox_credentials_id": proxmox_cred_Id
        }
        validated = schemas.UserCreate(**data)
        user= crud.create_user(db_session, validated)

        assert user.username == username
        assert user.role == role
        assert user.proxmox_credentials_id == proxmox_cred_Id
        
        return user
    return _create_user  

@pytest.fixture
async def test_create_user_admin_user(client, db_session, create_user_fixture, add_proxmox_credential_fixture):
        
    proxmox_id = await add_proxmox_credential_fixture(db_session, PROXMOX_TEST_TOKEN_ID, PROXMOX_TEST_TOKEN_USER, PROXMOX_TEST_TOKEN_SECRET)
    
    response_user_creation = await create_user_fixture(db_session, USERNAME_ADMIN, PASSWORD_ADMIN, "admin", proxmox_id)
 
    assert response_user_creation is not None
    assert response_user_creation.role == "admin"
    assert response_user_creation.proxmox_credentials_id == proxmox_id 
    
    return response_user_creation