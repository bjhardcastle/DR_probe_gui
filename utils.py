import json
import pathlib

import pandas as pd


def get_implant_type(mouseID: int) -> dict:
    """ scan a spreadsheet of surgery notes and find the implant used for a particular mouse, or return none

    Args:
        mouseID (int): 6-digit id

    Returns:
        dict: 
            "index" (int): 
            "type" (str): implant type, version, or nickname
            "search_strings": for searching elsewhere (eg implant template files)
    """
    # open json file with implant info (in current working directory)
    implant_info_file = pathlib.Path("implant_info.json")

    with implant_info_file.open() as json_file:
        json_data = json.load(json_file)
        implants = json_data["implants"]

    # open spreadsheet with surgery notes
    xlsx_file = pathlib.Path(R'C:\Users\ben.hardcastle\OneDrive - Allen Institute\DR_Surgery_Dev_Tracking.xlsx')

    if not pathlib.Path(xlsx_file).exists():
        print(f"cannot find surgery notes spreadsheet\n{xlsx_file=}") # todo logging
        return None

    # read implant surgery notes from specific sheet
    df = pd.read_excel(xlsx_file, sheet_name='Survival Tracking')
    Warning("Using DR surgery spreadsheet copied locally - will not get updates")

    # look for a row with the corresponding mouseID and extract implant description cell
    x = df[df["MID"].isin([int(mouseID)])]["Type"]

    if len(x) > 1:
        print(f"{mouseID=} has multiple rows in surgery notes") # todo logging
        return None

    try:
        implant_description = x.to_numpy()[0]
    except IndexError:
        print(f"{mouseID=} not in surgery notes spreadsheet") # todo logging
        return None

    for i in implants:
        if any([name in implant_description for name in i["search_strings"]]):
            return i

    # if we still haven't found any matches:
    print(f"{mouseID=} in surgery notes spreadsheet - no known type matched in {implant_description=}") # todo logging
    return None


def make_implant_info_file():
    """ last updated 2022-05-30"""
    # todo

    implant_info_file = pathlib.Path("implant_info.json")

    implant_info = {
        "implants": [{
            "index": 0,
            "type": "#42",
            "search_strings": ["foot", "ball", "42"],
        }, {
            "index": 1,
            "type": "TS-1",
            "search_strings": ["TS1", "TS-1"],
        }, {
            "index": 2,
            "type": "TS-2",
            "search_strings": ["TS2", "TS-2"],
        }, {
            "index": 3,
            "type": "TS-3",
            "search_strings": ["TS3", "TS-3"],
        }, {
            "index": 4,
            "type": "TS-4",
            "search_strings": ["TS4", "TS-4"],
        }]
    }

    # write json file directly from dictionary
    with implant_info_file.open('w') as json_file:
        json.dump(implant_info, json_file, indent=4, ensure_ascii=False)


print(f"{get_implant_type(612090)=}")
