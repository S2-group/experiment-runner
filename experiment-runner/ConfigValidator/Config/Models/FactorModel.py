from typing import List
from ExtendedTyping.Typing import SupportsStr


class FactorModel:
    #FIXME: The treatment levels should be a set
    def __init__(self, factor_name: str, treatments: List[SupportsStr]):
        self.__factor_name = factor_name
        self.__treatments = treatments

    def get_factor_name(self) -> str:
        return self.__factor_name

    def get_treatments(self) -> List[SupportsStr]:
        return self.__treatments
