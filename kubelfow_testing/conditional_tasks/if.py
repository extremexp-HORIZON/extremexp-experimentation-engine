from kfp import dsl

@dsl.component
def flip_coin() -> str:
    import random
    return random.choice(['heads', 'tails'])

@dsl.component
def my_comp():
   print('Conditional task executed!')

@dsl.pipeline
def my_pipeline():
    coin_flip_task = flip_coin()
    with dsl.If(coin_flip_task.output == 'heads'):
        conditional_task = my_comp()