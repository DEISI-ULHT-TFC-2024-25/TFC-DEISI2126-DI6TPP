# Attack Script Generation
## Prerequisites

Before generating the attack script, ensure the following:
1. The `make_attack_script.sh` script is executable.
2. You have the target host's IP address (`HOST_IP`).

---

## Steps to Generate the Attack Script

Follow these steps to generate the attack script:

1. **Execute the script**  
   Run the `make_attack_script.sh` script from the command line:
   ```bash
   ./make_attack_script.sh
    ```
2. **Provide the name of the attack template**
    You will be prompted to provide the name of the attack. This name corresponds to the template directory containing the attack logic.

3. **Script Generation**
    The attack script will be generated in the following format:
    ```bash
    {attack-name-provided}-on-{HOST_IP}.py
    ```
