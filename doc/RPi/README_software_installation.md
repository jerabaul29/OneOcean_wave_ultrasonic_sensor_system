## system

```bash
sudo apt update
sudo apt upgrade
sudo apt autoremove
sudo apt install git
sudo apt install vim
sudo apt install tmux
sudo apt install tree
sudo apt install expect
sudo apt install python3-numpy
sudo apt install python3-scipy
sudo apt install python3-matplotlib
sudo apt install python3-pip
sudo apt install python3-netifaces

sudo apt-get install python3-serial  # should be installed by pip3, but somehow not working...
```

## pip

```bash
pip3 install crcmod
pip3 install netifaces

pip3 install pyserial  # should be installed by pip3, but somehow not working... see workaround install with sudo apt-get
pip3 install compress_pickle  # shoulbe be installed by pip3, but somehow not working... see workaround install by hand
```

## by hand

For compress_pickle:

```
pi@raspberrypi:~/Git $ git clone https://github.com/lucianopaz/compress_pickle.git
Cloning into 'compress_pickle'...
remote: Enumerating objects: 1639, done.
remote: Counting objects: 100% (609/609), done.
remote: Compressing objects: 100% (319/319), done.
remote: Total 1639 (delta 381), reused 494 (delta 287), pack-reused 1030
Receiving objects: 100% (1639/1639), 2.83 MiB | 566.00 KiB/s, done.
Resolving deltas: 100% (1006/1006), done.
pi@raspberrypi:~/Git $ cd compress_pickle/
pi@raspberrypi:~/Git/compress_pickle $ sudo python3 setup.py install


```
