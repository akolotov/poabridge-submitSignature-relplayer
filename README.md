submitSignature replayer for the old poabridge
====

A simple script allowing to replay submitSignature transactions sent by the old poabridge

## How to use

1. Fill `config.toml` with data referring to the JSON RPC URL, the proper directory with a keyfile and a password file where the password is in plain text.
2. Run the script adding the transaction hash to replay as the argument.

## Run by docker

```shell
docker run -ti --rm -v $(pwd):/appdata poanetwork/poabridge-ss-helper 0x1294f97f1ec2f8af7ff7315de4d451a17a2164549bf8616633f8d87b806544b9
```
