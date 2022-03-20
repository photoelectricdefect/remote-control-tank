#RPI XBOX Controller Relay

https://python-evdev.readthedocs.io/en/latest/

##Instructions

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

```bash
<python version> /usr/local/lib/<python version>/dist-packages/evdev/evtest.py
```

This script will help you map keys for your controller, now write your script