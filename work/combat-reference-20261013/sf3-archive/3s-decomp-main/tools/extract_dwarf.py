import re
from collections import OrderedDict
from typing import Any

# A throwaway script for parsing the output of `dtk dwarf dump`

def adjust_offset(offset: int) -> int:
    return offset - 0x100000 + 0x80

def main():
    with open("dwarf") as f:
        text = f.read()

    pattern = r"/\*\n.   Compile unit: C:\\(.+)\n.   Producer: .+\n.   Language: \w+\n(?:    Code range: (\w+) -> (\w+)\n)?\*/"
    ranges: OrderedDict[str, Any] = OrderedDict()

    for match in re.finditer(pattern, text):
        path, range_start_str, range_end_str = match.groups()

        if range_start_str == None or range_end_str == None:
            continue

        path_components = path.split("\\")
        path = "/".join(path_components)
        range_start = int(range_start_str, 16)
        range_end = int(range_end_str, 16)

        if path not in ranges:
            ranges[path] = [range_start, range_end]
        else:
            ranges[path][0] = min(ranges[path][0], range_start)
            ranges[path][1] = max(ranges[path][1], range_end)

    ranges = [(path, range[0], range[1]) for path, range in ranges.items()]
    ranges = sorted(ranges, key=lambda x: x[1])
    prev_end = None

    for path, range_start, range_end in ranges:
        range_start = adjust_offset(range_start)
        range_end = adjust_offset(range_end)

        path = path.removesuffix(".c").removesuffix(".C").removesuffix(".s")

        # If the gap between files is big enough add another file in the middle
        if prev_end != None and range_start - prev_end > 12:
            unk_start = prev_end + 4
            unk_size = range_start - unk_start
            print(f"- [0x{unk_start:06X}, asm] # size = 0x{unk_size:X}")

        print(f"- [0x{range_start:06X}, asm, {path}]")

        prev_end = range_end

if __name__ == "__main__":
    main()
