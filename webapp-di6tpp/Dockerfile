FROM python:3.12-slim

#directory that will start on when we enter the container 
WORKDIR /webapp-di6tpp

# Install dependêncies on system for Terraform and Ansible
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    mariadb-client \
    unzip \
    nano \
    sudo \
    gnupg \
    software-properties-common \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* && \
    #proxmoxer library: To have access to proxmox info
    pip install proxmoxer requests && \
    # Install Terraform
    curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y terraform && \
    # Install Ansible
    apt-get install -y ansible && \
    # Install hping3 and tcpdump
    apt-get install -y hping3 tcpdump


COPY requirement_packages.txt .

#install the python packages with a faster method
RUN pip install --no-cache-dir -r requirement_packages.txt

# Copy files 
COPY README.md .
COPY *.py .
COPY data_model ./data_model
COPY templates ./templates
COPY static ./static
COPY config.toml .
COPY alembic.ini .
COPY createVM/ ./createVM
COPY ansible_package_script ./ansible_package_script 
COPY attacks ./attacks
COPY hpingattack.py .
COPY root_ssh/* /root/.ssh
COPY tests/ ./tests
COPY .env.test .
RUN chmod +x ./ansible_package_script/make-parrot-scripts.sh
RUN chmod +x ./ansible_package_script/make-ansible-scripts.sh
RUN chmod +x ./ansible_package_script/make-chimera-scripts.sh
RUN chmod +x ./ansible_package_script/make-docker-scripts.sh
RUN chmod 600 /root/.ssh/id_ed25519

# Define a entrypoint with flexible logic so we can run different commands
ENTRYPOINT ["/bin/bash", "-c"]

# default, runs the aplication
CMD ["python webapp.py"]