from typing import List

from ConfigValidator.CustomErrors.BaseError import BaseError
from ExtendedTyping.Typing import SupportsStr


class FactorModel:
    def __init__(self, factor_name: str, treatments: List[SupportsStr]):
        if len(set(treatments)) != len(treatments):
            raise BaseError(f"Treatment levels for factor {factor_name} are not unique!")

        self.__factor_name = factor_name
        self.__treatments = treatments

    @property
    def factor_name(self) -> str:
        return self.__factor_name

    @property
    def treatments(self) -> List[SupportsStr]:
        return self.__treatments
