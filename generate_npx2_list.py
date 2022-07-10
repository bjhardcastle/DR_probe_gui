"""
    cycle through folders and generate checksums for 
"""
import json
import os, timeit, zlib, random, binascii, platform
import pathlib
import time
import datetime
import logging

import timing

# logging.basicConfig(filename=f'{datetime.datetime.now().strftime("clear_dir_%Y_%m_%d_%H-%M-%S")}.log', level=logging.INFO)

# glob pattern
pattern = '*/*.npx2'

# for each file in scan_dir, see if it exists in each location in turn
if platform.system() == 'Windows':
    backup_locations = [
                                                         # R'\\allen\programs\mindscope',                                            # R'\\allen\programs\braintv',
        R'\\allen\programs\mindscope\workgroups\np-exp',
    ]
else:
    backup_locations = [
                                                         # R'/allen/programs/mindscope',
                                                         # R'/allen/programs/braintv',
        R'/allen/programs/mindscope/workgroups/np-exp',
    ]


def crc32altren(filename):
    """Altren solution"""
    buf = open(str(filename), 'rb').read()
    hash = binascii.crc32(buf)
    return "%X" % (hash & 0xFFFFFFFF)


def forLoopCrc(fpath):
    """With for loop and buffer."""
    crc = 0
    with open(str(fpath), 'rb', 65536) as ins:
        for x in range(int((os.stat(fpath).st_size / 65536)) + 1):
            crc = zlib.crc32(ins.read(65536), crc)
    return '%X' % (crc & 0xFFFFFFFF)


j = 'npexp_npx2_list.json'
if os.path.exists(j):
    with open(j, 'r') as f:
        files = json.load(f)

for b in backup_locations:
    g = pathlib.Path(b).rglob(pattern)
    try:
        for s in g:
            files.update({
                str(s.relative_to(s.parent.parent).as_posix()): {
                    'windows': str(pathlib.PureWindowsPath(s)),
                    'linux': str(pathlib.PurePosixPath(s)),
                    'size': os.stat(str(s)).st_size,
                }
            })
            with open(j, 'w') as f:
                json.dump(files, f, indent=4)
    except:
        pass
