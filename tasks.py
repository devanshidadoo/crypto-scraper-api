# tasks.py
from celery import Celery, chord
from scraper import process_url

celery_app = Celery(
    "crypto_scraper",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

@celery_app.task(bind=True, name="tasks.process_url_task", max_retries=2, default_retry_delay=5)
def process_url_task(self, url: str) -> dict:
    try:
        return process_url(url)
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task(name="tasks.aggregate_results")
def aggregate_results(results: list[dict]) -> list[dict]:
    return results

def scrape_batch(urls: list[str]):
    """
    Enqueue a batch of URLs; returns an AsyncResult whose .get()
    yields the list of processed dicts.
    """
    tasks = [process_url_task.s(url) for url in urls]
    job = chord(tasks)(aggregate_results.s())
    return job
