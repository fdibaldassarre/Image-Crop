#!/usr/bin/env python3

from lib.Interface import Interface
import argparse

parser = argparse.ArgumentParser(description="Image crop")
parser.add_argument( 'address', nargs='?', default=None, help = 'Image address' )

args = parser.parse_args()

address = args.address

interface = Interface(address)
interface.start()
