sudo apt install python-dev
sudo apt install python-pip
sudo pip install evdev
cp -frT ./xbox_relay.service /etc/systemd/system/xbox_relay.service
sudo systemctl enable xbox_relay
sudo systemctl restart xbox_relay