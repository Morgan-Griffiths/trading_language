const { ObjectId } = require('bson')
const mongoose = require('mongoose')
const Schema = mongoose.Schema

let positionSchema = new Schema({
    time: {
        type: Date,
        required: true,
    },
    date: {
        type: Date,
        required: true,
    },
    price: {
        type: Number,
        required: true,
    },
    symbol: { type: String, uppercase: true, required: true },
    quantity: { type: Number },
    positionId: { type: ObjectId, required: true },
    orderId: { type: Number, required: true },
    filled: { type: Boolean, required: true },
    status: { type: String, required: true }, // working,rejected,success
    orderType: { type: String, required: true }, // single,NET_debit,net_credit
    tradeType: { type: String, required: true }, // BUY,BUY_TO_OPEN,BUY_TO_CLOSE,SELL,SELL_TO_OPEN,SELL_TO_CLOSE
    tradeDirection: { type: String, required: true }, // OPEN,CLOSE
    strategy: { type: String, required: true },
    positionType: { type: String, required: true }, // single,spread
    entry_point: { type: String, required: true }, // MARKET,2/3rds,MIDPOINT
    close_date: { type: Date }, // Date of mandatory exit
    net_payment: { type: Number }, // Net amount for option spread
    buy_price: { type: Number }, // price for buy leg of spread
    buy_quantity: { type: Number }, // quantity for buy leg of spread
    buy_symbol: { type: String }, // option symbol for buy leg
    buy_instruction: { type: String }, // BUY_TO_OPEN,BUY_TO_CLOSE
    buy_price: { type: Number }, // price for sell leg of spread
    sell_quantity: { type: Number }, // quantity for sell leg of spread
    sell_symbol: { type: String }, // option symbol for sell leg
    sell_instruction: { type: String }, // SELL_TO_OPEN,SELL_TO_CLOSE
})

let workingOrderSchema = new Schema({
    time: {
        type: Date,
        required: true,
    },
    date: {
        type: Date,
        required: true,
    },
    price: {
        type: Number,
        required: true,
    },
    symbol: { type: String, uppercase: true, required: true },
    quantity: { type: Number },
    positionId: { type: ObjectId, required: true },
    orderId: { type: Number, required: true },
    filled: { type: Boolean, required: true },
    status: { type: String, required: true }, // working,rejected,success
    orderType: { type: String, required: true }, // single,NET_debit,net_credit
    tradeType: { type: String, required: true }, // BUY,BUY_TO_OPEN,BUY_TO_CLOSE,SELL,SELL_TO_OPEN,SELL_TO_CLOSE
    tradeDirection: { type: String, required: true }, // OPEN,CLOSE
    strategy: { type: String, required: true },
    positionType: { type: String, required: true }, // single,spread
    entry_point: { type: String, required: true }, // MARKET,2/3rds,MIDPOINT
    close_date: { type: Date }, // Date of mandatory exit
    net_payment: { type: Number }, // Net amount for option spread
    buy_price: { type: Number }, // price for buy leg of spread
    buy_quantity: { type: Number }, // quantity for buy leg of spread
    buy_symbol: { type: String }, // option symbol for buy leg
    buy_instruction: { type: String }, // BUY_TO_OPEN,BUY_TO_CLOSE
    buy_price: { type: Number }, // price for sell leg of spread
    sell_quantity: { type: Number }, // quantity for sell leg of spread
    sell_symbol: { type: String }, // option symbol for sell leg
    sell_instruction: { type: String }, // SELL_TO_OPEN,SELL_TO_CLOSE
})
module.exports = mongoose.model('working_orders', workingOrderSchema)
