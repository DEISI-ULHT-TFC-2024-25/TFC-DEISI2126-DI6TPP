#!/bin/bash

INPUT=$1
TEMPLATE_DIR="chimera-template"
INSTALL_TEMPLATE="$TEMPLATE_DIR/install.yml"
INVENTORY_TEMPLATE="$TEMPLATE_DIR/inventory.yml"

# Check for input file and template files
if [[ ! -f $INPUT ]]; then echo "Error: Input file '$INPUT' not found."; exit 99; fi
if [[ ! -f $INSTALL_TEMPLATE ]]; then echo "Error: Install template file '$INSTALL_TEMPLATE' not found."; exit 99; fi
if [[ ! -f $INVENTORY_TEMPLATE ]]; then echo "Error: Inventory template file '$INVENTORY_TEMPLATE' not found."; exit 99; fi

# Remove BOM and ensure proper line endings
sed -i 's/\r$//g' "$INPUT"

OLDIFS=$IFS
IFS=','

while read -r HOSTNAME HOSTIP
do
    # Skip header line dynamically
    [[ "$HOSTNAME" == "HOSTNAME" ]] && continue

    # goes 1 level above so we can reach data volume
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_DIR="$(dirname "$SCRIPT_DIR")"

    # Define the output directory
    OUTPUT_DIR="$BASE_DIR/data/chimera-on-${HOSTNAME}"
    mkdir -p "$OUTPUT_DIR"

    # Generate output file names
    INSTALL_FILE="$OUTPUT_DIR/install-chimera-on-${HOSTNAME}.yml"
    INVENTORY_FILE="$OUTPUT_DIR/inventory-on-${HOSTNAME}.yml"

    # Check if files already exist and ask before overwriting
    for FILE in "$INSTALL_FILE" "$INVENTORY_FILE"; do
        if [[ -f $FILE ]]; then
            read -p "File '$FILE' exists. Overwrite? (y/n): " CHOICE
            [[ $CHOICE != "y" ]] && echo "Skipping $FILE" && continue
        fi
    done

    # Create Ansible install script
    sed -e "s/__HOSTNAME__/$HOSTNAME/g" "$INSTALL_TEMPLATE" > "$INSTALL_FILE"
    echo "Generated $INSTALL_FILE"

    # Create Ansible inventory file
    sed -e "s/__HOSTNAME__/$HOSTNAME/g" \
        -e "s/__HOSTIP__/$HOSTIP/g" \
        "$INVENTORY_TEMPLATE" > "$INVENTORY_FILE"
    echo "Generated $INVENTORY_FILE"

done < "$INPUT"

IFS=$OLDIFS

echo "Ansible files generated in $OUTPUT_DIR  directory."