# 📁 webapp-di6tpp/ — FastAPI Application Core

This directory contains the core FastAPI-based server and related logic for the DI6TPP web application and contains also the DockerFile mencioned last folder README. This server acts as the main gateway for interacting with **Proxmox VMs**, initiating **simulated attacks**, **managing user and VM data**, and **integrating with Redis and MariaDB**.

It serves the frontend templates, handles **API routing**, manages **authentication tokens**, and orchestrates infrastructure tasks like **VM creation via Terraform**, attack execution using **Ansible** or custom scripts, and logging.

---

## Files Sumary

File    Purpose

webapp.py  Central FastAPI logic & UI controller

create_vm.py  Full automation pipeline for provisioning VMs

alembic.ini   Enables database migration control (schema updates)

inserting_packages.py   Auto-detects and prepares role-based tools on VMs

attack.py   Executes real attacks using structured templates

hpingattack.py    Specialized manual or scripted attack launcher



Each piece works together to turn DI6TPP into a complete infrastructure-as-attack-lab platform — scalable, configurable, and extensible.

## More in detail:

### webapp.py
This is the main entry point of the web server so one of the most important files.

Responsibilities:

  Initializes the FastAPI app
  Mounts static files and HTML templates

  Includes API routers for:

  - User management (users)

  - Proxmox credentials (proxmox_creds)

  - VM management (vms)

  Defines middleware (authentication ready but commented. needs to be changed)

  Handles exception rendering with custom error pages

  This file Provides routes for:

  - 🔐 Login/logout (/login, /logout)

  -  ⚔️ Attack initiation (/attacks, /start-attack)

  -  💻 VM management (/create-vm, /modify-vm, /remove-vm)

  -  👤 Admin panel (user creation and list viewing: /admin, /admin/create_user,/admin/all_users)

This file is essential as it brings together all backend services and controls how users and systems interact with the application.

---

### 💻 create_vm.py

Handles all logic for dynamically creating new virtual machines (VMs) using Terraform and user-submitted configurations.

Validates input JSON for required VM specs

Generates:

- A CSV file with VM specs passed on the form 

- A terraform.tfvars file with Proxmox credentials stored on User's data

- Runs Terraform scripts to:

  init, plan, apply VM configurations using make_terraform_deploys script (for more info check di6tpp/terraform-test folder)
  But it on this folder was implemented a small change on the way csv is readed. now it allows to have a header for better understanding of the csv fields.

- Saves VM metadata to the MariaDB database using SQLAlchemy models

This file is critical for VM provisioning — it's the brain behind dynamically constructing attack or target nodes.

---

### Alembic Setup

alembic.ini

Configuration for database migrations using Alembic with SQLAlchemy and MariaDB.

Uses custom migrations/ folder

Includes logging config

Connects via mysql+pymysql

Migrations allow schema evolution over time without manual DB updates.

---

### inserting_packages.py

A utility module that determines what packages or services (e.g., Docker, tcpdump) should be installed inside a VM, based on its role (attacker or target).

What it does:

  Based on VM role:

  - If attacker: generates a parrot.csv package spec

  - If target: generates CSVs for Docker, TCPDump, Chimera

  Creates structured CSV files later consumed by provisioning scripts (e.g., Ansible or bash)

This file is still in production
This module is indispensable for tailoring the VM according to the attack simulation logic.

---

### attack.py

Responsible for triggering an attack process from a previously created attacker VM to a target using the **files from di6tpp/attack folder**.

How it works: 

Reads a CSV with attack specs (parameters-attack-deploy.csv)

Runs:
  - A shell script: deploy-attack-script.sh

  - An Ansible playbook using dynamic inventory based on attacker IP

This file is still in production
This file orchestrates offensive actions in a controlled, reproducible, and testable manner.

---

### hpingattack.py

Python script used to initiate hping3-based ICMP flood attacks manually or from scripts.

Tasks performed:

  - Checks if hping3 and tcpdump are installed (installs if missing)

  - Launches a flood attack from attacker to target

  - Optionally uses SSH (via Paramiko) to execute commands remotely

This file is still in production
Useful for debugging or launching specific attack types interactively.