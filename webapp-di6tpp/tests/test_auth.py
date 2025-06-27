import pytest
from data_model import crud

'''@pytest.mark.anyio
async def test_login(client):
    response = await client.post("/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200


# Fixture to create a normal user (if this doesnt exist already)
#fixture is something that provides data or ready enviroments to tests
@pytest.fixture
def create_normal_user(db_session):
    user = crud.get_user_by_field(db_session,"username", "normaluser")
    proxmox_credentials = crud.get_random_proxmox_credentials(db_session)
    
    if not proxmox_credentials:
        raise RuntimeError("❌ Não existem credenciais Proxmox na base de dados de teste!")

    if not user:
        user_data = {
            "username": "normaluser",
            "password": "normaluser123",
            "role": "user",
            "proxmox_credentials_id": proxmox_credentials.proxmox_id
        }
        user = crud.create_user(db_session, user_data)
        
    return user

@pytest.mark.anyio
async def test_user_login_and_access_admin(client, create_normal_user):
    # Login with normal user
    login_response = await client.post("/login", json={
        "username": create_normal_user.username,
        "password": create_normal_user.password
    })


    assert login_response.status_code == 200

    # copy cookies answer
    cookies = login_response.cookies

    # try to acess the admin page using the cookies
    admin_response = await client.get("/admin", cookies=cookies)

    # wait from be forbidden (403) or non autorized (401)
    assert admin_response.status_code in [401, 403]
'''