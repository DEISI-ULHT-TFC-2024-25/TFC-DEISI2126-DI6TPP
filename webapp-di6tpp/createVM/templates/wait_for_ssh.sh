#!/bin/bash

VMIP=$1

timeout=50
interval=10
start=$(date +%s)

echo "Verifying conectivity for ${VMIP}..."
ping_ok=0
ssh_port_ok=0
ssh_ready=0

while true; do
  now=$(date +%s)
  elapsed=$((now - start))

  echo "Elapsed time: $elapsed seconds"
  echo "Timeout: $timeout seconds"


  # Verify the time execution to check if extended the timeout
  if (( $elapsed >= $timeout )); then
    echo "Timeout reached ($timeout seconds). SSH not available."
    exit 1
  fi

   if [ $ping_ok -eq 0 ]; then
    if ping -c 1 -W 1 ${VMIP} >/dev/null 2>&1; then
      echo " Ping OK for ${VMIP}"
      ping_ok=1
    else
      echo "Still no ping..."
      sleep $interval
      continue
    fi
    fi

   if [ $ssh_port_ok -eq 0 ] && [ $ping_ok -eq 1 ]; then
    if nc -z -w2 ${VMIP} 22; then
      echo " Port 22 open in ip ${VMIP}"
      ssh_port_ok=1
    else
      echo "Port 22 still closed..."
      sleep $interval
      continue
    fi
    fi


   # Test SSH
  if  [ $ssh_port_ok -eq 1 ] && timeout 5 ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 techsupport@${VMIP} "echo SSH is ready" >/dev/null 2>&1; then
    echo " SSH available in ip ${VMIP}!"
    break
  else
    echo "waiting for SSH to answer..."
  fi

  sleep $interval
done