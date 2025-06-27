# 📁 `webapp/` — DI6TPP Web Application Container

This folder contains the **Docker web application component** of the di6tpp project which is a cybersecurity-oriented platform designed to simulate and analyze offensive and defensive strategies using a virtualized 6G-inspired environment.

The **webapp** is the main user interface (built using **FastAPI**) where users can interact with backend services, initiate attacks, configure virtual machines (via Proxmox), and manage infrastructure components dynamically.

This webapp has the following containers via Docker and orchestrated using Docker Compose:

- 🔧 **FastAPI backend**  
- 🐬 **MariaDB** database (external container)  
- 🔁 **Redis** for caching & messaging  
- ⚙️ **Terraform & Ansible** (installed inside the container for automation)  

---

## Running the Container

Steps that you need to follow to run the container:

### 1. 📄 .env File

You need to create a `.env` file and ask a administrator for the following required credentials to be able to acess all the webapp:

```env
DB_ROOT_PASSWORD=your_root_password
DB_NAME=your_db_name
DB_USER=your_user
DB_PASSWORD=your_password
PROXMOX_TOKEN_ID=your_token_id
PROXMOX_TOKEN_SECRET=your_token_secret
```

### 2. Build & Run the webapp container

From the **webapp directory**, run:

```bash
docker compose up --build
```

The webapp will be accessible on:

📍 http://localhost:8081

---

## Webapp Container Info

### Docker Overview

### Dockerfile Highlights:

Installs:

- Python dependencies from `requirement_packages.txt`  
- System tools: `terraform`, `ansible`, `mariadb-client`, `hping3`, `tcpdump`  
- Copies source code and configuration files  
- Entrypoint: `webapp.py`


#### Docker Compose Services

- `mariadb`: MariaDB database with persistent volume  
- `redis`: In-memory store for message brokering  
- `webapp`: Builds from `./webapp-di6tpp` and runs the FastAPI app with volume mounting  

---


## ⚙️ Configuration

### `config.toml`

```toml
[webapp]
port = 8081
log_level = "TRACE"
```

- Sets the webapp port and logging level


### `settings.py`

Defines advanced logging using Python’s `logging.config`.

Logging features:

- Stream and file logging  
- Rotating file logs (1MB, 3 backups)  
- Custom format including timestamps, file names, and line numbers  
- Fine-grained control over Uvicorn logs  

---

## 📚 Dependencies

All Python packages are defined in `requirement_packages.txt`.

Main packages:

- `fastapi`, `uvicorn`, `jinja2`, `sqlalchemy`, `alembic`  
- `proxmoxer` (API wrapper for Proxmox)  
- `redis`, `httpx`, `python-dotenv`, `paramiko`, `pycryptodome`  

---

## 📝 Notes

The container mounts local folders for persistent data:

- Database data  
- Webapp migrations  
- Webapp `data/` directory (for storing persistent application data)  

Environment variables allow flexible configuration between development and production.

---


## More About

This webapp is designed to be extended with:

- **User authentication**  
  Implement secure session or token-based authentication mechanisms for user access.

- **Attack orchestration modules**  
  Enable users to launch and monitor simulated offensive actions against virtual targets.

- **VM lifecycle management via Proxmox**  
  Automate creation, configuration, startup, and teardown of virtual machines using the Proxmox API.

- **Redis-based async task queues**  
  Offload long-running tasks and improve responsiveness through background job processing.

- **MariaDB data modeling and optimization**  
  Define relational schemas to store users, logs, attack metadata, and system states; optimize queries and ensure data integrity.