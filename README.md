# soracom-onyx-signal-info

Reterieve cellular signal information from Quectel's modem device via the AT command port.
The result can be output to stdout, SORACOM Air metadata service, or unified endpoint.

## Modem device

Tested with SORACOM Onyx LTE USB dongle SC-QGLC4-C1.

Maybe work with Quectel EC2x, EG9x, EG2x-G, EM05 series modems. No warranty.


## Prerequisite

Python3 and pySerial

```shell
sudo apt-get install -y python3 python3-serial
```

The user must have privilege to access the AT command port, i.e. root user or in dialout group.

## Usage

```shell
get-onyx-signal-info.py [-h] [-d DEVICE] [-i INCLUDE] [--json] [--metadata] [--udp-endpoint]
```
- `-h` : Show help and exit.
- `-d DEVICE` : Name of the AT command port to use. If not specified, `/dev/ttyUSB3` is used.
- `-i INCLUDE` : Comma-separated list of items to be output. Set `-i any` to output all available items.
- `--json` : Output the result to the standard output in JSON format.
- `--metadata` : Put the result to the SORACOM Air metadata service as tag values.
- `--udp-endpoint` : Send the result to the unified endpoint by UDP packet.

## Example

Output all available items to the standard output in JSON format:

```
./get-onyx-signal-info.py -d /dev/ttyUSB3 -i any --json
```

Put `band`, `rsrp` and `sinr` to the SORACOM Air metadata:

```
./get-onyx-signal-info.py -d /dev/ttyUSB3 -i band,rsrp,sinr --metadata
```

Send `band`, `rsrp`, `rsrq` and `sinr` to the unified endpoint in UDP packet.

```
./get-onyx-signal-info.py -d /dev/ttyUSB3 -i band,rsrp,rsrq,sinr --udp-endpoint
```
