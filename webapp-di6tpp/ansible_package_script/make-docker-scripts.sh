#!/bin/bash

INPUT=$1
TEMPLATE_DIR="docker-template"
INSTALL_DOCKER_TEMPLATE="$TEMPLATE_DIR/install-docker.yml"
INSTALL_IMAGE_TEMPLATE="$TEMPLATE_DIR/install-image.yml"
INVENTORY_TEMPLATE="$TEMPLATE_DIR/inventory.yml"

# Check for input file and template files
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
[ ! -f $INSTALL_DOCKER_TEMPLATE ] && { echo "Install template file $INSTALL_DOCKER_TEMPLATE not found"; exit 99; }
[ ! -f $INSTALL_IMAGE_TEMPLATE ] && { echo "Install template file $INSTALL_IMAGE_TEMPLATE not found"; exit 99; }
[ ! -f $INVENTORY_TEMPLATE ] && { echo "Inventory template file $INVENTORY_TEMPLATE not found"; exit 99; }

OLDIFS=$IFS
IFS=','

# Remove BOM if present
sed -i 's/\r$//g' $INPUT

while read HOSTNAME HOSTIP HOSTUSER DOCKERIMAGE CONTAINERNAME HOSTPORT1 HOSTPORT2 RESTARTPOLICY TIMEZONE
do
    # Skip header line if present
    [[ "$HOSTNAME" == "HOSTNAME" ]] && continue

    # goes 1 level above so we can reach data volume
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_DIR="$(dirname "$SCRIPT_DIR")"

    # Define the output directory for the configuration files
    OUTPUT_DIR="$BASE_DIR/data/docker-install-${HOSTNAME}"
    mkdir -p $OUTPUT_DIR

    # Generate output file names
    INSTALL_DOCKER_FILE="$OUTPUT_DIR/install-docker-on-${HOSTNAME}.yml"
    INSTALL_IMAGE_FILE="$OUTPUT_DIR/run-image-on-${HOSTNAME}.yml"
    INVENTORY_FILE="$OUTPUT_DIR/inventory-on-${HOSTNAME}.yml"

    # Always generate Docker installation file
    sed -e "s|__HOSTNAME__|$HOSTNAME|g" \
        $INSTALL_DOCKER_TEMPLATE > $INSTALL_DOCKER_FILE
    echo "Generated $INSTALL_DOCKER_FILE"

    # If image and related values are present, generate run-image file
    if [[ -n "$DOCKERIMAGE" && -n "$CONTAINERNAME" && -n "$HOSTPORT1" && -n "$HOSTPORT2" && -n "$RESTARTPOLICY" && -n "$TIMEZONE" ]]; then
        sed -e "s|__HOSTNAME__|$HOSTNAME|g" \
            -e "s|__DOCKERIMAGE__|$DOCKERIMAGE|g" \
            -e "s|__CONTAINERNAME__|$CONTAINERNAME|g" \
            -e "s|__HOSTPORT1__|$HOSTPORT1|g" \
            -e "s|__HOSTPORT2__|$HOSTPORT2|g" \
            -e "s|__RESTARTPOLICY__|$RESTARTPOLICY|g" \
            -e "s|__TIMEZONE__|$TIMEZONE|g" \
            $INSTALL_IMAGE_TEMPLATE > $INSTALL_IMAGE_FILE
        echo "Generated $INSTALL_IMAGE_FILE"
    fi

    # Replace placeholders in the inventory template and save to the output file
    sed -e "s|__HOSTNAME__|$HOSTNAME|g" \
        -e "s|__HOSTIP__|$HOSTIP|g" \
        -e "s|__HOSTUSER__|$HOSTUSER|g" \
        -e "s|__TIMEZONE__|$TIMEZONE|g" \
        $INVENTORY_TEMPLATE > $INVENTORY_FILE
    echo "Generated $INVENTORY_FILE"

done < $INPUT

IFS=$OLDIFS

echo $OUTPUT_DIR