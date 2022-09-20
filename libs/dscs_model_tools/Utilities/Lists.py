import re


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def flip_dict(dct):
    return {v: k for k, v in dct.items()}


def natural_sort(l, accessor=lambda x: x):
    """
    Adapted from https://stackoverflow.com/a/4836734
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=lambda x: alphanum_key(accessor(x)))
