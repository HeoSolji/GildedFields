# utils.py
import random
import config
import numpy as np

def determine_quality():
    qualities = [5, 3, 2, 1, 0]
    chances = [
        config.STAR_QUALITY_CHANCE.get(5, 0),
        config.STAR_QUALITY_CHANCE.get(3, 0),
        config.STAR_QUALITY_CHANCE.get(2, 0),
        config.STAR_QUALITY_CHANCE.get(1, 0),
        1 - sum(config.STAR_QUALITY_CHANCE.values())
    ]
    result = int(np.random.choice(qualities, p=chances))
    print("Chất lượng cây vừa trồng:", result)
    return result