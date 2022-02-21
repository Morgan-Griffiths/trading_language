import redis
import json
import datetime


class RedisInterface(object):
    def __init__(self, expiration=30):
        self.expiration = expiration
        self.db = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)

    def set_value(self, key: str, value: str, expiration=None):
        if expiration is not None:
            self.db.set(key, value, ex=expiration)
        else:
            self.db.set(key, value, ex=self.expiration)

    def set_dict(self, key: str, value: dict):
        self.db.hmset(key, value)

    def get_dict(self, key: str):
        self.db.hget(key)

    def get_value(self, key: str):
        return self.db.get(key)

    def store_value(self, key, value, expiration=None):
        assert not isinstance(value, set), "Set storage not supported"
        if isinstance(value, list) or isinstance(value, dict):
            json_value = json.dumps(value)
            self.set_value(key, json_value, expiration)
        elif (
            isinstance(value, datetime.date)
            or isinstance(value, datetime.datetime)
            or isinstance(value, datetime.timedelta)
        ):
            self.set_value(key, str(value), expiration)
        else:
            self.set_value(key, value, expiration)

    def retrieve_value(self, key):
        value = self.get_value(key)
        try:
            json_value = json.loads(value)
            return json_value
        except:
            return value
