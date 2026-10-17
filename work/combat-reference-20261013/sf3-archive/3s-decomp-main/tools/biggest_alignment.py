import sys

def alignment_power(addr: int) -> int:
    power = 1

    while True:
        if addr % 2**power != 0:
            return power - 1
        
        power += 1

def main():
    min_alignment_power = 10000000

    for arg in sys.argv[1:]:
        pow = alignment_power(int(arg, 16))
        min_alignment_power = min(min_alignment_power, pow)

    print(f"biggest alignment is {2**(min_alignment_power)} (2**{min_alignment_power})")

if __name__ == '__main__':
    main()
