# FILE FOR LOADING ADDITIONAL DATA

def load_regions():
    with open('app_data/regions.txt', 'r') as file:
        regions = file.read().split('\n')
    return regions


REGIONS = load_regions()
