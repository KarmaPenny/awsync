import boto3
import json
import sys
from time import sleep
from typing import Union, Any
from uuid import UUID, uuid4


# patch default json encoder to allow classes to define how they get encoded via to_json method
json_default_encoder = json.JSONEncoder().default
def json_encoder(self, obj):
    return getattr(obj.__class__, "to_json", json_default_encoder)(obj)
json.JSONEncoder.default = json_encoder


class Channel():
    """Class for passing data between lambda instances"""

    def __enter__(self):
        """creates a new sqs queue to use as the underlying message queue for the channel"""
        name = str(uuid4())
        sqs = boto3.client("sqs")
        sqs.create_queue(QueueName=name)
        self.url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
        return self

    def __exit__(self, *args):
        """deletes the underlying sqs queue when we are done"""
        boto3.client("sqs").delete_queue(QueueUrl=self.url)
        
    def to_json(self):
        """enables json encoding of Channel objects"""
        return self.__dict__

        
def push(c: Union[Channel, dict], message: Any):
    """pushes a message onto a Channel

    Args:
        c: the channel to push the message onto
        message: a json encodable object to push onto the channel
    """
        
    url = c.url if isinstance(c, Channel) else c["url"]
    boto3.client("sqs").send_message(QueueUrl=url, MessageBody=json.dumps(message))


def pop(c):
    """pops a message off a Channel, blocks until a message is received

    Args:
        c: the channel to pop a message from

    Returns:
        the message that was popped off the channel
    """

    url = c.url if isinstance(c, Channel) else c["url"]
    messages = []
    while not messages:
        messages = boto3.client("sqs").receive_message(QueueUrl=url).get("Messages", [])
    return json.loads(messages[0]["Body"])

_context = None
def invoke(method, *args, **kwargs):
    """invokes a given method in a new lambda instance

    Args:
        method: the method to invoke inside the new lambda instance
        args: the positional args to pass to the method when invoked
        kwargs: the key word args to pass to the method when invoked
    """

    payload = json.dumps({
        "module": method.__module__,
        "method": method.__name__,
        "args": args,
        "kwargs": kwargs,
    })
    boto3.client("lambda").invoke(
        FunctionName=_context.function_name,
        InvocationType="Event",
        Payload=payload.encode("utf-8"),
    )


def lambda_handler(event: dict, context):
    """runs a given method pass in via event payload

    Args:
        event: contains the method to run as well as the args to pass to the method
        context: contains information about the lambda function that is running
    """

    # save the context in case we need to invoke a new copy of this lambda
    global _context
    _context = context

    # get the method specified in the event payload, default to main
    method = getattr(sys.modules[event.get("module", __name__)], event.get("method", "main"))

    # run the method
    result = method(*event.get("args", []), **event.get("kwargs", {}))

    # return the result
    return {"statusCode": 200, "body": json.dumps(result)}


def square(c, i):
    """ this code runs asynchronously in a different lambda instance """
    push(c, i * i)

    
def main():
    """This is the entry point of the first lambda instance"""

    total = 0

    # open a channel to communicate between lambda instances
    with Channel() as c:
        # spawn 5 new lambda instances to square each number in parallel
        for i in range(5):
            invoke(square, c, i)

        # add the results from each lambda together 
        for i in range(5):
            total += pop(c) 

    return total
