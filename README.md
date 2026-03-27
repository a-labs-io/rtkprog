# rtkprog

Tool for flashing Realtek RTL87x2x Bluetooth SoCs via UART

## Installation / Dependencies

Using `uv` 

```shell
$ uv sync
```

Using `pip` 

```shell
$ pip install -r requirements.txt
```

## Firmware Blobs

In order to be able to flash firmware, you need to get the firmware loader blobs from the official Realtek MPCLI tool [RealMCU website](https://www.realmcu.com) or from the [Realtek Zephyr project repository](https://github.com/rtkconnectivity/realtek-zephyr-project/tree/eef376419cfb40c0bef85a63e04d775687516796/tool/bin/bee/mpcli/fw).

Once extracted to this tool's `fw/` directory, the structure should look like this (same level as `rtkprog.py`):

```shell
$ tree fw
fw
├── flash_avl.bin
├── RTL8762C_FW_B.bin
├── RTL8762D_FW_A.bin
├── RTL8762E_FW_B.bin
├── RTL8762G_FW_A.bin
├── RTL8762G_FW_B.bin
└── RTL8762H_FW_A.bin


```

## Essential System Images

Before being able to write and run Zephyr application images, some essential system images (such as Bootloader patches, System patches, and Configuration files) must be programmed in advance, which can be downloaded from Zephyr's [hal_realtek](https://github.com/rtkconnectivity/realtek-zephyr-project/tree/eef376419cfb40c0bef85a63e04d775687516796/bin) repository.

## Hardware Setup & Auto-Reset

This tool supports auto-reset via serial RTS / DTR lines. This allows switching between bootloader mode and normal application mode in software without physical interaction with the board (e.g. via buttons / switches / jumpers). For this, the following wiring is required:

| USB-UART Pin | RTL87x2x Pin | Pin Name | Description                            |
| ------------ | ------------ | -------- | -------------------------------------- |
| RTS          | RESET        | RESET    | Active-low chip-reset input            |
| DTR          | P0_3         | LOG/BOOT | Boot mode select (low = download mode) |

## Usage

```
./rtkprog.py --help
usage: rtkprog [-h] [-p PORT] [-b BAUD] [-v | -q] COMMAND ...

Tool for programming Realtek RTL8762x BT SoCs

positional arguments:
  COMMAND
    write          Write binary file(s) to flash (auto-erases required sectors)
    read           Read flash to file(s)
    erase          Erase flash sections or entire chip (default)
    mac            Read or write the MAC address in flash
    reset          Reset the chip
    terminal       Reset the chip and open bidirectional connection to serial port
    efuse          Read eFuse CRC16 status

options:
  -h, --help       show this help message and exit
  -p, --port PORT  Serial port (default: /dev/ttyUSB0)
  -b, --baud BAUD  Baud rate for binary transfer and terminal (default: 921600).
  -v               Increase verbosity (-v = INFO, -vv = DEBUG)
  -q, --quiet      Suppress all output below ERROR
```

### Flash Write

One or multiple binaries can be written to different flash locations using the format: `-w <ADDRESS,SEEK,FILE>`

Optionally, a MAC address can be provided with `--mac`, which will be patched during flashing. Using `--mac auto` preserves the existing MAC address. Using this parameter can save a write cycle compared to using  `rtkprog mac --mac XX:XX:XX:XX:XX:XX` when the configuration file is being flashed anyway.

The writing process automatically erases the required flash pages before performing the write operation.

```bash
./rtkprog.py -v \
    --port /dev/ttyUSB0 \
    --baud 921600 \
    write \
    --mac XX:XX:XX:XX:XX:XX \
    -w 0x4001000,0x200,bin/rtl87x2g/configFile_x.x.x.x-hash.bin \
    -w 0x4002000,0x200,bin/rtl87x2g/BANK0_boot_patch_MP_release_x.x.x.x_hash.bin \
    -w 0x400a000,0x200,bin/rtl87x2g/BANK1_boot_patch_MP_release_x.x.x.x_hash.bin \
    -w 0x4012000,0x200,bin/rtl87x2g/OTAHeader_Bank0_x.x.x.x-hash.bin \
    -w 0x4013000,0x200,bin/rtl87x2g/BANK0_sys_patch_MP_release_x.x.x.x_hash.bin \
    -w 0x401b000,0x200,bin/rtl87x2g/bt_stack_patch_MP_master_x.x.x.x_hash.bin \
    -w 0x402d000,0x0,zephyr.bin
```

> **Note:** For the system images an offset `0x200` is used, because they contain a 512 bytes header.

### Flash Read

The entire flash memory of the chip can be dumped to a file, or specific sections can be read using the following command, format:  `<ADDRESS,SIZE,FILE>`

```bash
./rtkprog.py -v \
    --port /dev/ttyUSB0 \
    --baud 921600 \
    read -r 0x4001000,0x1000,image.bin
```

### Flash Erase

Erases one or multiple regions in flash, format: `<ADDRESS,SIZE>`

```bash
./rtkprog.py -v \
    --port /dev/ttyUSB0 \
    erase -r 0x4001000,0x1000
```

### Read MAC Address

Read/write the MAC address.

```bash
./rtkprog.py -v \
    --port /dev/ttyUSB0 \
    mac --mac XX:XX:XX:XX:XX:XX
```

### Read eFuse Status

This command can be used to determine if eFuses have been burned (CRC16 = `0xFFFF` = not burned).

```bash
./rtkprog.py -v \
    --port /dev/ttyUSB0 \
    efuse
```

## License

This software is released under the [Apache-2.0 License](LICENSE).
