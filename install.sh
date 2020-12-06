#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "please run as root"
  exit 1
fi

cp paybyphones_autopay.py /usr/local/bin/paybyphones_autopay.py
cp paybyphones.service /etc/systemd/system/paybyphones.service
mkdir -p /var/lib/paybyphones
cp config.yaml /var/lib/paybyphones/config.yaml

systemctl start paybyphones.service
systemctl enable paybyphones.service
