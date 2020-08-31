def with_precision(val, precision):
    """
    Round `val` to the closest multiple of `precision`.
    """
    return float(round(val / precision) * precision)
