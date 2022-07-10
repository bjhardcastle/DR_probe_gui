""" data integrity database classes """

import abc
import dataclasses
import os
import pathlib
import zlib
from curses.ascii import isalnum
from typing import Dict, List, Optional, Tuple, Union

KB = 1024
MB = 1024**2
GB = 1024**3


def forLoopCrc(fpath: Union[str, pathlib.Path]) -> str:
    """ generate crc32 with for loop and buffer """
    crc = 0
    with open(str(fpath), 'rb', 65536) as ins:
        for x in range(int((os.stat(fpath).st_size / 65536)) + 1):
            crc = zlib.crc32(ins.read(65536), crc)
    return '%X' % (crc & 0xFFFFFFFF)


def valid_crc32_checksum(value: str) -> bool:
    """ validate crc32 checksum """
    if isinstance(value, str) and value.isalnum() and len(value) == 8:
        return True
    return False


@dataclasses.dataclass()
class DataValidationFile():
    """ represents a file to be validated
        can be subclassed easily to change the checksum alogrithm
    """
    path: str = None
    size: int = None
    _checksum: str = None
    checksum_threshold = 50 * MB
    checksum_function = forLoopCrc

    def __post_init__(self):
        """ setup depending on the inputs """

        if not (self.path and self._checksum):
            raise ValueError("DataValidationFile: either path or checksum must be set")

        if self.path and os.path.exists(self.path):
            self.size = os.path.getsize(self.path)

        if self.path and not self._checksum and self.size > self.checksum_threshold:
            self.generate_checksum()

    def generate_checksum(self):
        self.checksum = self.checksum_function(self.path)

    @property
    def checksum(self) -> str:
        return self._checksum

    @checksum.setter
    def checksum(self, value: str):
        if valid_crc32_checksum(value):
            self._checksum = value
        else:
            raise ValueError("DataValidationFile: trying to set an invalid crc32 checksum")


class ValidationDatabase(abc.ABC):
    """ 
    serves as a template for interacting with a database 
    of filepaths, filesizes, and filehashes, for validating
    data integrity
    
    not to be used directly, but subclassed:
    make a new subclass that implements each of the "abstract"
    methods specified in this class
    
    as long as the subclass methods accept the same inputs
    and output the expected results, a new database subclass 
    can slot in to replace an old one in some other code 
    without needing to make any other changes to that code
    
    Some design notes:
    
    - hash + filesize uniquely identify data, regardless of path 
    
    - the database holds previously-generated checksum hashes for
    large files (because they can take a long time to generate),
    plus their filesize at the time of checksum generation
    
    - small text-like files can have checksums generated on the fly
    so don't need to live in the database (but they could)
    
    for a given data file input we want to identify in the database:
        - self:
            - size[0] == size[1]
            - hash[0] == hash[1]
            - path[0] == path[1]
    
        - valid backups:
            - size[0] == size[1]
            - hash[0] == hash[1]
            - path[0] != path[1]
                
            - valid backups, with filename mismatch:
                - filename[0] != filename[1]                
            
        - invalid backups:
            - path[0] != path[1] 
            - filename[0] == filename[1]
            
            - invalid backups, corruption likely:
                - size[0] == size[1]
                - hash[0] != hash[1]
            
            - invalid backups, out-of-sync or incomplete transfer:       
                - size[0] != size[1]
                - hash[0] != hash[1]
                
        - other, assumed unrelated:
            - size[0] != size[1]
            - hash[0] != hash[1]
            - filename[0] != filename[1]
                
    """

    @abc.abstractmethod
    def find_matches(self,
                     file: DataValidationFile,
                     path: str = None,
                     size: int = None,
                     chksum: str = None) -> List[DataValidationFile]:
        """search database for entries that match any of the given arguments 

        Args:
            path (Union[str, List[str]], optional): _description_. Defaults to None.
            size (Union[int, List[int]], optional): _description_. Defaults to None.
            chksum (Union[str, List[str]], optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """
