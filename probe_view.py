import dataclasses
from dataclasses import dataclass
from typing import Union

# insertion event
#   - insertion img, + other imgs pre/post
#   - implant
#       - label
#       - picture
#       - hole list [1, ..., n]
#           - corresponding brain areas
#       - plan [A: {3,4,3,4}, B: {1,2,1,2}, ...]
#   - planned probes
#       - letter/index (common)
#       - holes possible {2,3,4}
#       - holes planned original {3,4,3,4}
#   - inserted probes
#       - holes hit {day1: 2, day2: 3, ...}
#       - motor locs
#       - insertion notes {day1: "...", day2: "...", ..}
#       - position on image
#       - original image name (where probes location annotations are drawn)


@dataclass(order=True) # order allows comparisons and sorting of instances
class Probe:
    """ class for a single neuropixels probe 
    should be initialized with a name [a-f] or number [0-5]
    """
    init_id: Union[int, str] = dataclasses.field(default=None, init=True, repr=False)
    index: int = None
    label: str = None
    notes: str = None
    coords: list = None
    max_probes: int = dataclasses.field(default=6, init=True, repr=False)

    def __init__(self, init_id):

        if isinstance(init_id, str):
            self.label = init_id
            self.index = self.chr2idx(init_id)

        elif isinstance(init_id, int):

            self.index = init_id
            self.label = self.idx2chr(init_id)

    @index.setter
    def index(self, idx):
        if idx not in range(self.max_probes):
            raise ValueError(f"{idx=}: Probe index must be in range [0-{self.max_probes-1}]",
                             f"=> [A-{self.idx2chr(self.max_probes-1)}]")
        self.index = idx

    @label.setter
    def label(self, label):
        self.index = self.chr2idx(str(label)) # validate by assigning to index
        self.label = label.upper()

    @classmethod
    def idx2chr(self, idx=None) -> str:
        """convert probe index [0-5] to a character [A-F]"""
        if idx is None:
            idx = self.index
        start_idx = ord("A".upper()) # find character index for "A", first in our series
        return chr(start_idx + idx)  # find our character relative to "A"

    @classmethod
    def chr2idx(self, label=None) -> int:
        """convert probe label character [A-F] to an index [0-5]"""
        if label is None:
            label = self.label

        start_idx = ord("A".upper())  # find character index for "A", first in our series
        this_idx = ord(label.upper()) # find our character index
        return this_idx - start_idx   # find the number of positions of our character from "A"

    class nestedtest:
        ...


x = [b, c, a] = [Probe(1), Probe("C"), Probe(0)]

print(x)
print(Probe.chr2idx("b"))
