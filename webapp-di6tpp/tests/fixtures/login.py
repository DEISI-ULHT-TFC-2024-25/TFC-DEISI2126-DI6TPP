import pytest
import logging

from httpx import AsyncClient
from sqlalchemy.orm import Session

from webapp import app  # substitui por onde tens a tua app
from tests.fixtures.db import override_get_db  # se tiveres um DB de testes
from data_model import crud,schemas  # onde defines funções como create_user
from tests.fixtures.db import USERNAME_ADMIN, PASSWORD_ADMIN


logger= logging.getLogger('uvicorn.error') # ou cria um logger específico para testes


@pytest.fixture
def logged_in_admin_client_fixture():
    async def _logged_in_admin_client(client: AsyncClient, db_session: Session, username:str,password:str ):
        
        # 1. Cria um utilizador admin 
        user_data = {
            "username": username,
            "password": password,
        }

        # Garante que o user existe (usa o teu CRUD / ORM) pois como esa no test db está limpo
        user = crud.get_user_by_field(db_session,"username", user_data["username"])
        
        assert user is not None, "O utilizador admin não foi criado corretamente"
        
        # 2. Faz login
        response = await client.post("/login", json=user_data)
        logger.info(f"Login response: {response.text}")
        # Verifica se o login foi bem-sucedido
        assert response.status_code == 200, f"response: {response.text} location: {response.headers.get('Location')}"
        
        # 3. Reenvia cookies do login para a fixture
        token = response.cookies.get("access_token")
        assert token is not None, "Token não foi encontrado nos cookies"

        return response
    return _logged_in_admin_client