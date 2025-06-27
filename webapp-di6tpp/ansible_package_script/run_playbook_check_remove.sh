#!/bin/bash
set -e
set -x 

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

run_playbook() {
    PACKAGENAME=$1
    INSTALL_FILE=$2
    INVENTORY_FILE=$3
    PLAYBOOK_DIR=$4
    IMAGE_FILE=$5

    if [ ! -f "${PLAYBOOK_DIR}/${INSTALL_FILE}" ] || [ ! -f "${PLAYBOOK_DIR}/${INVENTORY_FILE}" ]; then
        echo " Error: Missing required file(s):"
        [ ! -f "${PLAYBOOK_DIR}/${INSTALL_FILE}" ] && echo "   - Playbook file not found: ${INSTALL_FILE}"
        [ ! -f "${PLAYBOOK_DIR}/${INVENTORY_FILE}" ] && echo "   - Inventory file not found: ${INVENTORY_FILE}"
        exit 1
    fi

    echo "Running playbook install file: ${INSTALL_FILE} ; Inventory: ${INVENTORY_FILE}; Playbook Dir: ${PLAYBOOK_DIR}"
    ansible-playbook -i "${PLAYBOOK_DIR}/${INVENTORY_FILE}" "${PLAYBOOK_DIR}/${INSTALL_FILE}" --extra-vars "ansible_python_interpreter=/usr/bin/python3"
    echo "Playbook ran successfully."

    if [ "$PACKAGENAME" == "docker" ]; then

        if [ ! -f "${PLAYBOOK_DIR}/${IMAGE_FILE}" ];then
            echo " Error: Missing required image file:"
            [ ! -f "${PLAYBOOK_DIR}/${IMAGE_FILE}" ] && echo "   - Image file not found: ${IMAGE_FILE}"
        fi 

        #garantes that image_file is not empty
        if [ -n "$IMAGE_FILE" ]; then
            echo "Running image playbook: $IMAGE_FILE"
            ansible-playbook -i "${PLAYBOOK_DIR}/${INVENTORY_FILE}" "${PLAYBOOK_DIR}/${IMAGE_FILE}" --extra-vars "ansible_python_interpreter=/usr/bin/python3"
            echo "Image playbook finished."
        fi
    fi

    if [ "$PACKAGENAME" == "chimera" ]; then
        echo "Running chimera playbook: $INSTALL_FILE"
        if [ ! -f "$BASE_DIR/ansible_package_script/src/config.toml" ] || [ ! -f "${PLAYBOOK_DIR}/src/chimera.service" ]; then
            echo "⚠️ Missing Chimera support files!"
        fi
    fi

    
}

deleting_playbook(){

    PLAYBOOK_DIR=$1
    echo "Deleting playbook dir: ${PLAYBOOK_DIR}"
    # delete the parrot-scripts parrot-on-<hostname> directory so after we can delete the whole directory
    rm -rf ${PLAYBOOK_DIR}/*

    # Check if the directory was deleted successfully
    if [ $? -eq 0 ]; then
        echo "Directory ${PLAYBOOK_DIR}/* deleted successfully."
    else
        echo "Failed to delete directory ${PLAYBOOK_DIR}/*."
        exit 1
    fi

    # delete the parrot-script directory
    rm -rf ${PLAYBOOK_DIR}
    
    if [ $? -eq 0 ]; then
        echo "Directory parrot-on-${PLAYBOOK_DIR} deleted successfully."
    else
        echo "Failed to delete directory parrot-script-on-*."
        exit 1
    fi

}

check_container(){
    HOSTIP=$1
    CONTAINERNAME=$2

    echo "Verifying if container '${CONTAINERNAME}' is running on $HOSTIP..."
        if ssh "techsupport@${HOSTIP}" "docker ps -q -f name=${CONTAINERNAME}" | grep -q .; then
            echo "Container is running. Executing interactive bash and exiting..."

            ssh -tt "techsupport@${HOSTIP}" "docker exec -it ${CONTAINERNAME} bash -c 'echo entering inside of container bash && exit'"

            echo "Exited the container."
        else
            echo "Container ${CONTAINERNAME} is not running on $HOSTIP."
        fi
}

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <hostname> <role> <packagename> [<container_name> <remote_ip> (if parrot or docker)]"
    exit 1
fi

HOSTNAME=$1
ROLE=$2
PACKAGENAME=$3
CONTAINER_NAME=$4
HOSTIP=$5

if [ "$ROLE" == "attacker" ]; then
    if [ "$PACKAGENAME" == "parrot" ]; then

        PLAYBOOK_DIR="$BASE_DIR/data/parrot-on-${HOSTNAME}"

        run_playbook "parrot" "install-on-${HOSTNAME}.yml" "inventory-on-${HOSTNAME}.yml" "$PLAYBOOK_DIR"

        if [ -n "$HOSTIP" ] && [ -n "$CONTAINER_NAME" ]; then
            check_container "${HOSTIP}" "${CONTAINER_NAME}"
        fi

        echo "Deleting the playbook"
        deleting_playbook "$PLAYBOOK_DIR"
    fi
fi

if [ "$ROLE" == "target" ]; then
    
    echo "Running playbook hostname: ${HOSTNAME} ; role: $ROLE"
    echo "target playbook"

    DIR="$BASE_DIR/data"

    if [ "$PACKAGENAME" == "docker" ]; then
        PLAYBOOK_DIR="${DIR}/docker-install-${HOSTNAME}"

        run_playbook "docker" "install-docker-on-${HOSTNAME}.yml" "inventory-on-${HOSTNAME}.yml" "$PLAYBOOK_DIR" "run-image-on-${HOSTNAME}.yml"

        if [ -n "$HOSTIP" ] && [ -n "$CONTAINER_NAME" ]; then
            check_container "${HOSTIP}" "${CONTAINER_NAME}"
        fi
        echo "Deleting the playbook"
        deleting_playbook "$PLAYBOOK_DIR"

    elif [ "$PACKAGENAME" == "chimera" ]; then  
        PLAYBOOK_DIR="${DIR}/chimera-on-${HOSTNAME}"   
        run_playbook "chimera" "install-chimera-on-${HOSTNAME}.yml" "inventory-on-${HOSTNAME}.yml" "$PLAYBOOK_DIR"
        deleting_playbook "$PLAYBOOK_DIR"
    else
        PLAYBOOK_DIR="${DIR}/${PACKAGENAME}-scripts-${HOSTNAME}"
        run_playbook $PACKAGENAME "install-${PACKAGENAME}-on-${HOSTNAME}.yml" "inventory-on-${HOSTNAME}.yml" "$PLAYBOOK_DIR"
        deleting_playbook "$PLAYBOOK_DIR"
    fi
fi