# 📁 data_model/ — Data Layer & ORM Integration for DI6TPP

This folder is responsible for defining and controlling how the web application connects to and interacts with the MariaDB database. It ensures that all user data, VM specs, Proxmox credentials, logging information, and attack metadata are:

  - Properly validated

  - Securely stored

  - Easily accessible via Python objects (using SQLAlchemy & Pydantic)

It is fundamental to the architecture of DI6TPP because it guarantees data integrity, security, and efficient communication between the FastAPI backend and the MariaDB instance.

---

## File Summary

File   Role

**crud.py**   Business logic to create, read, update, and delete DB entries

**database.py**   Establishes the database connection using SQLAlchemy

**models.py**   Defines how data is structured in the MariaDB database

**schemas.py**    Ensures frontend/backend data consistency via Pydantic validation

**security.py**   Encrypts and decrypts passwords using Blowfish encryption

---

## More Detailed

### database.py — DB Connection Manager

This file is responsible for establishing and maintaining the connection between the FastAPI backend and the MariaDB database.

  - Loads credentials from .env (DB_USER, DB_PASSWORD,DB_HOST,DB_PORT,DB_NAME)

  - Builds the SQLAlchemy connection string with pymysql

  - Creates a session factory via SessionLocal

  - Exposes get_mariadb() generator to open and safely close sessions on request

Essential for database lifecycle management inside API routes.

---

### models.py — SQLAlchemy Models (Database Schema)

Defines the full schema of the application.

Tables Included:

  User, Session: tracks users and their active sessions

  VM, VMRole: VM metadata and its relationship to a given role

  WebAppLogs, LogAnalytics: captures every action made and analyzes the impact

  ProxmoxCredentials: stores token ID/secret combos to give the webapp acess to enter proxmox 

  AttackInstructions, AttackTarget: represents actions and targets within a test

Features:

  - Uses JSON columns to store flexible VM specs

  - Leverages relationship() to make joined queries efficient and better structure

  - Designed with nullable=False constraints to enforce integrity of data

Models form the backbone of data representation for the whole system be clean and organize.

---

### schemas.py — Input/Output Validation

Built using Pydantic, this file defines the expected structure of data that:

  - Comes from the frontend/UI

  - Gets passed into API routes

  - Gets sent back to the client

Validation logic for username and password:

  - Usernames must contain only alphanumeric characters or underscores

  - Passwords must contain at least one uppercase character, only contain letters and numbers and have at least 8 digits

  - Uses Pydantic @validator decorators for in-depth field validation

  - Employs inheritance patterns (Base, Create, Out) to separate concerns

Validation lives here because it doesn’t require DB access — it keeps the app safe by preventing malformed or malicious data early in the request lifecycle like the famous SQL Injetion.

---

### security.py — Blowfish Encryption Utility

This file implements **Blowfish symmetric encryption to hash** and store sensitive data, such as passwords or API tokens.

This file:
  - Uses a SECRET_KEY from .env 
  - Ensures passwords are padded to 8-byte multiples before encryption (as required by Blowfish)
  - Securely encrypts data for storage and decrypts it when needed

Encryption is reversible, unlike hashing, which is why it's only used for fields that need to be **recoverable** (e.g., token API keys) to use on the vm creation script. Otherwise, hashed passwords (via PassLib) are preferred.

---

### crud.py — Core Logic for Data Persistence

This file contains all functions that interact directly with the database, making use of the SQLAlchemy models and session object.

Manages:
Users, VMs, Logs, Sessions, Proxmox Credentials, and Attack Targets

Includes logic for:

  Calls schemas functions to ensure for example, Username uniqueness, that is checked during user creation using binary comparison to allow case-sensitive usernames.

  Secure password encrypting and hashing using fuctions from security file when a user is created on create_user()

  Random selection functions (e.g., get_random_user_id, get_random_proxmox_credentials) are used to randomly assign resources when appropriate (useful for assigning Proxmox tokens or VMs dynamically)

  Creating logs, instructions, and session tokens with datetime.utcnow()

  Role mapping utilities like role_exists() and get_id_by_role() help validate and resolve roles for VMs.

  Logging and analytics functions (create_log, get_logs_by_vm) link user and VM actions to centralized log tables.

  VM management includes duplicate-checking (vm_already_exists) and status toggling (update_vm_status).

  Deletion and update logic is safely implemented for all core entities (users, VMs, Proxmox credentials).


This file handles all data writing/reading logic and ensures our DB is consistent, relational, and well-linked.

### routers/ 


## data_model/ is Essential because:

Acts as the interface layer between the business logic of the application and the MariaDB backend. Without this layer:

- There would be no secure user management

- VMs could not be stored, tracked, or queried

- Logs would be lost or inconsistent

- Credentials would be unprotected

It’s an indispensable part of the DI6TPP architecture, ensuring that every form submission, login, attack, or VM creation is stored, auditable, and secure.






