from kfp import dsl

@dsl.component
def flip_three_sided_coin() -> str:
    import random
    return random.choice(['heads', 'tails', 'draw'])

@dsl.component
def print_comp(text: str):
    print(text)

@dsl.pipeline
def my_pipeline():
    coin_flip_task = flip_three_sided_coin()
    with dsl.If(coin_flip_task.output == 'heads'):
        print_comp(text='Got heads!')
    with dsl.Elif(coin_flip_task.output == 'tails'):
        print_comp(text='Got tails!')
    with dsl.Else():
        print_comp(text='Draw!')