from subprocess import run
from pathlib import Path

def iniciate_the_attack():
    
    #to get the file path and then the parent(which is the folder that this file is "webapp-di6tpp in this case")
    base_dir = Path(__file__).parent
    attack_dir = base_dir / "attacks"
    csv_file = attack_dir / "parameters-attack-deploy.csv"

    # run the deploy script de deploy
    deploy_result = run(
        ["bash", "deploy-attack-script.sh", str(csv_file)],
        cwd=attack_dir,
        capture_output=True,
        text=True
    )

    if deploy_result.returncode != 0:
        return {
            "status": "error",
            "step": "deploy-script",
            "stderr": deploy_result.stderr,
            "stdout": deploy_result.stdout
        }

    # extract the last line of the csv file (ip) to get the folder exact name
    with open(csv_file, "r") as f:
        last_line = f.readlines()[-1].strip().split(",")
        attacker_ip = last_line[0]

    deploy_folder = attack_dir / f"deploy-on-{attacker_ip}"
    inventory = deploy_folder / f"inventory-{attacker_ip}.yml"
    playbook = deploy_folder / f"deploy-attack-{attacker_ip}.yml"

    # run the ansible-playbook 
    ansible_result = run(
        ["ansible-playbook", "-i", str(inventory), str(playbook)],
        cwd=deploy_folder,
        capture_output=True,
        text=True
    )

    return {
        "status": "success" if ansible_result.returncode == 0 else "failed",
        "stdout": ansible_result.stdout,
        "stderr": ansible_result.stderr
    }
