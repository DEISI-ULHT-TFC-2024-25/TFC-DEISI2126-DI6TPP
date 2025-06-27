#!/bin/bash

INPUT=$1
TEMPLATE_DIR="apt-template"
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

while read HOSTNAME HOSTIP HOSTUSER PACKAGENAME
do
    # Skip header line if present
    [[ "$HOSTNAME" == "HOSTNAME" ]] && continue

    # goes 1 level above so we can reach data volume
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_DIR="$(dirname "$SCRIPT_DIR")"

    # Define the output directory for the package
    OUTPUT_DIR="$BASE_DIR/data/${PACKAGENAME}-scripts-${HOSTNAME}"
    mkdir -p $OUTPUT_DIR

    # Generate output file names
    INSTALL_FILE="$OUTPUT_DIR/install-${PACKAGENAME}-on-${HOSTNAME}.yml"
    INVENTORY_FILE="$OUTPUT_DIR/inventory-on-${HOSTNAME}.yml"

    # Replace placeholders in the install template and save to the output file
    sed -e "s/__HOSTNAME__/$HOSTNAME/g" \
        -e "s/__PACKAGENAME__/$PACKAGENAME/g" \
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

echo "Ansible files generated in respective $PACKAGENAME-ansible-scripts directories"