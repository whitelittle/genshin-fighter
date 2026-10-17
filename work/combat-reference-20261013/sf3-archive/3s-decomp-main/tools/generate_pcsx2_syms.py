# Inspired by https://github.com/ethteck/kh1/blob/main/tools/sym2pcsx2.py

# A simple tool that reads the symbol_addrs.txt file produced by splat
# and generates a .sym file for use with the PCSX2 emulator's debugger.

# NOTE: The generated .sym file MUST be in the EXACT same directory and have
# the EXACT same name as the .iso being used in PCSX2 for the emulator
# to detect it. For example, the sym file generated to accompany
# `Roms/SFIII.iso` MUST be named/stored as `Roms/SFIII.sym`

from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class Symbol:
    name: str
    address: int

def extract_symbols(path: Path) -> list[Symbol]:
    with open(path, 'r') as f:
        text = f.read()

    pattern = r"((?:\w|_)+) = (\w+);(?: // .*)?"
    symbols: list[Symbol] = list()

    for match in re.finditer(pattern, text):
        name, address_str = match.groups()
        symbol = Symbol(name, int(address_str, 16))
        symbols.append(symbol)

    return symbols

def main():
    symbols_path = Path("config/anniversary/symbols")
    symbols: list[Symbol] = []

    for path in symbols_path.iterdir():
        symbols.extend(extract_symbols(path))

    for symbol in symbols:
        print(f"{symbol.address:X} {symbol.name}")

if __name__ == "__main__":
    main()
