#!/bin/bash

# Run splat
python3 -m splat split config/sfiii.yaml

# Patch linker script with entrypoint
LINKER_SCRIPT=config/SLPM_656.21.ld
{ echo "ENTRY(__start)"; cat $LINKER_SCRIPT; } > tmp
mv tmp $LINKER_SCRIPT
