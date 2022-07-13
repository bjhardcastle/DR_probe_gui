import os
import pathlib
import timeit
import zlib
from typing import Union


def chunk_crc32(fpath: Union[str, pathlib.Path], chunksize: int = 65536) -> str:
    """ generate crc32 with for loop to read large files in chunks """
    crc = 0
    read = []
    process = []
    with open(str(fpath), 'rb', chunksize) as ins:
        for _ in range(int((os.stat(fpath).st_size / chunksize)) + 1):
            read_timer = timeit.default_timer()
            chunk = ins.read(chunksize)
            read.append(timeit.default_timer() - read_timer)
            process_timer = timeit.default_timer()
            crc = zlib.crc32(chunk, crc)
            process.append(timeit.default_timer() - process_timer)
    print(f'Read: {sum(read) / len(read)}')
    print(f'Process: {sum(process) / len(process)}')
    return '%08X' % (crc & 0xFFFFFFFF)


path = R"\\allen\programs\mindscope\workgroups\np-exp\1127061307_569156_20210908\1127061307_569156_20210908_probeA_sorted\continuous\Neuropix-PXI-100.0\pc_features.npy"
#! 4GB file on network
# 32768.0 chunks: 52.168861 s
# 65536 chunks: 6.9938936 s
# 131072 chunks: 7.277428900000004 s
# 262144 chunks: 6.981789000000006 s
# 524288 chunks: 7.035019699999992 s
# 1048576 chunks: 9.000374199999996 s

# path = R"\\allen\programs\mindscope\workgroups\np-exp\1127061307_569156_20210908\1127061307_569156_20210908_probeA_sorted\continuous\Neuropix-PXI-100.0\continuous.dat"
#! 250GB file on network
# Read: 0.0003326543683942379
# Process: 4.059068883272465e-05
# 32768.0 chunks: 2917.0309681 s

for c in [0.5, 1, 2, 4, 8, 16]:
    start_time = timeit.default_timer()
    chksum = chunk_crc32(path, chunksize=int(c * 65536))
    time = timeit.default_timer() - start_time
    print(f"{c*65536} chunks: {time} s")

from time import sleep, perf_counter
from threading import Thread


def task(chunk,crc):
    return zlib.crc32(chunk, crc)


start_time = perf_counter()

# create and start 10 threads
threads = []

for n in range(1, 11):
    
    t = Thread(target=zlib.crc32, args=(chunk,crc))
    threads.append(t)
    t.start()

# wait for the threads to complete
for t in threads:
    t.join()

end_time = perf_counter()

print(f'It took {end_time- start_time: 0.2f} second(s) to complete.')