import logging
import asyncio
import jwt
import os
import httpx

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from jwt import exceptions as jwt_exceptions
from pydantic import ValidationError
from datetime import datetime, timedelta

from data_model import schemas, crud, models
from data_model.database import get_mariadb

#allows organize smal routes like /users
router = APIRouter()
logger = logging.getLogger('uvicorn.error')


# JWT config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRATION_TIME"))  # 30 minutes

def create_user_access_token(user: models.User, db: Session = Depends(get_mariadb)) -> str:
    """
    Generates a JWT for a user and register this new session on Session table
    """
    try:
        # Calculate expiration timestamp for the token (now + 1800 seconds)
        expire_time = datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRE_SECONDS)

        # Define the payload (token content):
        payload = {
            "sub": str(user.user_id),
            "username": user.username,
            "role": user.role,
            "exp": expire_time
        }
        
        # Encode and sign the token using secret key and algorithm
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        logger.info(f"encoding token: {token}")
        # Build the session data object to save in the DB
        session_data = schemas.SessionCreate(
            user_id=user.user_id,
            token=token,
            login_timestamp=datetime.utcnow(),
            logout_timestamp=None,
            last_activity=datetime.utcnow(),  # Initialize last activity to now
            valid_until=expire_time
        )
        
        logger.info(f"creating session on db")
        # Persist the session in the database
        crud.create_session(db, session_data)

        return token
    
    except Exception as e:
        logger.error(f"Unexpected error while creating session: {e}")
        raise HTTPException(status_code=500, detail="Session creation failed")



def verify_token(token: str):
    """Verify the JWT token and return its payload if valid, otherwise return None."""
    try:
        logger.debug(f"Verifying Token: {token}")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    #
    except jwt_exceptions.ExpiredSignatureError as e:
        logger.error(f"Token has expired: {e}")
        return None

    except jwt_exceptions.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected token decoding error: {e}")
        return None

def get_current_user(
    request: Request,
    db,
    access_token: str | None
) -> models.User:
    """
    Extracts the token (from cookie or header), validates it, checks the session,
    and returns the authenticated user.
    """
    try:
        # 1. gets the token 
                
        if not access_token:
            logger.info(f"no token:")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing")

        # 2. Verify token (signature, expiration, etc.)
        payload = verify_token(access_token)
        if not payload:
            logger.info(f"not payload:")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        logger.info(f"checking on sessions if the token is valid")
        
        # 3. verify if the session exists and it is active on db
        session = crud.get_sessions_by_field(db,"token", access_token)
        invalid = session.valid_until < datetime.utcnow()
        logger.info(f"token is valid until {session.valid_until} and time now is {datetime.utcnow()} so it's invalid= {invalid}")
        if not session or session.valid_until < datetime.utcnow() or session.logout_timestamp is not None:
            logger.info(f"session not found or expired:")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

        logger.info(f"getting the user that has the token")
        # 4. get the user from db
        user = crud.get_user_by_field(db,"user_id", session.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user
    #needed so httpexceptions dont fall on the exception. exception needed for unexpeted errors like db errors or connections
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error while checking for a valid session: {e}")
        raise HTTPException(status_code=500, detail="Session checking failed")

async def validate_proxmox_creds( proxmox_user,token_id, token_key):
    proxmox_api = f"https://10.5.0.1:8006/api2/json/"
    tokencreds = f"{proxmox_user}!{token_id}"

    try:
        api_token = f"PVEAPIToken={tokencreds}={token_key}"
        headers = {"Authorization": api_token}
      
        async with httpx.AsyncClient(verify=False) as client:
            
            response = await client.get(f"{proxmox_api}/nodes", headers=headers)

            if response.status_code != 200:
                logger.error(f"tokencreds: {tokencreds}")
                logger.error(f"Authentication failed: {response.text}")
                raise HTTPException(status_code=401, detail="Invalid API Token")

            logger.info("Authenticated successfully with API Token.")
            
            # Return headers with the API token for future requests. Avoid query string leaks!
            # PROXMOX documentation:"You must pass the API token in the Authorization header."
            return True  

    except Exception as e:
        logger.error(f"error connecting to proxmox: {e}")
        return False

@router.post("/admin/create_user", response_model=schemas.UserOut)
async def create_user(request: Request, db: Session = Depends(get_mariadb)):
    """ Endpoint to create a new user """

    try:
        data = await request.json()
        logger.info(f"Received data: {data}")

        #data was all structured in js        
        validated = schemas.UserCreate(**data)
        logger.info(f"Validated data: {validated}")
        
        #this is made in here because here we have acess to db info no on schema file    
        new_user = crud.create_user(db, validated)
        logger.info(f"New user created: {new_user}")

        if not new_user:
            raise HTTPException(status_code=400, detail="Error creating user")

        return JSONResponse(content={"message": "User created successfully!", "username": new_user.username}, status_code=200)
    
    #pydantic errors
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(e.errors())}
        )
    except HTTPException as e:
        logger.warning(f"HTTPException caught: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

@router.post("/admin/all_users/delete")
async def delete_user(request:Request, db:Session = Depends(get_mariadb)):
    
    data = await request.json()
    user_id = data.get('user_id')
    if not user_id:
        logger.error("User ID not provided in the request")
        return JSONResponse(content={
            "message": "User ID is required",
        }, status_code=400)
        
    logger.info(f"going to delete user with id: {user_id}")
    
    deleted_user = crud.delete_user(db,user_id)
    if deleted_user:
        return JSONResponse(content={
            "message": "User deleted successfully",
        })
    else:
        return JSONResponse(content={
            "message": "User to delete not found",
        }, status_code=404)
        


@router.post("/admin/addcredential")
async def get_proxmox_id(request: Request ,db: Session = Depends(get_mariadb)):
    """ gets a proxmox token id and secret and adds to db if not exists and returns the id of the proxmox object."""
    try:
        logger.info("Starting pxomoxid endpoint")
        data = await request.json()  

        token_id = data['proxmox_cred_Id']
        proxmoxUser = data['proxmoxUser']
        
        cred={
            'token_id':token_id, 
            'proxmox_user': proxmoxUser,
            'token_key': data['proxmoxSecret'],
        }
        
        valide = await validate_proxmox_creds(proxmoxUser,token_id, cred['token_key'])
        if not valide:
            logger.error("Proxmox credentials are not valid")
            raise HTTPException(status_code=401, detail="Invalid Proxmox credentials")

        proxmox_rand_cred = crud.get_proxmox_credential_by_field(db, "token_id", token_id)

        if not proxmox_rand_cred:
            proxmox_id = crud.create_proxmox_credentials(db, cred).token_id
        else:
            proxmox_id = proxmox_rand_cred.proxmox_id
            
        logger.info(f"random Token for the user : {proxmox_id}")
        return proxmox_id
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(e.errors())}
        )
    except HTTPException as e:
        logger.warning(f"HTTPException caught: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )    
    except Exception as e:
        logger.error(f"Error in get_proxmox_id: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))