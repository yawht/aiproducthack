from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379', backend='redis://localhost:6379/0')

@app.task
def add(x, y):
    import time
    time.sleep(40)
    return x + y

@app.task
def print_result(x, y):
    import time
    time.sleep(40)
    return x + y

@app.task
def long_sum(x):
    res = 0
    for i in range(1, x+1):
        cur_value = 0
        for _ in range(i):
            cur_value += 1
        res += cur_value
    return res