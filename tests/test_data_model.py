from src.infrastructure.database_layer import DataBase
import bson

""" Interpreter places trades. Streaming updates trade and position according to trade outcome """


def test_open_position(db: DataBase, teardown):
    positionId = db.create_position("me", "opex")
    assert isinstance(positionId, bson.ObjectId)


def test_insert_open_order_and_update_position(db: DataBase, teardown):
    positionId = db.create_position("me", "opex")
    orderId = 234234
    db.store_order({}, 5, "TSLA", 50, orderId, positionId)
    db.update_position_open(positionId)
    db.add_enter_trade_to_position(positionId, orderId)
    positions = db.return_open_positions("opex")
    print("positions", positions)
    assert positions[0] == positionId
    position = db.return_position_orders([positionId])[0]
    assert position["price"] == 5
    assert position["symbol"] == "TSLA"
    assert position["quantity"] == 50
    assert position["orderId"] == orderId
    assert position["positionId"] == positionId


def test_open_exit_position(db: DataBase, teardown):
    positionId = db.create_position("me", "opex")
    open_orderId = 234234
    db.store_order({"tradeDirection": "open"}, 5, "TSLA", 50, open_orderId, positionId)
    db.update_position_open(positionId)
    db.add_enter_trade_to_position(positionId, open_orderId)
    close_orderId = 432432
    db.store_order(
        {"tradeDirection": "close"}, 6, "TSLA", 50, close_orderId, positionId
    )
    db.update_position_close(positionId)
    db.add_exit_trade_to_position(positionId, open_orderId)
    positions = db.return_open_positions("opex")
    assert positions == []
    positions = db.return_exit_placed_positions("opex")
    assert positions != []


def test_open_close_position(db: DataBase, teardown):
    positionId = db.create_position("me", "opex")
    open_orderId = 234234
    db.store_order({"tradeDirection": "open"}, 5, "TSLA", 50, open_orderId, positionId)
    db.update_position_open(positionId)
    db.add_enter_trade_to_position(positionId, open_orderId)
    close_orderId = 432432
    db.store_order(
        {"tradeDirection": "close"}, 6, "TSLA", 50, close_orderId, positionId
    )
    db.update_position_close(positionId)
    positions = db.return_open_positions("opex")
    assert positions == []
    positions = db.return_exit_placed_positions("opex")
    assert positions != []
    # finalize close after exit is confirmed
    db.close_position(positionId)
    positions = db.return_exit_placed_positions("opex")
    assert positions == []
