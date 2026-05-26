
def check_results_less_than(threshold, results):
    print("===========")
    print(threshold)
    print(results)
    print("===========")
    # return results['S1'][1]['result']['output'] < int(threshold)
    return results['S1'][1]['result']['Task1']['ParamIncreasedBy5'] < int(threshold)

