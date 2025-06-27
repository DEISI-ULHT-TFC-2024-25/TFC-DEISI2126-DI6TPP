import pytest
from tests.fixtures.db import PASSWORD_ADMIN
from tests.fixtures.user import create_user_fixture, add_proxmox_credential_fixture, test_create_user_admin_user
from tests.fixtures.login import logged_in_admin_client_fixture
from data_model import crud

@pytest.mark.anyio
async def test_loggin_admin_user(client, db_session,test_create_user_admin_user, logged_in_admin_client_fixture, create_user_fixture, add_proxmox_credential_fixture):
    #it reads the logged_in_client fixture to get the cookies 
    
    admin_user = test_create_user_admin_user

    token_response = await logged_in_admin_client_fixture(client, db_session, admin_user.username, PASSWORD_ADMIN)
    
    assert token_response.status_code == 200
    assert client.cookies is not None, "Cookies should be set after login"
    assert f"{client.cookies}"
