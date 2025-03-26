from typing import Callable
from itertools import product

def batcher(iterable, n):
    result = []
    i = 0
    while i < len(iterable):
        result.append(iterable[i:i+n])
        i += n
    return result

def matrix_creator(
    batched_indexes: list[tuple],
    indexes: list[tuple[set, str]],
    values: dict,
    n: int,
    no_value: Callable[[int], str]
):
    if n == 1:
        return (
            "\t" + ", ".join([
                str(values[i]) if i in values else str(no_value(i))
                for i in batched_indexes
            ]) + ", % " + str(batched_indexes[0][-2])
        )
    if n == 2:
        return (
            "\t%" + ", ".join(indexes[-1][0]) + "\n" +
            "\n".join([
                matrix_creator(i, indexes, values, n - 1, no_value)
                for i in batched_indexes
            ])
        )

    result = ""
    for i, e in enumerate(batched_indexes):
        idxs = indexes[0][0]
        idx = list(idxs.keys())[i] if isinstance(idxs, dict) else idxs[i]

        result += (
            "\n\t% " + idx +
            "\n" + matrix_creator(e, indexes[1:], values, n - 1, no_value) +
            "\n"
        )
    return result

def construct_explicit(
    values: dict,
    indexes: list[tuple[set, str]],
    no_value: Callable[[int], str]
) -> str:
    only_indexes = list(product(*(i[0] for i in indexes)))
    batched_indexes = only_indexes
    for index_values, _ in list(reversed(indexes))[:-1]:
        batched_indexes = batcher(batched_indexes, len(index_values))

    return matrix_creator(
        batched_indexes,
        indexes,
        values,
        len(indexes),
        no_value
    ) + "\n]);"

def combine_comp_flav(c, f):
    separator = "_"
    return str(c) + separator + str(f)