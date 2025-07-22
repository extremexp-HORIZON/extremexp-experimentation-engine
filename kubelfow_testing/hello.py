import kfp

kfp_client = kfp.Client()

@kfp.dsl.component
def say_hello(name: str) -> str:
    hello_text = f'Hello, {name}!'
    print(hello_text)
    return hello_text

@kfp.dsl.pipeline
def hello_pipeline(recipient: str) -> str:
    hello_task = say_hello(name=recipient)
    return hello_task.output

kfp_client.create_run_from_pipeline_func(
    hello_pipeline,
    arguments={
        "recipient": "World",
    }
)