#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update and upgrade the system

echo "Updating and upgrading the system..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Python, pip, and other dependencies
echo "Installing Python, pip, and other dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv git curl

# Install Google Chrome for Selenium
echo "Installing Google Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt-get -f install -y
rm google-chrome-stable_current_amd64.deb

# Clone the repository
echo "Cloning the repository..."
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Create and activate a virtual environment
echo "Creating and activating a virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create the .env file
echo "Creating the .env file..."
cp .env.example .env

echo "----------------------------------------------------"
echo "Setup complete!"
echo "----------------------------------------------------"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your credentials: nano .env"
echo "2. Run the application: python start_app.py"
