#!/usr/bin/python

import psutil

def getCPUUse():
    cpu = psutil.cpu_percent(interval=None)
    return cpu

def getRAM():
    ram = psutil.virtual_memory()
    return ram.available / 2**20 # MiB
    