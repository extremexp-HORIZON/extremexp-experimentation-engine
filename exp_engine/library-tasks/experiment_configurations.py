def configuration_filter_S2(combinations):
    valid_list = [
        {'param1_vp': 3},
        {'param1_vp': 5}
    ]
    filtered_combinations = []
    for c in combinations:
        if c in valid_list:
            filtered_combinations.append(c)
    return filtered_combinations


def configuration_generator_S2():
    generated_configurations_list = []
    c = {'param1_vp': 14}
    generated_configurations_list.append(c)
    return generated_configurations_list
