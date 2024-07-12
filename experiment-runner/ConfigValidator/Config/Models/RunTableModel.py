import itertools
import random
from typing import Dict, List, Tuple

from ConfigValidator.CustomErrors.BaseError import BaseError
from ExtendedTyping.Typing import SupportsStr
from ProgressManager.RunTable.Models.RunProgress import RunProgress
from ConfigValidator.Config.Models.FactorModel import FactorModel


class RunTableModel:
    def __init__(self,
                 factors: List[FactorModel],
                 exclude_variations: List[Dict[FactorModel, List[SupportsStr]]] = None,
                 repetitions: int = 1,
                 data_columns: List[str] = None,
                 shuffle: bool = False
                 ):
        if exclude_variations is None:
            exclude_variations = {}
        if data_columns is None:
            data_columns = []

        if repetitions < 1:
            raise BaseError("Negative number of repetitions detected!")

        if len(set([factor.factor_name for factor in factors])) != len(factors):
            raise BaseError("Duplicate factor name detected!")

        if len(set(data_columns)) != len(data_columns):
            raise BaseError("Duplicate data column detected!")

        self.__factors = factors
        self.__exclude_variations = exclude_variations
        self.__repetitions = repetitions
        self.__data_columns = data_columns
        self.__shuffle = shuffle

    def get_factors(self) -> List[FactorModel]:
        return self.__factors

    def get_data_columns(self) -> List[str]:
        return self.__data_columns

    def generate_experiment_run_table(self) -> List[Dict]:
        def __filter_list(full_list: List[Tuple]):
            if len(self.__exclude_variations) == 0:
                return full_list

            to_remove_indices = []
            for exclusion in self.__exclude_variations:
                # Construct the exclusion tuples
                list_of_lists = []
                indexes = []
                for factor, treatment_list in exclusion.items():
                    list_of_lists.append(treatment_list)
                    indexes.append(self.__factors.index(factor))
                exclude_combinations_list = list(itertools.product(*list_of_lists))

                # Mark the exclusions in the full table
                for idx, elem in enumerate(full_list):
                    for exclude_combo in exclude_combinations_list:
                        if all([exclude_combo[i] == elem[indexes[i]] for i in range(len(indexes))]):
                            to_remove_indices.append(idx)

            to_remove_indices.sort(reverse=True)
            for idx in to_remove_indices:
                del full_list[idx]
            return full_list

        list_of_lists = [factor.treatments for factor in self.__factors]
        combinations_list = list(itertools.product(*list_of_lists))
        filtered_list = __filter_list(combinations_list)

        column_names = ['__run_id', '__done']  # Needed for experiment-runner functionality
        for factor in self.__factors:
            column_names.append(factor.factor_name)

        if self.__data_columns:
            for data_column in self.__data_columns:
                column_names.append(data_column)

        experiment_run_table = []
        for j in range(self.__repetitions):
            for i, combo in enumerate(filtered_list):
                row_list = list(combo)
                row_list.insert(0, f'run_{i}_repetition_{j}')  # __run_id
                row_list.insert(1, RunProgress.TODO)  # __done

                if self.__data_columns:
                    for _ in self.__data_columns:
                        row_list.append(" ")
                experiment_run_table.append(dict(zip(column_names, row_list)))

        if self.__shuffle:
            random.shuffle(experiment_run_table)
        return experiment_run_table

