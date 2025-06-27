import logging
import os
from fastapi.responses import JSONResponse
import subprocess

logger = logging.getLogger('uvicorn.error')

ANSIBLE_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "ansible_package_script")

def create_csv_apt_file(data,csv_dir,package):
    
    apt_csv_path = os.path.join(csv_dir, "parameters-{package}.csv")
    logger.info(f"APT CSV file created! You can check it in: {apt_csv_path}")

    with open(apt_csv_path, "w") as f:
        f.write("HOSTNAME,HOSTIP,HOSTUSER,PACKAGENAME\n")
        #this can be modified to {hostname} and everything from data when created the
        # user can insert their package preferences
        f.write(f"{data['vmname']},{data['vmip']},techsupport,{package}\n")

    logger.info("apt CSV with data!")
    return apt_csv_path

def create_csv_docker_file(data,csv_dir):
    
    docker_csv_path = os.path.join(csv_dir, "parameters-docker.csv")
    logger.info(f"docker CSV file created! You can check it in: {docker_csv_path}")
    values= [data['vmname'],data['vmip'],"techsupport","webgoat/webgoat-8.0","webgoat","2222:22","8080:80","unless-stopped","UTC"]
    header= ["HOSTNAME","HOSTIP","HOSTUSER","DOCKERIMAGE","CONTAINERNAME","HOSTPORT1","HOSTPORT2","RESTARTPOLICY","TIMEZONE"]
    with open(docker_csv_path, "w") as f:
        f.write(",".join(header) + "\n")
        f.write(",".join(values) + "\n")

    logger.info("docker CSV with data!")
    logger.info(f"docker CSV file info {values}")
    return {
        "docker_csv_path": docker_csv_path,
        "vm_data": dict(zip(header, values))
    }

def create_csv_parrot_file(data,csv_dir):
    
    parrot_csv_path = os.path.join(csv_dir, "parameters-parrot.csv")
    logger.info(f"parrot CSV file created! You can check it in: {parrot_csv_path}")
    
    header = ["HOSTNAME", "HOSTIP", "HOSTUSER", "CONTAINER_NAME"]
    #!! in here you can change the data on the csv files
    values = [data["vmname"], data["vmip"], "techsupport", "parrot"]

    with open(parrot_csv_path, "w") as f:
        f.write(",".join(header) + "\n")
        f.write(",".join(values) + "\n")

    logger.info("parrot CSV with data!")

    return {
        "parrot_csv_path": parrot_csv_path,
        "vm_data": dict(zip(header, values))
    }
    
def create_csv_chimera_file(data,csv_dir):
    
    chimera_csv_path = os.path.join(csv_dir, "parameters-chimera.csv")
    logger.info(f"chimera CSV file created! You can check it in: {chimera_csv_path}")
    csvinfo=f"{data['vmname']},{data['vmip']}\n"
    
    with open(chimera_csv_path, "w") as f:
        f.write("HOSTNAME,HOSTIP\n")
        f.write(csvinfo)

    logger.info("chimera CSV with data!")
    logger.info(f"chimera CSV file info {csvinfo}")
    
    return chimera_csv_path

def run_script(script_path,csv_dir):
    # Changes for the directory where the script and template are located
    # This is necessary to ensure the script can find the template file
    os.chdir(ANSIBLE_SCRIPTS_DIR)
    
    # Check if the script exists before running it
    if os.path.isfile(script_path):
        logger.info(f"Running script: {script_path}")
        subprocess.run([script_path, csv_dir], check=True)
        logger.info(f"Playbook creation script executed successfully: {script_path}")
        
       
    else:
        raise FileNotFoundError(f"Script not found: {script_path}")


def run_playbooks(data,packagename,container_name):
    
    logger.info(f"data: {data}")
    #applying the ansible playbook
    role= data["vmrole"]
    
    if role == 'attacker':
        logger.info(f"running playbook script")
        
        if packagename == "parrot" and container_name is None:
            raise ValueError("Invalid container name")
        
        try:
            subprocess.run(
                ["bash", "run_playbook_check_remove.sh", data["vmname"], role,packagename, container_name, data["vmip"]],
                cwd=ANSIBLE_SCRIPTS_DIR,
                text=True,
                check=True
            )    
            logger.info("Script finished successfully.")
            
        except subprocess.CalledProcessError as e:
            logger.error("Script failed with return code %s", e.returncode)
            raise RuntimeError("Error executing the attacker package script.")
            #subprocess.CalledPr error will be displayed on configure_vm_endpoint() for more detail on this error

    elif role == 'target':
        
        if packagename == "docker":
            if container_name is None:
                raise ValueError("Invalid container name")
            try:
                subprocess.run(["bash", "run_playbook_check_remove.sh", data["vmname"], role, packagename, container_name, data["vmip"]], cwd=ANSIBLE_SCRIPTS_DIR, check=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error("Script failed with return code %s", e.returncode)
                raise RuntimeError("Error executing the target package script.")
        else:
            try:
                subprocess.run(["bash", "run_playbook_check_remove.sh", data["vmname"], role, packagename], cwd=ANSIBLE_SCRIPTS_DIR, check=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error("Script failed with return code %s", e.returncode)
                raise RuntimeError("Error executing the target package script.")

    logger.info(f"{packagename} playbook successfully executed for role {role}.")


#this data can be everything just need to be a dic and have all the varibles necessary to build the csv files
#such as vname,vmip, etc...
def inserting_packages(data: dict, csv_dir: str, credentials_dir: str,terraform_dir: str):
    # After creating the VM, now run the wait_for_ssh.sh script to ensure SSH is available.
    WAIT_FOR_SSH = os.path.join(credentials_dir, "wait_for_ssh.sh")
    
    if os.path.isfile(WAIT_FOR_SSH):
        logger.info(f"Running the wait_for_ssh.sh script for IP {data['vmip']}...")
        subprocess.run([WAIT_FOR_SSH, data['vmip']], cwd=str(terraform_dir), check=True)
        logger.info(f"wait_for_ssh.sh script executed successfully for IP {data['vmip']}.")
    else:
        raise FileNotFoundError(f"ERROR: wait_for_ssh.sh script not found at {WAIT_FOR_SSH}")
    
    logger.info(f"checking which vm_role is the vm: which is {data['vmrole']}")
    
    if data['vmrole'] == 'attacker':
    
        logger.info(f"starting adding attacker packages")
        parrot_csv_data= create_csv_parrot_file(data,csv_dir)
        parrot_csv_path= parrot_csv_data['parrot_csv_path']
        container_name= parrot_csv_data['vm_data']['CONTAINER_NAME']
        #script path for the specific attacker script package
        
        bash_script_path = os.path.join(ANSIBLE_SCRIPTS_DIR, "make-parrot-scripts.sh")
        logger.info(f"located bash scipt path ${bash_script_path}")
        logger.info(f"running parrot package script")
        # Executing the script for instaling necessary packages 
        run_script(bash_script_path, parrot_csv_path)
        run_playbooks(data,"parrot",container_name)
        
    elif data['vmrole'] == 'target':
        
        #instead of inserting docker between '' it could be a variable with data introduzed by user 
        # or adressing certain packages for a specific attack selected by the user
        logger.info(f"starting adding target packages")
        docker_bash_path = os.path.join(ANSIBLE_SCRIPTS_DIR, "make-docker-scripts.sh")
        logger.info(f"located bash script path ${docker_bash_path}")
        docker_csv= create_csv_docker_file(data,csv_dir)
        docker_csv_path= docker_csv["docker_csv_path"]
        container_name= docker_csv['vm_data']['CONTAINERNAME']
        run_script(docker_bash_path, docker_csv_path)
        run_playbooks(data,"docker", container_name)
        
        logger.info(f"finished tcpdump. starting chimera")
        chimera_bash_path = os.path.join(ANSIBLE_SCRIPTS_DIR, "make-chimera-scripts.sh")
        chimera_csv_path= create_csv_chimera_file(data,csv_dir)
        run_script(chimera_bash_path, chimera_csv_path)
        run_playbooks(data,"chimera", None)
        logger.info(f"ended chimera")
        
        logger.info(f"finished docker file package. starting tcpdump package")
        tcpdump_bash_path = os.path.join(ANSIBLE_SCRIPTS_DIR, "make-ansible-scripts.sh")
        apt_csv_path = create_csv_apt_file(data,csv_dir,'tcpdump')
        run_script(tcpdump_bash_path, apt_csv_path)
        run_playbooks(data,"tcpdump", None)
      
    else:
        logger.error(f"ERROR on vm_role name")
        raise RuntimeError("Error on vm_role. It is not attacker or target.")   