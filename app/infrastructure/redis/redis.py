import asyncio
import json
from datetime import timedelta
from typing import Any

import redis
from loguru import logger
from redis import asyncio as ars

from app.core.config import settings


def sync_redis_connect(
    redis_config: dict = settings.REDIS_CONFIG,
) -> redis.Redis:
    """Connect to a Redis database with a synchronous connection.

    Args:
        redis_config (dict, optional): Redis configuration dict. Defaults to settings.REDIS_CONFIG.

    Returns:
        redis.Redis: Redis connection object (synchronous).
    """
    redis_user = redis_config["user"]
    redis_password = redis_config["password"]
    redis_port = int(redis_config["port"])
    redis_address = redis_config["address"]
    redis_encoding = redis_config["encoding"]
    redis_db = int(redis_config["db"])

    try:
        conn = redis.from_url(
            f"{redis_address}:{redis_port}",
            encoding=redis_encoding,
            db=redis_db,
            username=redis_user,
            password=redis_password,
            decode_responses=True,
        )
        ping = conn.ping()
        logger.debug("Redis cache connection: ok")
        if ping is True:
            return conn
        raise redis.ConnectionError
    except redis.AuthenticationError as message:
        logger.error(f"Redis auth error: {message}")
        logger.exception(f"Redis auth error: {message}")
        raise redis.AuthenticationError from message


def sync_redis_close(conn: redis.Redis) -> bool:
    """Gracefully close underlying connection.

    Args:
        conn (redis.Redis): Connection

    Returns:
        bool: Whether connection was closed
    """
    # gracefully closing underlying connection
    try:
        if conn.ping():
            conn.close()
            return True
        return False
    except redis.ResponseError as message:
        m = f"Impossible to close the connection, because: {message}"
        logger.error(m)
        raise Exception(m) from message


async def redis_connect(
    redis_config: dict = settings.REDIS_CONFIG,
) -> ars.Redis:
    """Connect to a Redis database.

    Args:
        redis_config (dict, optional): Redis configuration dict. Defaults to settings.REDIS_CONFIG.

    Raises:
        ars.ConnectionError: Could not reach database
        ars.AuthenticationError: Authentication error

    Returns:
        ars.Redis: Redis Async connection object
    """
    redis_user = redis_config["user"]
    redis_password = redis_config["password"]
    redis_port = int(redis_config["port"])
    redis_address = redis_config["address"]
    redis_encoding = redis_config["encoding"]
    redis_db = int(redis_config["db"])

    try:
        conn = await ars.from_url(
            f"{redis_address}:{redis_port}",
            encoding=redis_encoding,
            db=redis_db,
            username=redis_user,
            password=redis_password,
            decode_responses=True,
        )
        # val = await conn.execute('GET', 'my-key')
        ping = await conn.ping()
        logger.debug("Redis cache connection: ok")
        if ping is True:
            return conn
        raise ars.ConnectionError
    except ars.AuthenticationError as message:
        logger.error(f"Redis auth error: {message}")
        logger.exception(f"Redis auth error: {message}")
        raise ars.AuthenticationError from message


async def redis_close(conn: ars.Redis) -> bool:
    """Gracefully close underlying connection.

    Args:
        conn (ars.Redis): Connection

    Raises:
        Exception: Error when closing connection

    Returns:
        bool: Whether connection was closed
    """
    # gracefully closing underlying connection
    try:
        if await conn.ping():
            await conn.aclose()
            return True
        return False
    except ars.ResponseError as message:
        m = f"Impossible to close the connection, because: {message}"
        logger.error(m)
        raise Exception(m) from message


async def get_data(client: ars.Redis, key: str) -> str:
    """Get data from redis.

    Args:
        client (Redis): Redis connection
        key (str): Key to get the data from

    Raises:
        Exception: Error when getting the data

    Returns:
        str: Json data
    """
    try:
        return await client.get(key)
        # val = client.get(key)
    except ars.ResponseError as message:
        m = f"Impossible to get the data with key: {key}, because: {message}"
        logger.error(m)
        logger.exception(m)
        raise Exception(m) from message


async def get_list_keys(client: ars.Redis | None = None, pattern: str = "*") -> list:
    """Get the list of keys matching a pattern.

    Args:
        client (Redis, optional): Redis connection. Defaults to None.
        pattern (str, optional): Regex pattern to use for matching keys. Defaults to "*".

    Raises:
        Exception: Error when getting the list of keys

    Returns:
        list: List of keys in the Redis database
    """
    try:
        if not client:
            # Get the client
            client = await redis_connect()

        keys = await client.keys(pattern)
        logger.debug(f"Redis number of existing keys: {len(keys)}")
        return keys
    except ars.ResponseError as message:
        m = f"Impossible to get the list of keys with pattern: {pattern}, because: {message}"
        logger.error(m)
        logger.exception(m)
        raise Exception(m) from message


async def clear_data(
    key: str, direct: bool = True, namespace: str | None = None, client: ars.Redis | None = None
) -> bool:  # noqa
    """Clear and delete cache data from redis database.

    This function work in 2 different ways:
    1. If direct is True, it will delete the key directly from redis database.
    2. If direct is False, it will delete the key from redis database using a lua script composed with key and namespace. Be carefull because with direct = False you can delete all the keys that match the lua expression built.

    Args:
        key (str): the key of the data you want to delete
        direct (bool, optional): If you want to direct delete the data instead using a lua expression function. Defaults to True.
        namespace (str, optional): Namespace. Defaults to None.
        client (Redis, optional): Async Redis client object. Defaults to None.

    Raises:
        Exception: If it's impossible to delete the data

    Returns:
        bool: True if the data was deleted. Otherwise False or exception
    """
    if not client:
        # Get the client
        client = await redis_connect()
    try:
        if not direct:
            if namespace:
                lua = f"for i, name in ipairs(redis.call('KEYS', '{namespace}:*')) do redis.call('DEL', name); end"
            else:
                lua = f"for i, name in ipairs(redis.call('KEYS', '*{key}*')) do redis.call('DEL', name); end"
            if client.eval(lua, key):
                return True
            return False
        await client.delete(key)
        logger.debug(f"Redis data clear: {key}")
        return True
    except ars.ResponseError as message:
        m = f"Impossible to clear the data with key: {key}, because: {message}"
        logger.error(m)
        logger.exception(m)
        raise Exception(m) from message


async def save_data(client: ars.Redis, key: str, value: str, expire: int | timedelta | None = None) -> Any:
    """Save the data to redis database cache.

    You can set also an expiration time in seconds.
    After the expiration time the key will be automatically deleted by redis.

    Args:
        client (ars.Redis): the Redis connection async object
        key (str): the unique key of your cache (watch the keybuilder functionality if you want to know how to build a key)
        value (str): the data you want to save in the cache
        expire (int, optional): the expiration time in seconds. Defaults to None and it will be created 3600 second for the object.

    Raises:
        Exception: Response error if it's impossible to save the data

    Returns:
        any: the state of the operation
    """
    try:
        if not expire:
            expire = timedelta(seconds=3600)

        state = await client.set(
            key,
            value=value,
            ex=expire,
        )
        logger.debug(f"Redis cache saved: {key}")
        return state
    except ars.ResponseError as message:
        m = f"Impossible to save the data with key: {key}, because: {message}"
        logger.error(m)
        logger.exception(m)
        raise Exception(m) from message


async def update_data(key: str, new_data: dict, client: ars.Redis | None = None, expire: int | None = None) -> dict:
    """Update a redis cache key with a new data.

    If the key it's not present in the database it will be created a new one.

    Args:
        key (str): the key of your db cache object
        new_data (dict): the new data you want to save in the cache
        client (ars.Connection, optional): the redis connection client object. Defaults to None.
        expire (int, optional): the expiration time in second. Defaults to None and will be updated to 3600 seconds by default.

    Returns:
        dict: The data inserted in the cache redis db
    """
    if not client:
        # Get the client
        client = await redis_connect()

    # check if the value exist
    old_data = await get_data(client=client, key=key)

    if old_data:
        # delete the previous record
        await client.delete(key)

    # create the new object
    new_data_str = json.dumps(new_data)
    state = await save_data(client=client, key=key, value=new_data_str, expire=expire)

    if state is True:
        data = json.loads(new_data_str)
    logger.debug(f"Redis cache updated: {key}")
    return data


async def redis_cache_flow(key: str, new_data: dict, expire: int | None = None, update: bool = False) -> Any:
    """Function to use the redis cache flow inside your project asynchronously.

    Args:
        key (str): the key of your data (please refear to the key builder if you want to generate e useful hash key, but you can use whatever key string you want)
        new_data (dict): the data you want to cache
        update (bool, optional): if you want to force the update of an existing value. Defaults to False.

    Returns:
        dict: the result dict with the key and values inserted
    """
    # Get the client
    client = await redis_connect()

    # First it looks for the data in redis cache
    data = await get_data(client=client, key=key)
    state = False

    # If cache is found then serves the data from cache
    if data is not None:
        if update:
            data = json.dumps(new_data)
            state = await update_data(key=key, new_data=new_data, client=client, expire=expire)

    # If cache is not found save the object
    else:
        # This block sets saves the respose to redis and serves it directly
        data = json.dumps(new_data)
        state = await save_data(client=client, key=key, value=data, expire=expire)

    if state is True:
        data = json.loads(data)

    await redis_close(client)
    logger.debug(f"Redis cache: {key}")
    return data


# Global usable functions with asyncio support
def redis_cache(key: str, new_data: dict, **kwargs: dict[str, int | bool | None]) -> dict:
    """Function to use the redis cache inside your project synchronously.

    Be careful: if a record it's already in the db with the same key, it will not be updated by default.

    You can set an expiration date with the `expire` (int) parameter.
    You can also set `update` (bool) to True if you want to force the update of a record if it's already present inside the db with the new_data

    Args:
        key (str): your key name to save the data
        new_data (dict): your data to save
        **kwargs (dict): optional arguments to pass to the redis_cache_flow function. For example you can pass expiration time in seconds (int) or update = True if you want to update the data if there is a key already in the cache saved before.

    Returns:
        dict: the data saved inside redis
    """
    expire = kwargs.pop("expire", None)
    update = kwargs.pop("update", False)
    if not isinstance(expire, (int, type(None))):
        raise ValueError("expire must be int or None")
    if not isinstance(update, bool):
        raise ValueError("update must be bool")
    return asyncio.run(redis_cache_flow(key, new_data, expire=expire, update=update))


def redis_cache_delete(key: str, namespace: str | None = None, direct: bool = True) -> bool:
    """Function to delete a redis cache value inside your project synchronously.

    If the record (with the key) is not found inside redis it returns False.

    By default (if direct = True) the function directly delete the value from redis using your key.
    If you want to use a lua script to delete something you can set direct = False and the function will compose a lua script to create a pattern matching with your key and namespace.
    Be carefull because if you use direct = False probably you will delete some other keys and not only a single one

    Args:
        key (str): your key name of the record you want to delete
        namespace (str, optional): if you want to use a namespace to search in the redis db. Defaults to None.
        direct (bool ,otional): If you want to delete directly instead evaluate lua script and do a research. Defaults to False.

    Returns:
        bool: _description_
    """
    return asyncio.run(clear_data(key, namespace=namespace, direct=direct))


def redis_cache_keys(pattern: str = "*") -> list:
    """Get the list of keys inside the redis cache db.

    You can use a pattern search query to search inside the database and match different values.

    By default the function research for every values inside the database.

    Args:
        pattern (str, optional): the query search string you want to use. Defaults to "*" to search and gather everything.

    Returns:
        list: the list of the keys founded inside the redis cache db.
    """
    return asyncio.run(get_list_keys(pattern=pattern))


def redis_cache_update(key: str, data: dict) -> dict:
    """Redis cache update synchronous function to update a value inside the database.

    If a record is not present, the function will create a new one by default.

    Args:
        key (str): the key of your record
        data (dict): the data you want to update

    Returns:
        dict: the result data after the update or new insert.
    """
    return asyncio.run(update_data(key, data))
