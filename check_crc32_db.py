import json
import os
import pathlib
import sys

sys.path.append(os.getcwd())
import data_validation as dv


# json checksum lists ------------------------------------------------------------------------------------------------ #

lims = R"\\allen\ai\homedirs\ben.hardcastle\lims_npx2_list_hashed.json"
npexp = R"\\allen\ai\homedirs\ben.hardcastle\npexp_npx2_list_hashed.json"

db = {}
for file in [lims, npexp]:
    with open(file, 'r') as f:
        db.update(json.load(f))

objs = []
files = list(db)   # npx2 files: parentfolder/filename.npx2
for file in files:
    if "crc32" in db[file].keys():

        path = "\\" + db[file]["windows"]
        size = db[file]["size"]
        crc32 = db[file]["crc32"]
        if len(crc32) < 8:
            crc32 = "0" * (8 - len(crc32)) + crc32
        objs.append(dv.CRC32DataValidationFile(path=path, size=size, checksum=crc32))


# openhashtab checksum.sums list ------------------------------------------------------------------------------------- #

np1j = R"\\W10DT05501\j\checksums.sums"
db = {}
for file in [np1j]:
    with open(file, 'r') as f:
        lines = f.readlines()

    for idx in range(0, len(lines), 2):
        line0 = lines[idx].rstrip()
        line1 = lines[idx + 1].rstrip()

        if "crc32" in line0:
            crc32, *args = line1.split(' ')
            filename = ' '.join(args)

            if filename[0] == "*":
                filename = filename[1:]
            path = '/'.join(["//W10DT05501/j", filename])

            try:
                objs.append(dv.CRC32DataValidationFile(path=path, checksum=crc32))
            except ValueError as e:
                print(e)


# look for matches between objects ----------------------------------------------------------------------------------- #

objs.sort()
for obj in objs:
    if objs.count(obj) > 1:
        if ".npx2" in obj.path:
            print(f"{pathlib.Path(obj.parent).as_uri()}/{obj.name} has valid {objs.count(obj)-1} backup(s)")
            print(f"{os.path.exists(obj.path)=}")
