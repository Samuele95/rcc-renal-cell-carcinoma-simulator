def get_dimension_from_volume(volume: float, block_size: int = 10) -> int:
    micron_volume = volume * 10 ** 12
    root = (micron_volume ** (1 / 3)) / block_size
    return int(root)


def get_number_of_cells_from_concentration(cell_concentration: int, volume: float) -> int:
    return int(cell_concentration * volume)
