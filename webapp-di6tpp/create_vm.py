import logging
import os
import subprocess

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Request,HTTPException


from data_model.database import get_mariadb
from data_model import schemas
from data_model import crud
from inserting_packages import inserting_packages
from datetime import datetime

logger = logging.getLogger('uvicorn.error')


#Terraform directories
#webapp-di6tpp
TERRAFORM_DIR = "/webapp-di6tpp/createVM"
DATA_DIR = "/webapp-di6tpp/data"
CSV_DIR = os.path.join(TERRAFORM_DIR, "csvs")
SCRIPT_DIR= os.path.join(TERRAFORM_DIR, "script")
CREDENTIALS_DIR =  os.path.join(TERRAFORM_DIR, "templates")
PLAN_DIR = os.path.join(DATA_DIR, "data")

PROXMOX_API_URL = "https://10.5.0.1:8006/api2/json"

#check if every directory exists
def setup_directories():
    
    # check if the folder exists if doesn't exists it will create
    for directory in [TERRAFORM_DIR, CSV_DIR, CREDENTIALS_DIR, DATA_DIR,SCRIPT_DIR]:
        os.makedirs(directory, exist_ok=True)
        
        
def validate_vm_data(data):
    
    required_fields = [
        "vm_id", "vmip", "vmcidr", "vmgw", "vmbr", 
        "template", "vmname", "vmcpu", "vmmem", "vmdisk01",'vmrole'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    #just for templates and environment vms
    if data["vmip"] == "0.0.0.0":
        raise ValueError("VMID cannot be 0.0.0.0")
    
    logger.info("VM values validated!")
    return data

def create_csv_file(data):
    
    csv_path = os.path.join(CSV_DIR, f"{data['vmname']}.csv")
    logger.info(f"CSV file created! You can check it in: {csv_path}")

    with open(csv_path, "w") as f:
        f.write("VMID,VMIP,VMCIDR,VMGW,VMBR,TEMPLATE,VMNAME,VMCPU,VMMEM,VMDISK01,VMDISK01LOC,VMDISK02,VMDISK02LOC\n")
        f.write(f"{data['vm_id']},{data['vmip']},{data['vmcidr']},{data['vmgw']},{data['vmbr']},"
                f"{data['template']},{data['vmname']},{data['vmcpu']},{data['vmmem']},"
                f"{data['vmdisk01']},{data.get('vmdisk01loc', 'local-lvm')},"
                f"{data.get('vmdisk02', '50')},{data.get('vmdisk02loc', 'local-lvm')},{data['vmrole']}\n")

    logger.info("CSV with data!")
    return csv_path


def create_tfvars_file(user_id, encripted_private_key):
    tfvars_path = os.path.join(CREDENTIALS_DIR, "terraform.tfvars")
    #private_key= decrypt_password(encripted_private_key) insert that when proxmox credential can be modified
    
    logger.info(f"terraform.tfvars created! You can check it in: {tfvars_path}")

    with open(tfvars_path, "w") as f:
        f.write(f'pm_api_token_id = "{user_id}"\n')
        f.write(f'pm_api_token_secret = "{encripted_private_key}"\n')

    logger.info("Credencials saved in terraform.tfvars!")
    return tfvars_path


def run_terraform_scripts(script_path, csv_path, plan_file, tfvars_path,name):
    try:    
        #cwd is because csv is inside of "createVM"
        logger.info(f"Executing '{script_path} {csv_path}' on {TERRAFORM_DIR}")
        subprocess.run([script_path, csv_path], cwd=DATA_DIR, check=True)
        logger.info(f"Executed '{script_path} {csv_path}' on {TERRAFORM_DIR}")
        
        #name of the directory that will be created for the container files on make_terraform_deploys.sh
        #checking if deploy_parameters were good constructured
        deploy_dir = os.path.join(DATA_DIR,f"deploy-{name}") 
        os.makedirs(deploy_dir, exist_ok=True)
        
        
        logger.info(f"Executing 'terraform init' on {deploy_dir}")
        subprocess.run(["terraform", "init"], cwd=deploy_dir, check=True)
        logger.info(f"Executed 'terraform init' on {deploy_dir}")
            
        if not tfvars_path:
            raise FileNotFoundError(f"ERROR: terraform.tfvars file not found in {deploy_dir}")

        if not plan_file:
            raise FileNotFoundError(f"ERROR: plan_file file not found in {DATA_DIR}")

        
        logger.info(f"Executing 'terraform plan' on {deploy_dir}")
        logger.info(f"plan_file: {plan_file}")
        
        cmd= ["terraform", "plan", "-out", str(plan_file), "-var-file", str(tfvars_path)]
        logger.info(f"executing: {' '.join(cmd)}")
        subprocess.run(
            cmd,
            cwd=str(deploy_dir),
            check=True
        )
        
        logger.info(f"Terraform Plan created in: {plan_file}")
    
    
        if os.path.exists(plan_file):
            logger.info(f"Terraform plan saved successfully: {plan_file}")
        else:
            raise FileNotFoundError(f"Plan file was not created: {plan_file}")


        logger.info(f"Executed 'terraform plan' on {deploy_dir}")
        logger.info(f"Executing 'terraform apply -auto-approve' on {deploy_dir}")
        
        cmdapply=["terraform", "apply", "-auto-approve", plan_file]
        logger.info(f"executing: {' '.join(cmdapply)}")
        
        #use the plan file so the apply dont need to rebuild it.
        subprocess.run(cmdapply, cwd=str(deploy_dir), check=True)

        logger.info(f"Executed 'terraform apply -auto-approve' on {deploy_dir}")
        
        logger.info("Terraform executed!")
        
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR on Terraform services: {e}")
        raise RuntimeError("ERROR on Terraform services.")
    
async def generate_vm(request: Request, db, user_tokenid: int):
    
    data= await request.json()

    csv_path = create_csv_file(data)
        
    proxmox_object = crud.get_proxmox_credential_by_promoxid(db, user_tokenid)
    
    if proxmox_object is None :
        logger.error(f"No Proxmox Credentials with password found. Please ask for an admin to add them.")
        raise ValueError("No Proxmox credentials with token found.")
    
    logger.info(f"🔑 Random API Key: {proxmox_object}")
    access_token_id= f"{proxmox_object.proxmox_user}!{proxmox_object.token_id}"
    logger.info(f"access token id: {access_token_id}")
    
    token_secret=proxmox_object.token_key

    logger.info(f"validating token split create: {access_token_id}/ secret {token_secret}")

    tfvars_path = str(create_tfvars_file(access_token_id, token_secret))
        
    # executing the comands in the terraform location files for checking 
    # errors and start executing the terraform script
    script_path = os.path.join(SCRIPT_DIR, "make_terraform_deploys.sh")
    plan_file = os.path.join(PLAN_DIR, f"{data['vmname']}.tfplan")
    
    #create a empty file for the plan file
    if not os.path.exists(plan_file):
        with open(plan_file, 'w') as f:
            pass

    logger.info("Start running the terraform services")
    
    #Executing init,plan and apply terraform to create the VM
    run_terraform_scripts(script_path, csv_path, plan_file, tfvars_path, data["vmname"])
    return {"message": "VM provisioned successfully"}      
        
      
async def create_vm_entry(data, db, userid: int):
    
    # reading the json
    print(f"We received this data: {data}")
    logger.debug(f"We received this data: {data}")

    #check if every directory exists
    setup_directories()
    
        
    logger.info(f" Checking containers:")
    #Validate the data with our requirements and proxmox exiting containers

    # Validate if we have everything we need
    validate_vm_data(data)
 
    validated = schemas.VMCreate(
        vm_id=data["vm_id"],
        vmname=data["vmname"],
        creator_id=userid,  
        vm_ip=data["vmip"],
        role_id= crud.get_id_by_role(db,data["vmrole"]),     
        active_status="running",
        vm_specs=data,
        born_place="Webapp",
        created_at=datetime.utcnow().isoformat()
    )
    
    logger.info(f"get_all_necessary_items (building  vm_role and getting user)")

    vm_data = validated.dict()
    vm_data["creator_id"] = userid
    vm_data["role_id"] = crud.get_id_by_role(db, data["vmrole"])
    return crud.create_vm(db, schemas.VMCreate(**vm_data))


async def configure_vm(request: Request):
    data= await request.json()

    logger.info("Start running the packages scripts")
    #inserting the necessary roles packages to the vm
    inserting_packages(data,CSV_DIR,CREDENTIALS_DIR,TERRAFORM_DIR)  
    
    return {"message": "VM created successfully!"}
