from typing import Any
import redis


class RedisInterface(object):
    def __init__(self, expiration=30):
        self.expiration = expiration
        self.db = redis.Redis(host="localhost", port=6379, db=1)

    def set_value(self, key: str, value: str):
        self.db.set(key, value, ex=self.expiration)

    def set_dict(self, key: str, value: dict):
        self.db.hmset(key, value)

    def get_dict(self, key: str):
        self.db.hget(key)

    def get_value(self, key: str):
        return self.db.get(key)
