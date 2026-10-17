from pathlib import Path
import subprocess
import re
import shutil
from dataclasses import dataclass

OBJDUMP = Path('/usr/bin/mipsel-linux-gnu-objdump')

JUMP_INSTRUCTIONS = {
    # 'beq',
    # 'bne',
    # 'bltz',
    # 'bgez',
    'j',
    'jal'
}

def run_command(args: list[str]) -> str:
    process = subprocess.run(args, capture_output=True, text=True)
    return process.stdout

def create_or_clear(dir: Path):
    if dir.exists():
        shutil.rmtree(dir)

    dir.mkdir(parents=True, exist_ok=True)

@dataclass
class Instruction:
    file_offset: int
    vram_offset: int
    code: int
    label: str
    operands: str | None

    @property
    def signature(self) -> int:
        if self.label in JUMP_INSTRUCTIONS:
            return -1

        if self.operands != None and (r"%hi" in self.operands or r"%lo" in self.operands):
            return -1

        return self.code

@dataclass
class Func:
    label: str
    instructions: list[Instruction]

    @property
    def file_offset(self) -> int:
        return self.instructions[0].file_offset
    
    @property
    def vram_offset(self) -> int:
        return self.instructions[0].vram_offset        
    
@dataclass
class Object:
    name: str
    funcs: list[Func]

def funcs_are_equal(func_a: Func, func_b: Func) -> bool:
    i_a = 0
    i_b = 0
    ins_a = func_a.instructions
    ins_b = func_b.instructions

    while i_a < len(ins_a) and i_b < len(ins_b):
        if ins_a[i_a].signature != -1 \
            and ins_b[i_b].signature != -1 \
            and ins_a[i_a].signature != ins_b[i_b].signature:

            return False

        i_a += 1
        i_b += 1

    a_nops_left = all(x.code == 0 for x in ins_a[i_a:])
    b_nops_left = all(x.code == 0 for x in ins_b[i_b:])

    return a_nops_left and b_nops_left

def revert_bytes(n: int) -> int:
    return (n >> 24) | ((n >> 8) & 0xFF00) | ((n << 8) & 0xFF0000) | ((n << 24) & 0xFF000000)

def longest_consecutive_range(arr: list[int]) -> tuple[int, int]:
    if len(arr) == 0:
        return (0, 0)
    
    best_range = (0, 1)
    best_len = 1
    current_range = [0, 1]
    current_len = 1

    for i in range(1, len(arr)):
        if arr[i] - arr[i - 1] == 1:
            current_len += 1
            current_range[1] = i + 1

            if current_len > best_len:
                best_len = current_len
                best_range = tuple(current_range)

        else:
            current_range = [i, i + 1]
            current_len = 1

    return best_range

def extract_funcs_from_asm(path: Path) -> list[Func]:
    with open(path) as f:
        file_str = f.read()

    func_pattern = r"glabel (\w+)\n((?:.|\n)+?)\.size"
    instruction_pattern = r"/\* (\w+)\s+(\w+)\s+(\w+) \*/\s+((?:\w|\.)+) *(.+)?\n"

    funcs: list[Func] = list()

    for func_match in re.finditer(func_pattern, file_str):
        func_label, body = func_match.groups()
        instructions: list[Instruction] = list()

        for instruction_match in re.finditer(instruction_pattern, body):
            file_offset_str, vram_offset_str, code_str, label, operands = instruction_match.groups()

            instructions.append(
                Instruction(
                    file_offset=int(file_offset_str, 16),
                    vram_offset=int(vram_offset_str, 16),
                    code=int(code_str, 16),
                    label=label,
                    operands=operands
                )
            )

        funcs.append(Func(func_label, instructions))

    return funcs

def extract_funcs_from_archive(path: Path) -> list[Object]:
    args = [
        OBJDUMP, 
        '--disassemble', 
        '--disassemble-zeroes', 
        '--file-offsets', 
        path
    ]

    dump_lines = run_command(args).splitlines()

    object_header_regex = re.compile(r"^(\w+)\.o:\s+file format")
    function_header_regex = re.compile(r"(\w+) <(\w+)> \(File Offset: 0x(\w+)\):")
    instruction_regex = re.compile(r"^\s*(\w+):\s+(\w+)\s+(\w+)\s*(.*)?$")

    objects: list[Object] = list()

    for line in dump_lines:
        obj_header_match = object_header_regex.search(line)
        func_header_match = function_header_regex.search(line)
        instruction_match = instruction_regex.search(line)

        if obj_header_match:
            object_name = obj_header_match.groups()[0]
            objects.append(Object(object_name, list()))

        elif func_header_match:
            label = func_header_match.groups()[1]
            objects[-1].funcs.append(Func(label, list()))

        elif instruction_match:
            offset_str, code_str, label, operands = instruction_match.groups()
            offset = int(offset_str, 16)

            instruction = Instruction(
                file_offset=offset,
                vram_offset=offset,
                code=revert_bytes(int(code_str, 16)),
                label=label,
                operands=operands
            )

            objects[-1].funcs[-1].instructions.append(instruction)

    return objects

def find_lib_syms(
    lib: Path, 
    asm: Path, 
    obj: str | None = None, 
    asm_range: tuple[int | None, int | None] = (None, None)
):
    objects = extract_funcs_from_archive(lib)
    
    if obj:
        objects = [x for x in objects if x.name == obj]

    asm_funcs = extract_funcs_from_asm(asm)
    asm_lower, asm_upper = asm_range

    if asm_lower:
        asm_funcs = [x for x in asm_funcs if x.file_offset >= asm_lower]

    if asm_upper:
        asm_funcs = [x for x in asm_funcs if x.file_offset < asm_upper]

    global_start_offset = 0
    funcs_found = 0

    for object in objects:
        print(f"Looking for {object.name}.o ...\n")

        # Gather matches

        local_start_offset = global_start_offset
        matches: list[tuple[int, int]] = list()

        for obj_func_index, obj_func in enumerate(object.funcs):
            for asm_func_index in range(local_start_offset, len(asm_funcs)):
                asm_func = asm_funcs[asm_func_index]

                if funcs_are_equal(obj_func, asm_func):
                    matches.append((obj_func_index, asm_func_index))
                    local_start_offset = asm_func_index + 1
                    break
        
        # Analyze matches

        if len(matches) == 0:
            print("No matches at all ❌")
        else:
            base_range = longest_consecutive_range([x[1] for x in matches])
            base_len = base_range[1] - base_range[0]

            # This is a heuristic.
            # If there are less than 3 consecutive functions matched
            # then that's probably not the place where this object
            # is in the file.
            required_base_len = min(len(object.funcs), 3)

            if base_len < required_base_len:
                print("Too few matches ⚠️")
            else:
                for i in range(*base_range):
                    obj_func_index, asm_func_index = matches[i]
                    obj_func = object.funcs[obj_func_index]
                    asm_func = asm_funcs[asm_func_index]

                    print(f"{obj_func.label} = 0x{asm_func.vram_offset:08X}; // type:func")

                    global_start_offset = max(global_start_offset, asm_func_index + 1)
                    funcs_found += 1

                missed_before = matches[base_range[0]][0]
                missed_after = len(object.funcs) - matches[base_range[1] - 1][0] - 1

                if missed_before > 0:
                    print()
                    print(f"Missed {missed_before} functions before:")

                    for func in object.funcs[:missed_before]:
                        print(f"\t{func.label}")

                if missed_after > 0:
                    print()
                    print(f"Missed {missed_after} functions after:")
                    
                    for func in object.funcs[-missed_after:]:
                        print(f"\t{func.label}")

        print("\n\n")

    print(f"Found {funcs_found} functions")

def main():
    pass

if __name__ == '__main__':
    main()
