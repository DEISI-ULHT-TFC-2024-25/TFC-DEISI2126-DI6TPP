#!/bin/bash

#creates the inventory and playbook inde of the deploy-on-(ip of the target) folder
#using the csv information

# Input CSV and template directory
INPUT=$1
TEMPLATE_DIR="deploy-attack-template"
INVENTORY_TEMPLATE="$TEMPLATE_DIR/inventory.yml"
DEPLOY_TEMPLATE="$TEMPLATE_DIR/deploy-attack.yml"

# Check for input file and template files
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
[ ! -f $INVENTORY_TEMPLATE ] && { echo "Template file $INVENTORY_TEMPLATE not found"; exit 99; }
[ ! -f $DEPLOY_TEMPLATE ] && { echo "Template file $DEPLOY_TEMPLATE not found"; exit 99; }

OLDIFS=$IFS
IFS=','

# Remove BOM if present
sed -i 's/\r$//g' $INPUT

# Read the CSV file and process each line
while read ATTACKER_HOST_IP HOST_USER ATTACK_SCRIPT
do
    # Skip header line if present. the $ is a variable to assemble the order of the element in the line (attacker), second (host_user) ... 
    #which will be useful for the next line because it already was the order fo the variables
    if [[ "$ATTACKER_HOST_IP" == "ATTACKER_HOST_IP" && "$HOST_USER" == "HOST_USER" && "$ATTACK_SCRIPT" == "ATTACK_SCRIPT" ]]; then
        continue
    fi
    echo "Read: $ATTACKER_HOST_IP, $HOST_USER, $ATTACK_SCRIPT"

    # Define output directory
    OUTPUT_DIR="deploy-on-${ATTACKER_HOST_IP}"
    mkdir -p $OUTPUT_DIR

    # Goes to inventory.yml file and changes the variables to their real values
    INVENTORY_FILE="$OUTPUT_DIR/inventory-${ATTACKER_HOST_IP}.yml"
    sed -e "s|__ATTACKER_HOST_IP__|$ATTACKER_HOST_IP|g" \
        -e "s|__HOST_USER__|$HOST_USER|g" \
        $INVENTORY_TEMPLATE > $INVENTORY_FILE
    echo "Generated $INVENTORY_FILE"

    # Generate upload template file with updated placeholders
    DIR_NAME="${ATTACK_SCRIPT%%/*}"
    DEPLOY_FILE="$OUTPUT_DIR/deploy-attack-${ATTACKER_HOST_IP}.yml"

    sed -e "s|__ATTACKER_HOST_IP__|$ATTACKER_HOST_IP|g" \
    -e "s|__HOST_USER__|$HOST_USER|g" \
    -e "s|__HOST_IP__|$HOST_IP|g" \
    -e "s|__USERNAME__|$USERNAME|g" \
    -e "s|__SECRET_KEY__|$SECRET_KEY|g" \
    -e "s|__DIR_NAME__|$DIR_NAME|g" \
    -e "s|__ATTACK_SCRIPT__|$ATTACK_SCRIPT|g" \
    $INVENTORY_TEMPLATE > $INVENTORY_FILE
    
    echo "Generated $DEPLOY_FILE"

done < $INPUT

IFS=$OLDIFS

echo "Generated deployment files in $OUTPUT_DIR"
