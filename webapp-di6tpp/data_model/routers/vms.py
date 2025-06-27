import logging
import httpx
import os
import subprocess
import asyncio

from fastapi import APIRouter, Request,Depends, HTTPException, status, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from data_model import crud
from data_model.database import get_mariadb
from typing import List
from datetime import datetime
from data_model import schemas

router = APIRouter()

#going to the templates folder. going 2 levels up to webapp-di6tpp folder
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

logger = logging.getLogger('uvicorn.error')

# Proxmox Credencials. tested with http and couldn't retrive the header
PROXMOX_API_URL = "https://10.5.0.1:8006/api2/json"
TOKEN_ID = os.getenv("PROXMOX_TOKEN_ID")
TOKEN_SECRET = os.getenv("PROXMOX_TOKEN_SECRET")

def get_user_id(db: Session):
    # Obtém um token atualizado da BD
    random_user_id= crud.get_random_user_id(db)

    print(f"random user  : {random_user_id}")
    return random_user_id

def start_role(role:str, db: Session):

    if crud.role_exists(db,role):
        print("getting the id role if already created")
        role_id = crud.get_id_by_role(db,role)
        if role_id == -1 :
            return 
        print (role_id)
    else:
        print("not created")
        role_id = crud.create_vm_role(db, role).role_id
        print(f"role {role} created in db")

    return {"role_id":role_id }


async def delete_vm_everywhere(db, vm_name: str, vm_id: int):
    
    if crud.get_vm_by_field(db, "vm_id", vm_id) is not None:
        logger.info(f"deleting vm {vm_name} with id {vm_id} from db")
        crud.delete_vm(db, vm_id)
        logger.info(f"deleted vm name: {vm_name}")
        
    DATA_DIR = "/webapp-di6tpp/data"
        
    deploy_dir = os.path.join(DATA_DIR,f"deploy-{vm_name}") 
    
    if os.path.exists(deploy_dir):
        
        cmdapply=["terraform", "destroy", f"-target=proxmox_vm_qemu.{vm_name}","-auto-approve"]
        logger.info(f"executing: {' '.join(cmdapply)}")
        
        subprocess.run(cmdapply, cwd=str(deploy_dir), check=True)
        #this way it will clean files and also directories and the deploy directory
        subprocess.run(f"rm -rf {deploy_dir}", shell=True, check=True)
    else:
        print("VM folder does not exist.")
    
    
    return True
            
        
@router.post("/delete-vm")
def delete_vm(vm_id_dic: dict = Body(...), db: Session = Depends(get_mariadb)):
        
    try:  
        #sense it is returned a Json dic, input: Object { vm_id: 4004 } we need to extract the vm_id with get
        vm_id = vm_id_dic.get("vm_id")
        logger.info(f"vm_id: {vm_id}")
        
        if not isinstance(vm_id, int):
            return JSONResponse(
                status_code=422,
                content={"detail": [{"msg": "vm_id must be an integer", "value": vm_id}]}
            )
        #terraform state list (and verify if has the vm name that we want to delete)
        #terraform destroy -target=proxmox_vm_qemu.{container_name} -> delete the container with terraform in proxmox       
      
        vm= crud.get_vm_by_field(db, "vm_id", vm_id)
        vm_name= vm.vmname 
        logger.info(f"container_name: {vm_name}")
        
        vm_deleted= asyncio.run(delete_vm_everywhere(db,vm_name,vm_id))
        
        #TODO deleting on proxmox too
       
        
        if vm_deleted and vm_name is not None :
            
            return JSONResponse(content={
                "message": f"VM {vm_name} deleted successfully",
                "vm_id": vm_id,
                "vmname": vm_name
            })
        else:
            return JSONResponse(content={
                "message": "VM not found",
                "vm_id": vm_id
            }, status_code=status.HTTP_404_NOT_FOUND)
            
    except FileNotFoundError as e:
        logger.error(f"Directory not found: {e}")
        return JSONResponse(content={"error": f"Deploy directory not found: {e}"}, status_code=400)  

    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR on Terraform services:: {e}")
        return JSONResponse(content={"error": f"Error executing Terraform services (init,plan and apply): {e}"}, status_code=500)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(
            content={"message": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

async def delete_vms(vms_to_delete: List[int] ,db: Session):
    
    # Delete VMs from the database
    for vm_id in vms_to_delete:
        crud.delete_vm(db, vm_id)
        logger.info(f"Deleted VM with ID: {vm_id}")
    return True

async def create_vms_on_db(vms_to_create: List[dict], db: Session):
    # Create VMs in the database
    for vm_data in vms_to_create:
        if crud.get_vm_by_field(db, "vmname", vm_data['vmname']) is not None:
            logger.info(f"VM {vm_data['vmname']} already exists in the database.")
            continue
        
        try:
            # validates the schema
            vm = schemas.VMCreate(**vm_data)
            # if it doesnt gets an error then will create the VM
            crud.create_vm(db, vm)
            logger.info(f"Created VM: {vm_data['vmname']}")
        except ValueError as e:
            logger.error(f"Validation failed for VM {vm_data['vmname']}: {e}")
            continue  # continues to the next VM to dont stop the process if one fails
    
    return True


async def get_all_vms(db):
    headers = {"Authorization": f"PVEAPIToken={TOKEN_ID}={TOKEN_SECRET}"}
    base_url = PROXMOX_API_URL
    
    #checking if exists the role in db
    #if not it will create
    start_role("target", db)
    start_role("attacker", db)
    
    async with httpx.AsyncClient(verify=False) as client:
        # First, get the nodes list
        nodes_url = f"{base_url}/nodes"
        nodes_response = await client.get(nodes_url, headers=headers)
        logger.info(f"Nodes response: {nodes_response.status_code}")
        if nodes_response.status_code != 200:
            logger.error(f"Failed to get nodes: {nodes_response.status_code}")
            return
        
        nodes = nodes_response.json().get("data", [])
        logger.info(nodes)
            
        vms_url = f"{base_url}/nodes/server19/qemu/"
        logger.info(f"VMs URL: {vms_url}")
        # Make the request to get VMs
        vms_response = await client.get(vms_url, headers=headers)
        
        if vms_response.status_code == 200:
            vms = vms_response.json().get("data", [])
            #lista de todos os vms no db e verificar se nao ha na var vms
            
            # Get all VMs from Proxmox
            proxmox_vm_ids = {vm['vmid'] for vm in vms}
            logger.info(f"Proxmox VM IDs: {proxmox_vm_ids}")
            
            # Get all VMs from the database
            db_vms = crud.get_vms(db)
            db_vm_ids = {vm.vm_id for vm in db_vms} #all vms in db to compare
            logger.info(f"DB VM IDs: {db_vm_ids}")
            
            #if we have on db vms that isn't on proxmox it means that was deleted there
            #so we have to delete it from db
            #we compared the ids on db with the proxmox
            vms_to_delete = set(db_vm_ids) - set(proxmox_vm_ids)
            logger.info(f"VMs to delete: {vms_to_delete}")
            
            #delete them from db
            if vms_to_delete:
                await delete_vms(vms_to_delete, db)
            
            #if we have on proxmox vms that isn't on db it means that was created there
            #so we have to add it to db with the information obtained on proxmox API
            vms_to_add = set(proxmox_vm_ids) - set(db_vm_ids)
            logger.info(f"VMs to add: {vms_to_add}")
            
            if vms_to_add:
                #sense we need to get the current state and all of that we need to get the 
                # vms variable to have all the dictionary with the information
            
                """ we will go to every single vms and check the state of the other vms.
                and add the vms on vms_to_add list to the db """
                vms_to_create = []
                for vm in vms:
                    vm_id = vm['vmid']
                    logger.info(f"updating vm {vm_id} status: {vm['status']}")
                    crud.update_vm_status(db, vm_id, vm['status'])
                    if vm_id not in vms_to_add:
                        continue
                    
                    vm_data = {
                        'vm_id': vm_id,
                        'vm_ip': "0.0.0.0", #default ip normally will be for templates/stopped vms and preventing errors
                        'vmname': vm['name'],
                        'creator_id': crud.get_user_by_field(db, "username", "UserAdmin1").user_id,# developer account will have the local machines
                        'role_id': crud.get_id_by_role(db, "target"),
                        'active_status': vm['status'],                        
                        'born_place': 'Proxmox',
                        'vm_specs': {},
                        'created_at': datetime.utcnow().isoformat(),
                    }
                    
                    if vm['status'] == 'running':
                        #we are only working on server19
                        config_url = f"{vms_url}{vm_id}/agent/network-get-interfaces"
                        logger.info(f"config_url: {config_url}")
                        
                        try:
                            ip_response = await client.get(config_url, headers=headers)
                            if ip_response.status_code == 200:
                                interfaces = ip_response.json().get('data', []).get('result', [])
                                                
                                for interface in interfaces:
                                    # Only process eth0 interface to be more precise because 
                                    # we only want ip addresses from ethernet interface
                                        if 'ip-addresses' in interface:
                                            for ip in interface['ip-addresses']:
                                                ip_addr = ip['ip-address']
                                                ip_type = ip.get('ip-address-type')
                                                
                                                # Only collect IPv4 addresses starting with 10.5
                                                if ip_type == 'ipv4' and ip_addr.startswith('10.5'):
                                                    logger.info(f"ip_addr {ip_addr}, ip_type: {ip_type}")
                                                    ip_address=ip_addr
                                                    break
                                        # Exit loop after processing eth0
                        
                                vm_data['vm_ip'] = ip_address
                                logger.info(f"{vm_data['vm_ip']} all {vm_data}")
                                logger.info(f"VM {vm_id} IPs: {ip_address}")  
                                vms_to_create.append(vm_data)
                            else:
                                logger.info(f"Failed to get VMs for server19. vm {vm_data["vmname"]} has some irregularities so it wont be added")
                                
                        except Exception as e:
                            logger.error(f"Failed to get IP for VM {vm_id}: {str(e)}")
                            return HTTPException(
                                content={
                                    "message": "Unexpected error occured", },
                                status_code=vms_response.status_code
                            )
                    elif vm['status'] == 'stopped':
                        # If the VM is not running, it means that is a template or stopped VM so we want to
                        #save it
                        vms_to_create.append(vm_data)
                        
                logger.info(f"vms_to_create {vms_to_create}")
                await create_vms_on_db(vms_to_create, db)
                
                return JSONResponse(    
                    content={
                        "message": "VMs updated successfully",
                        "vms_added": len(vms_to_create) if 'vms_to_create' in locals() else 0,
                        "vms_deleted": len(vms_to_delete) if 'vms_to_delete' in locals() else 0
                    },
                    status_code=status.HTTP_200_OK
                )
            else:
                return JSONResponse(    
                    content={
                        "message": "No VMs to updated",
                        "vms_added": len(vms_to_create) if 'vms_to_create' in locals() else 0,
                        "vms_deleted": len(vms_to_delete) if 'vms_to_delete' in locals() else 0
                    },
                    status_code=status.HTTP_200_OK
                )
        else:
            logger.error(f"Failed to get VMs error: {vms_response.status_code}")
            return JSONResponse(
                content={
                    "message": "Unexpected error occured", },
                status_code=vms_response.status_code
            )
            

