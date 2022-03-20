# RPI XBOX Controller Relay

https://python-evdev.readthedocs.io/en/latest/

## Instructions

Open terminal

```bash
sudo bluetoothctl
power on
agent on
default-agent
```

Now turn on controller and make it discoverable, then 

```bash
scan on
```

Once device id is found 

```bash
pair xx:xx:xx:xx:xx:xx
exit
```

Controller should now be paired

type `quit` in bluetoothctl shell

Now run `install.sh`

## Mapping Controller Keys

```bash
python3 /usr/local/lib/<your python3 version>/dist-packages/evdev/evtest.py
```

Once paired and connected, this script will help you map keys for your controller

## Service

`install.sh` also installs `xbox_relay.service` on your system so that `xbox_relay.py` runs on system boot, but before running it, you should change the `WorkingDirectory` field to point to your project directory