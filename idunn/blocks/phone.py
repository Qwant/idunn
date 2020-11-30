import logging
from typing import ClassVar
from phonenumbers import PhoneNumber, PhoneNumberFormat, parse, format_number

from .base import BaseBlock

logger = logging.getLogger(__name__)


def get_formatted_phone_number(phone, output_format):
    try:
        if not isinstance(phone, PhoneNumber):
            phone = parse(phone)
        return format_number(phone, output_format)
    except Exception:
        logger.warning("Failed to format phone number", exc_info=True)
    return None


def get_international_phone_number(phone):
    return get_formatted_phone_number(phone, PhoneNumberFormat.INTERNATIONAL)


def get_national_phone_number(phone):
    return get_formatted_phone_number(phone, PhoneNumberFormat.NATIONAL)


def get_e164_phone_number(phone):
    return get_formatted_phone_number(phone, PhoneNumberFormat.E164)


class PhoneBlock(BaseBlock):
    BLOCK_TYPE: ClassVar = "phone"

    url: str
    international_format: str
    local_format: str

    @classmethod
    def from_es(cls, place, lang):
        raw = place.get_phone()
        if not raw:
            return None
        try:
            parsed_phone_number = parse(raw)
        except Exception:
            logger.warning(
                "Failed to parse phone number for place %s", place.get_id(), exc_info=True
            )
            return None
        if parsed_phone_number is None:
            return None

        e164 = get_e164_phone_number(parsed_phone_number)
        national = get_national_phone_number(parsed_phone_number)
        international = get_international_phone_number(parsed_phone_number)
        if e164 is None or national is None or international is None:
            return None
        return cls(
            url="tel:{}".format(e164), international_format=international, local_format=national
        )
