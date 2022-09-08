# AWSync
Provides golang style concurrency in AWS for python

### Usage
The following example sums the squares of the numbers 0-4 in parallel. The main lambda spawns 5 new lambdas to calculate the square of each number and then adds the results together as they complete. A Channel object is used to push the results of each square operation to the main lambda.

```python
from awsync import *

def square(c, i):
  push(c, i * i)
  
def main():
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
```

### How it works
When a Channel is opened a new SQS queue is created. The Channel object can be passed to invoked lambdas to allow for communication between lambdas via pushing/popping messages on the Channel. When a Channel is closed the underlying SQS queue is deleted.

Calling invoke on a function spawns a new instance of the main lambda which executes the function with the provided arguments.

### Setup
To use awsync you'll need to create a lambda function from an docker image. Install the awsync package on the image and import it in your script. Make sure to give the lambda function permission to Invoke Functions as well as read, write and create SQS queues.
