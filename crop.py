#!/usr/bin/env python3

import argparse
from src import Interface

parser = argparse.ArgumentParser(description="Image crop")
parser.add_argument( 'address', nargs='?', default=None, help = 'Image address' )

args = parser.parse_args()

address = args.address

interface = Interface.start(address)
interface.start()
