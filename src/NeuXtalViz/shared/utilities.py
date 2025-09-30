def slider_to_value(value, range):
    return float(range[0] + (range[1] - range[0]) * float(value) / 100)


def value_to_slider(value, range):
    if range[0] == range[1]:
        return 0
    slider_value = int(100 * (float(value) - range[0]) / (range[1] - range[0]))

    if slider_value < 0:
        return 0
    if slider_value > 100:
        return 100
    return slider_value
