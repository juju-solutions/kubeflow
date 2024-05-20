#!/usr/bin/env bash
set -xe

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Installing dependencies..."
pip3 install -r $SCRIPT_DIR/requirements.txt
sudo apt update

if ! command -v docker
then
  echo "Installing Docker"
  sudo snap install docker
  sudo groupadd docker
  sudo usermod -aG docker $USER
  sudo snap disable docker
  sudo snap enable docker
fi

echo "Installing parsers"
sudo snap install yq
sudo snap install jq

echo "Installing Juju"
sudo snap install juju --channel=$JUJU_CHANNEL --classic

echo "Installing pigz for compression"
sudo apt install pigz
