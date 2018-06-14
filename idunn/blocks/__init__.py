from .opening_hour import OpeningHourBlock
from .phone import PhoneBlock
from .information import InformationBlock, WikipediaBlock

ALL_BLOCKS = [OpeningHourBlock, PhoneBlock, InformationBlock, WikipediaBlock]
BLOCK_TYPE_TO_CLASS = {b.BLOCK_TYPE: b for b in ALL_BLOCKS}
