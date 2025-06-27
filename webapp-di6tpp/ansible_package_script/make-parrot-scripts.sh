#!/bin/bash
#the input is the csv file
INPUT=$1
TEMPLATE_DIR="parrot-docker-template"
INSTALL_TEMPLATE="$TEMPLATE_DIR/install.yml"
INVENTORY_TEMPLATE="$TEMPLATE_DIR/inventory.yml"

# Check for input file and template files
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
[ ! -f $INSTALL_TEMPLATE ] && { echo "Install template file $INSTALL_TEMPLATE not found"; exit 99; }
[ ! -f $INVENTORY_TEMPLATE ] && { echo "Inventory template file $INVENTORY_TEMPLATE not found"; exit 99; }

OLDIFS=$IFS
IFS=','

# Remove BOM if present
sed -i 's/\r$//g' $INPUT

while read HOSTNAME HOSTIP HOSTUSER CONTAINER_NAME
do
    # Skip header line if present
    [[ "$HOSTNAME" == "HOSTNAME" ]] && continue

    # goes 1 level above so we can reach data volume
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_DIR="$(dirname "$SCRIPT_DIR")"

    # Define the output directory for the Docker installation scripts
    OUTPUT_DIR="$BASE_DIR/data/parrot-on-${HOSTNAME}"
    mkdir -p $OUTPUT_DIR

    # Generate output file names
    INSTALL_FILE="$OUTPUT_DIR/install-on-${HOSTNAME}.yml"
    INVENTORY_FILE="$OUTPUT_DIR/inventory-on-${HOSTNAME}.yml"

    # Replace placeholders in the install template and save to the output file
    sed -e "s/__HOSTNAME__/$HOSTNAME/g" \
        -e "s/__CONTAINER_NAME__/$CONTAINER_NAME/g" \
        $INSTALL_TEMPLATE > $INSTALL_FILE
    echo "Generated $INSTALL_FILE"

    # Replace placeholders in the inventory template and save to the output file
    sed -e "s/__HOSTNAME__/$HOSTNAME/g" \
        -e "s/__HOSTIP__/$HOSTIP/g" \
        -e "s/__HOSTUSER__/$HOSTUSER/g" \
        $INVENTORY_TEMPLATE > $INVENTORY_FILE
    echo "Generated $INVENTORY_FILE"

done < $INPUT

IFS=$OLDIFS

echo "Scripts generated in ${OUTPUT_DIR} directory."