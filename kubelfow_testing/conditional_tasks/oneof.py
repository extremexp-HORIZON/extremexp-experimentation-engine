from kfp import dsl

@dsl.component
def flip_three_sided_coin() -> str:
    import random
    return random.choice(['heads', 'tails', 'draw'])

@dsl.component
def print_and_return(text: str) -> str:
    print(text)
    return text

@dsl.component
def announce_result(result: str):
    print(f'The result is: {result}')

@dsl.pipeline
def my_pipeline() -> str:

    #  What dsl.OneOf Does
    #  The dsl.OneOf construct creates a conditional output selector that will contain the output from whichever task actually executed based on the conditional logic above it.

    #  How It Works
    #  Since your pipeline uses conditional execution (dsl.If, dsl.Elif, dsl.Else), only one of the three tasks (t1, t2, or t3) will actually run:
    #
    #  If coin flip = 'heads' → only t1 executes
    #  If coin flip = 'tails' → only t2 executes
    #  If coin flip = anything else → only t3 executes
    #  dsl.OneOf intelligently selects the output from whichever task actually ran, effectively "merging" the three possible execution paths back into a single value.

    #  Key Benefits
    #  Type Safety: Ensures your pipeline has a consistent return type despite branching logic
    #  Clean Data Flow: Allows downstream tasks (like announce_result) to consume the result without knowing which branch executed
    #  Pipeline Orchestration: Enables the pipeline to return a single coherent output regardless of the conditional path taken
    #  Gotcha 🚨
    #  All parameters to OneOf must have the same data type. Since t1.output, t2.output, and t3.output are all strings in your case, this works perfectly. If they were different types, you'd get a validation error.

    #  Think of it like a railway switch that automatically routes the "active train" (executed task output) onto the main track for the rest of your pipeline to use.

    coin_flip_task = flip_three_sided_coin()
    with dsl.If(coin_flip_task.output == 'heads'):
        t1 = print_and_return(text='Got heads!')
    with dsl.Elif(coin_flip_task.output == 'tails'):
        t2 = print_and_return(text='Got tails!')
    with dsl.Else():
        t3 = print_and_return(text='Draw!')
    
    oneof = dsl.OneOf(t1.output, t2.output, t3.output)
    announce_result(oneof)
    return oneof