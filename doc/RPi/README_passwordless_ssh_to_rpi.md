Generate a new key:

```
$ ssh-keygen
```

We name the key ```id_rsa_rpi_sl```, we use the password ```password_rpi_ug_sl```.

Public key content is:

```
$ cat /home/jrmet/.ssh/id_rsa_rpi_sl.pub 
REDACTED
```

Private key content is:

```
$ cat /home/jrmet/.ssh/id_rsa_rpi_sl
-----BEGIN OPENSSH PRIVATE KEY-----
REDACTED
-----END OPENSSH PRIVATE KEY-----
```

To add to the RPI:

```
ssh-copy-id -f -i /home/jrmet/.ssh/id_rsa_rpi_sl.pub pi@10.42.1.55
```
