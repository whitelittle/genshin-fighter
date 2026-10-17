#!/usr/bin/env python3

import os

RANGES: dict[str, tuple[int, int]] = {
    "anniversary": (0x10000, -0xBC)
}

def main():
    version = os.environ["VERSION"]
    target = os.environ["MAIN"]
    range = RANGES[version]

    bin_path = f"build/{version}/{target}"

    with open(bin_path, 'rb') as f:
        bin = f.read()

    with open(f"elf/{version}/header", 'rb') as f:
        header = f.read()

    with open(f"elf/{version}/footer", 'rb') as f:
        footer = f.read()

    with open(bin_path, 'wb') as f:
        f.write(header)
        f.write(bin[range[0]:range[1]])
        f.write(footer)

if __name__ == '__main__':
    main()
