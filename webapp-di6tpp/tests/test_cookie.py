import pytest
from data_model import crud
from datetime import datetime, timedelta

'''
@pytest.mark.anyio
def test_inactivity_timeout(db_session, client):
    # Simula uma sessão com last_activity há 31 minutos
    session = crud.get_sessions_by_field(db_session, "token", valid_token)
    session.last_activity = datetime.utcnow() - timedelta(minutes=31)
    db_session.commit()

    # Faz pedido com token válido (via cookie)
    response = client.get("/admin", cookies={"access_token": valid_token})

    assert response.status_code == 401
    assert response.json()["detail"] == "Sessão expirada por inatividade"
  
@pytest.mark.anyio  
def test_activity_resets_timeout(db_session, client, valid_token):
    # Simula sessão com last_activity há 10 minutos
    session = crud.get_sessions_by_field(db_session, "token", valid_token)
    session.last_activity = datetime.utcnow() - timedelta(minutes=10)
    db_session.commit()

    # Faz pedido com token válido
    response = client.get("/admin", cookies={"access_token": valid_token})

    assert response.status_code == 200

    # Verifica se o last_activity foi atualizado para agora (aproximadamente)
    session = crud.get_sessions_by_field(db_session, "token", valid_token)
    assert (datetime.utcnow() - session.last_activity).total_seconds() < 5
  '''  
