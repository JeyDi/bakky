import uuid

# import notifyme as nme
from celery import current_task
from loguru import logger

from app.core.config import settings
from app.core.utils.logs import Profiler
from app.infrastructure.celery.engine import app


def reinitialize_logger(request_id: int) -> Profiler:
    """Re-initializes the logger and returns a Profiler object.

    Args:
        request_id (int): The ID of the request/task.

    Returns:
        Profiler: The Profiler object used for logging.

    Raises:
        Exception: If an error occurs while processing the task.

    """
    # Celery keeps messing with our logging setup, so we need to re-initialize the logger
    settings._setup_logger()
    correlation_id = str(uuid.uuid4())
    with logger.contextualize(correlation_id=correlation_id):
        profiler = Profiler()
        profiler.info(f"Start processing task: {request_id}", task_id=request_id, checkpoint=1)
        profiler.info(f"Fetched task: {request_id}", task_id=request_id, checkpoint=2)
        try:
            profiler.info("Loaded index", task_id=request_id, checkpoint=3)
            profiler.info(
                "Finished processing of task",
                task_id=request_id,
                checkpoint=18,
            )
            return profiler
        except Exception as e:
            profiler.error("Was not able to complete the task", task_id=request_id, exception=e)
            raise e


@app.task(name="bakki.notify_test")
def notify_test(message: str = None) -> str:
    """Small atomic celery test task.

    Args:
        message (str, optional): A message you want to use. Defaults to None.

    Raises:
        Exception: If it's impossible to compose the message

    Returns:
        str: The elaborated message by the function
    """
    request_id = current_task.request.id
    return f"Result message: {message}" + f"\nTask_id: {request_id}"


@app.task(name="bakky.test_function")
def test_function() -> None:
    """Launch a style test with logger.

    Args:
        request_id (int): the id of the task to execute
        write_to_db (bool, optional): Wether to write the results of the task to the DataBase or not. Defaults to True.

    Returns:
        None
    """
    # Celery keeps messing with our logging setup, so we need to re-initialize the logger
    settings._setup_logger()
    correlation_id = str(uuid.uuid4())
    request_id = current_task.request.id
    with logger.contextualize(correlation_id=correlation_id):
        profiler = Profiler()
        profiler.info("Start processing task", task_id=request_id, checkpoint=1)
        try:
            profiler.info("Loaded index", task_id=request_id, checkpoint=3)
            profiler.info(
                "Finished processing of task",
                task_id=request_id,
                checkpoint=18,
            )
            # nme.send_google_chat_message("Bakky test function")
        except Exception as e:
            profiler.error("Was not able to complete the task", task_id=request_id, exception=e)
            # nme.send_google_chat_message("Bakky test function")
