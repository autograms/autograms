
#!/bin/bash

echo "Installing Docker..."

# Install prerequisites
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "Adding Docker repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add the current user to the docker group
echo "Allowing Docker to run without sudo..."
sudo usermod -aG docker "$USER"

# Refresh group membership for the current session
newgrp docker

echo "Docker installation complete! You can now run Docker commands without sudo."

