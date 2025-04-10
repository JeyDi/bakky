import time


class AppCache:
    """A class representing an application cache.

    Attributes:
        cache (dict): A dictionary to store the cached items.
        threshold_seconds (int): The threshold time in seconds for item expiration.

    Methods:
        __init__(self, threshold_seconds): Initializes the AppCache object.
        _current_time(self): Returns the current time.
        _is_expired(self, timestamp): Checks if a given timestamp is expired.
        add_item(self, *keys, value): Adds an item to the cache.
        get_item(self, *keys): Retrieves an item from the cache.
        remove_item(self, *keys): Removes an item from the cache.
        clean_cache(self): Cleans the cache by removing expired items.
    """

    def __init__(self, threshold_seconds):
        self.cache = {}
        self.threshold_seconds = threshold_seconds

    def _current_time(self):
        return time.time()

    def _is_expired(self, timestamp):
        return self._current_time() - timestamp > self.threshold_seconds

    def add_item(self, *keys, value):
        """Adds an item to the cache with the specified keys and value.

        Args:
            *keys: Variable number of keys used to access the item in the cache.
            value: The value to be stored in the cache.

        Returns:
            None
        """
        current_time = self._current_time()
        d = self.cache
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = {"value": value, "timestamp": current_time}

    def get_item(self, *keys):
        """Retrieve an item from the cache using the specified keys.

        Args:
            *keys: Variable number of keys used to access the item in the cache.

        Returns:
            The value associated with the specified keys in the cache, or None if the item is not found or has expired.
        """
        d = self.cache
        for key in keys:
            if key not in d:
                return None
            d = d[key]
        if self._is_expired(d["timestamp"]):
            self.remove_item(*keys)
            return None
        return d["value"]

    def remove_item(self, *keys):
        """Remove an item from the cache using the specified keys.

        Args:
            *keys: Variable number of keys representing the path to the item in the cache.

        Returns:
            None

        Raises:
            None
        """
        d = self.cache
        for key in keys[:-1]:
            if key not in d:
                return
            d = d[key]
        if keys[-1] in d:
            del d[keys[-1]]

    def clean_cache(self):
        """Clean the cache by removing expired entries.

        This method recursively traverses the cache and removes any entries that have expired.
        An entry is considered expired if it is a dictionary and contains a "timestamp" key,
        and the value of the "timestamp" key indicates that it has expired.

        Note: This method modifies the cache in-place.

        Returns:
            None
        """

        def recursive_clean(d):
            keys_to_delete = []
            for key, value in d.items():
                if isinstance(value, dict) and "timestamp" in value:
                    if self._is_expired(value["timestamp"]):
                        keys_to_delete.append(key)
                elif isinstance(value, dict):
                    recursive_clean(value)
            for key in keys_to_delete:
                del d[key]

        recursive_clean(self.cache)
