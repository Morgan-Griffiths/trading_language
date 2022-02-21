from src.infrastructure.redis_layer import RedisInterface


def test_set_and_get(redis: RedisInterface):
    redis.store_value("key", "hi")
    val = redis.retrieve_value("key")
    assert val == "hi"


def test_set_and_get_list(redis: RedisInterface):
    redis.store_value("key", ["hi"])
    val = redis.retrieve_value("key")
    assert val == ["hi"]


def test_set_and_get_dict(redis: RedisInterface):
    redis.store_value("key", {"hi": "ho"})
    val = redis.retrieve_value("key")
    assert val == {"hi": "ho"}
