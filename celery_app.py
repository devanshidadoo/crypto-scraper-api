from celery import Celery

# name your app and point to the Redis broker
app = Celery(
    "nlp_tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1"
)

# Optional: configure task serialization, timeouts, etc.
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_annotations={"*": {"rate_limit": "10/s"}}
)
