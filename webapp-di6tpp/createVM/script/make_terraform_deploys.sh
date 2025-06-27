#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR=$(cd $(dirname $0); pwd)
BASEDIR=$(cd $SCRIPT_DIR/..; pwd)

#reads the first argument (name of the file example parameters.csv)
INPUT=$1

#verifies if the file exists
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }

#gets the name of the csv file until the . and after any /
DEPLOYNAME=$(basename "$1" | cut -f 1 -d '.' )

OLDIFS=$IFS
IFS=','
 

TEMPLATE_DIR="$BASEDIR/templates"

#creates the diretory name with the csv file name
DEPLOY_DIR=deploy-$DEPLOYNAME

#remove boom. controles the lines avoiding error reading the csv file
sed -i 's/\r$//g' $INPUT

#creates the deploy directory and copy the template files for vars and provider info
mkdir $DEPLOY_DIR
cp $TEMPLATE_DIR/vars.tf $DEPLOY_DIR/
cp $TEMPLATE_DIR/vars_sensitive.tf $DEPLOY_DIR/
cp $TEMPLATE_DIR/provider.tf $DEPLOY_DIR/
cp $TEMPLATE_DIR/terraform.tfvars $DEPLOY_DIR/

#delets the main if already existed
> $DEPLOY_DIR/main.tf

echo "Content of CSV"
cat -A "$INPUT"

echo "First line of csv:"
head -n 1 "$INPUT"

# extract every variable and insert in a temporary file "f"
while read VMID VMIP VMCIDR VMGW VMBR TEMPLATE VMNAME VMCPU VMMEM VMDISK01 VMDISK01LOC VMDISK02 VMDISK02LOC VMROLE
do
    echo "reading line: VMID=$VMID, VMIP=$VMIP, TEMPLATE=$TEMPLATE, VMNAME=$VMNAME"
    
    
    echo ">> VM: VMNAME=$VMNAME | VMIP=$VMIP"
    
        f=$(mktemp)

        #verifies if it has only 1 disk (VMDISK02 with 0GB)
        if [ -z "$VMDISK02" ]; then

                sed -e "s/__VMID__/$VMID/g" \
                        -e "s/__VMIP__/$VMIP/g" \
                        -e "s/__VMCIDR__/$VMCIDR/g" \
                        -e "s/__VMGW__/$VMGW/g" \
                        -e "s/__VMBR__/$VMBR/g" \
                        -e "s/__VMNAME__/$VMNAME/g" \
                        -e "s/__VMCPU__/$VMCPU/g" \
                        -e "s/__VMMEM__/$VMMEM/g" \
                        -e "s/__VMDISK01__/$VMDISK01/g" \
                        -e "s/__VMDISK01LOC__/$VMDISK01LOC/g" \
                        -e "s/__TEMPLATE__/$TEMPLATE/g" \
                        -e "s/__HOST__/server19/g" \
                        $TEMPLATE_DIR/main_1d.tf > $f

        #saves the result in the temporary file "f" and adds it after to main.tf
                cat $f >> $DEPLOY_DIR/main.tf
                echo "" >> $DEPLOY_DIR/main.tf

        else
        # for 2 disks
                echo "got on if"

                #main_2d is the template for 2 disks while main_1d is only 1
                sed -e "s/__VMID__/$VMID/g" \
                        -e "s/__VMIP__/$VMIP/g" \
                        -e "s/__VMCIDR__/$VMCIDR/g" \
                        -e "s/__VMGW__/$VMGW/g" \
                        -e "s/__VMBR__/$VMBR/g" \
                        -e "s/__VMNAME__/$VMNAME/g" \
                        -e "s/__VMCPU__/$VMCPU/g" \
                        -e "s/__VMMEM__/$VMMEM/g" \
                        -e "s/__VMDISK01__/$VMDISK01/g" \
                        -e "s/__VMDISK01LOC__/$VMDISK01LOC/g" \
                        -e "s/__VMDISK02__/$VMDISK02/g" \
                        -e "s/__VMDISK02LOC__/$VMDISK02LOC/g" \
                        -e "s/__TEMPLATE__/$TEMPLATE/g" \
                        -e "s/__HOST__/server19/g" \
                        $TEMPLATE_DIR/main_2d.tf > $f

                cat $f >> $DEPLOY_DIR/main.tf
                echo "" >> $DEPLOY_DIR/main.tf
        fi

done < <(tail -n +2 "$INPUT") #jump the first line to ignore the header

IFS=$OLDIFS


# Create the vars_sensitive.tf file

cat <<EOL > $DEPLOY_DIR/vars_sensitive.tf
variable "pm_api_token_id" {
  description = "Token ID for the Terraform provider"
  type        = string
  sensitive   = true
}

variable "pm_api_token_secret" {
  description = "Secret for the Terraform provider"
  type        = string
  sensitive   = true
}
EOL

echo $DEPLOY_DIR