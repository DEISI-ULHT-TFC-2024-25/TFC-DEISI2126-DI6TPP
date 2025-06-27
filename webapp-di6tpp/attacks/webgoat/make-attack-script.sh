#!/bin/bash

# Prompt user for the template directory
echo "Enter the template directory containing the attack script and parameters file:"
read -r TEMPLATE_DIR

# Validate the template directory
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Template directory '$TEMPLATE_DIR' not found. Exiting."
    exit 1
fi

# Locate the attack script and parameters CSV file
ATTACK_SCRIPT=$(find "$TEMPLATE_DIR" -type f -name "*.py" | head -n 1)
PARAMETERS_FILE=$(find "$TEMPLATE_DIR" -type f -name "*.csv" | head -n 1)

# Check if the files exist
if [ -z "$ATTACK_SCRIPT" ]; then
    echo "No Python attack script (*.py) found in the template directory. Exiting."
    exit 1
fi

if [ -z "$PARAMETERS_FILE" ]; then
    echo "No parameters CSV file (*.csv) found in the template directory. Exiting."
    exit 1
fi

echo "Using attack script: $ATTACK_SCRIPT"
echo "Using parameters file: $PARAMETERS_FILE"

# Read the CSV file
OLDIFS=$IFS
IFS=','

# Remove BOM if present
sed -i 's/\r$//g' "$PARAMETERS_FILE"

# Get the header row to identify available parameters
header=$(head -n 1 "$PARAMETERS_FILE")
declare -A param_indices

# Map column names to their indices
index=0
for param in $header; do
    param_indices[$param]=$index
    index=$((index + 1))
done

# Skip the header row and process each line
tail -n +2 "$PARAMETERS_FILE" | while read -r line; do
    # Split line into an array
    IFS=',' read -ra fields <<< "$line"

    # Extract values if the parameter exists
    HOST_IP=${fields[${param_indices[HOST_IP]:-9999}]}
    PAYLOAD=${fields[${param_indices[PAYLOAD]:-9999}]}
    PROXY_HTTP=${fields[${param_indices[PROXY_HTTP]:-9999}]}
    PROXY_HTTPS=${fields[${param_indices[PROXY_HTTPS]:-9999}]}
    CONTENT_TYPE=${fields[${param_indices[CONTENT_TYPE]:-9999}]}
    PAYLOAD_USERNAME=${fields[${param_indices[PAYLOAD_USERNAME]:-9999}]}
    PAYLOAD_PASSWORD=${fields[${param_indices[PAYLOAD_PASSWORD]:-9999}]}
    USERNAME=${fields[${param_indices[USERNAME]:-9999}]}
    PASSWORD=${fields[${param_indices[PASSWORD]:-9999}]}
    SECRET_KEY=${fields[${param_indices[SECRET_KEY]:-9999}]}
    TRANSFER_AMOUNT=${fields[${param_indices[TRANSFER_AMOUNT]:-9999}]}
    TO_ACCOUNT=${fields[${param_indices[TO_ACCOUNT]:-9999}]}
    EXPLOIT_CODE=${fields[${param_indices[EXPLOIT_CODE]:-9999}]}
    PRICE=${fields[${param_indices[PRICE]:-9999}]}
    ITEM_ID=${fields[${param_indices[ITEM_ID]:-9999}]}

    # Generate output script name
    OUTPUT_SCRIPT="${TEMPLATE_DIR}-on-${HOST_IP}.py"

    # Replace placeholders in the template
    sed -e "s|__HOST_IP__|${HOST_IP:-''}|g" \
        -e "s|__PAYLOAD__|${PAYLOAD:-''}|g" \
        -e "s|__PROXY_HTTP__|${PROXY_HTTP:-''}|g" \
        -e "s|__PROXY_HTTPS__|${PROXY_HTTPS:-''}|g" \
        -e "s|__CONTENT_TYPE__|${CONTENT_TYPE:-''}|g" \
        -e "s|__PAYLOAD_USERNAME__|${PAYLOAD_USERNAME:-''}|g" \
        -e "s|__PAYLOAD_PASSWORD__|${PAYLOAD_PASSWORD:-''}|g" \
        -e "s|__USERNAME__|${USERNAME:-''}|g" \
	-e "s|__PASSWORD__|${PASSWORD:-''}|g" \
        -e "s|__SECRET_KEY__|${SECRET_KEY:-''}|g" \
	-e "s|__TRANSFER_AMOUNT__|${TRANSFER_AMOUNT:-''}|g" \
	-e "s|__TO_ACCOUNT__|${TO_ACCOUNT:-''}|g" \
	-e "s|__EXPLOIT_CODE__|${EXPLOIT_CODE:-''}|g" \
	-e "s|__PRICE__|${PRICE:-''}|g" \
        -e "s|__ITEM_ID__|${ITEM_ID:-''}|g" \
        "$ATTACK_SCRIPT" > "$OUTPUT_SCRIPT"

    echo "Generated attack script: $OUTPUT_SCRIPT"
done

IFS=$OLDIFS

