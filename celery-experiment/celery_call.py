import celery_tasks

# res = celery_tasks.add.delay(10, 11)
a = 1

task = celery_tasks.long_sum.delay(100 ** 10)
a = 1

