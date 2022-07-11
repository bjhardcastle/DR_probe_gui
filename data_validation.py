""" data integrity database classes """

import abc
import dataclasses
import os
import pathlib
import pdb
import re
import tempfile
import zlib
from typing import Callable, Dict, List, Optional, Tuple, Union

KB = 1024
MB = 1024**2
GB = 1024**3


def chunk_crc32(fpath: Union[str, pathlib.Path]) -> str:
    """ generate crc32 with for loop to read large files in chunks """
    crc = 0
    with open(str(fpath), 'rb', 65536) as ins:
        for _ in range(int((os.stat(fpath).st_size / 65536)) + 1):
            crc = zlib.crc32(ins.read(65536), crc)
    return '%X' % (crc & 0xFFFFFFFF)


def test_crc32_function(func):
    temp = os.path.join(tempfile.gettempdir(), 'checksum_test')
    with open(os.path.join(temp), 'wb') as f:
        f.write(b'foo')
    assert func(temp) == "8C736521", "checksum function incorrect"


def valid_crc32_checksum(value: str) -> bool:
    """ validate crc32 checksum """
    if isinstance(value, str) and len(value) == 8 \
        and all(c in '0123456789ABCDEF' for c in value.upper()):
        return True
    return False


class DataValidationFileBase(abc.ABC):
    """ Represents a file to be validated
    
        Can be subclassed easily to change the checksum alogrithm
        
        Call super().__init__(path, checksum, size) in subclass __init__  
        
    """

    # TODO add repr and eq methods

    # filesizes below this will have checksums auto-generated on init
    checksum_threshold: int = 50 * MB

    checksum_name: str = None # e.g. 'crc32'

    # implementation of algorithm for generating checksums, accepts a path and
    # returns a checksum string
    checksum_generator: Callable[[str], str] = NotImplementedError()

    # a function that confirms checksum_generator is working as expected,
    # accept a function, return nothing but raise exception if test fails
    checksum_test: Callable[[Callable], None] = NotImplementedError()

    # a function that accepts a string and confirms it conforms to the checksum
    # format, return True or False
    checksum_validate: Callable[[str], bool] = NotImplementedError()

    # @abc.abstractmethod
    def __init__(self, path: str = None, checksum: str = None, size: int = None):
        """ setup depending on the inputs """

        if not (path or checksum):
            raise ValueError(f"{self.__class__}: either path or checksum must be set")

        if path and not os.path.isfile(path):
            raise ValueError(f"{self.__class__}: path must point to a file {path=}")
        elif path:
            self.path = path

        if path and os.path.exists(path):
            self.size = os.path.getsize(path)
        elif size and isinstance(size, int):
            self.size = size
        elif not isinstance(size, int):
            raise ValueError(f"{self.__class__}: size must be an integer {size}")

        if checksum:
            self.checksum = checksum

        if not checksum \
            and self.path and os.path.exists(self.path) \
            and self.size and self.size < self.checksum_threshold \
            :
            self.checksum = self.__class__.generate_checksum(self.path)

    @classmethod
    # @abc.abstractmethod
    def generate_checksum(cls, path: str) -> str:
        cls.checksum_test(cls.checksum_generator)
        return cls.checksum_generator(path)

    @property
    # @abc.abstractmethod
    def checksum(self) -> str:
        print("validated checksum:")
        return self._checksum

    @checksum.setter
    # @abc.abstractmethod
    def checksum(self, value: str):
        if self.__class__.checksum_validate(value):
            print(f"setting {self.checksum_name} checksum: {value}")
            self._checksum = value
        else:
            raise ValueError(f"{self.__class__}: trying to set an invalid {self.checksum_name} checksum")

    def __repr__(self):
        return f"{self.__class__.__name__}(path=r'{self.path}', checksum='{self.checksum}', size={self.size})"

    def __eq__(self, other):
        return self.checksum == other.checksum and self.size == other.size


class SessionFile():
    """ Represents a single file belonging to a neuropixels ecephys session """

    # identify a session based on
    # [10-digit session ID]_[6-digit mouseID]_[6-digit date str]
    session_reg_exp = "[0-9]{0,10}_[0-9]{0,6}_[0-9]{0,8}"

    def __init__(self, path: str):
        """ from the complete file path we can extract some information upon
        initialization """

        # first ensure the path is a file
        if not (isinstance(path, str) and os.path.isfile(path)):
            raise ValueError(f"{self.__class__}: path must point to a file {path=}")
        else:
            self.path = path

        # extract the session ID from anywhere in the path
        session_folders = re.search(self.session_reg_exp, path)
        if session_folders:

            self.session_folder = session_folders[0]

            # extract the constituent parts of the session folder
            self.session_id = self.session_folder.split('_')[0]
            self.mouse_id = self.session_folder.split('_')[1]
            self.date = self.session_folder.split('_')[2]

            # we expect the session_folder string to first appear in the path as
            # a child of some 'repository' of session folders or individual
            # files - split the path at the first session_folder match and call
            # that folder the root
            self.root_path = self.path.split(self.session_folder)[0]

            # if the repository contains session folders, it should contain the
            # following:
            session_folder_path = os.path.join(self.root_path, self.session_folder)

            # but this may not exist: we could have a file sitting in a folder
            # with assorted files from multiple sessions (e.g. LIMS incoming),
            # or a folder which has the session_folder pattern with extra info
            # appended, eg. _probeABC:
            if os.path.exists(session_folder_path):
                self.session_folder_path = session_folder_path
            else:
                self.session_folder_path = None

            # wherever the file is, get its path relative to the parent of a
            # hypothetical session folder:
            relative_path = pathlib.Path(self.path).relative_to(self.root_path)
            if relative_path.parts[0] != self.session_folder:
                self.relative_path = os.path.join(self.session_folder, str(relative_path))
            else:
                self.relative_path = str(relative_path)


# TODO move path from DataValidation to File class
# TODO extend DVCRC43 and FileSession class to support checksum plus file operations


class DataValidationFileCRC32(DataValidationFileBase, SessionFile):
    checksum_name: str = "CRC32"     # e.g. 'crc32'
    checksum_generator: Callable[
        [str],
        str] = chunk_crc32           # implementation of algorithm for generating checksums, accept a path and return a checksum
    checksum_test: Callable[
        [Callable],
        None] = test_crc32_function  # a test Callable that confirms checksum_generator is working as expected, accept a function, return nothing (raise exception if test fails)
    checksum_validate: Callable[
        [str],
        bool] = valid_crc32_checksum # a function that accepts a string and validates it conforms to the checksum format, returning boolean

    def __init__(self, path: str = None, checksum: str = None, size: int = None):
        SessionFile.__init__(self, path)
        DataValidationFileBase.__init__(self, path, checksum, size)


class ValidationDatabase(abc.ABC):
    """ 
    serves as a template for interacting with a database of filepaths,
    filesizes, and filehashes, for validating data integrity
    
    not to be used directly, but subclassed: make a new subclass that implements
    each of the "abstract" methods specified in this class
    
    as long as the subclass methods accept the same inputs and output the
    expected results, a new database subclass can slot in to replace an old one
    in some other code without needing to make any other changes to that code
    
    Some design notes:
    
    - hash + filesize uniquely identify data, regardless of path 
    
    - the database holds previously-generated checksum hashes for
    large files (because they can take a long time to generate), plus their
    filesize at the time of checksum generation
    
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
                     file: DataValidationFileBase,
                     path: str = None,
                     size: int = None,
                     chksum: str = None) -> List[DataValidationFileBase]:
        """search database for entries that match any of the given arguments 

        Args:
            path (Union[str, List[str]], optional): _description_. Defaults to None.
            size (Union[int, List[int]], optional): _description_. Defaults to None.
            chksum (Union[str, List[str]], optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """


x = DataValidationFileCRC32(path=os.path.join(tempfile.gettempdir(), 'checksum_test'))
print(x.checksum)
x.checksum = "0" * 8
# int('003P', 16)
x = DataValidationFileCRC32(
    path=
    R"\\allen\programs\mindscope\workgroups\np-exp\1190290940_611166_20220708\1190258206_611166_20220708_surface-image1-left.png"
)
print(x)
print(x.path)
print(x.checksum)
print(x.mouse_id)
print(x.relative_path)
