# Trade description grammar

## Data Model

Every strategy either opens or closes a position. Each position may have 1 or more trades associated with it. As in the case of an option spread.

Each trade is stored in the following format

-   "time" : 1636727441.711505,
-   "date" : "2021-11-12",
-   "price" : 4.55,
-   "symbol" : "BBIG",
-   "quantity" : 69,
-   "orderId" : NumberLong("5303477251"),
-   "filled" : false,
-   "status" : "working",
-   "positionId" : ObjectId("618e7a91aead0d8a491bd4dd"),
-   "orderType" : "single",
-   "tradeType" : "SELL_SHORT",
-   "tradeDirection" : "OPEN",
-   "strategy" : "opex",
-   "positionType" : "single",
-   "entry_point" : "MARKET",
-   "close_date" : "2021-11-15"

Each position consists of the following

-   "time_created" : 1644417011.4469461,
-   "date_created" : "2022-02-09",
-   "date_exited" : null,
-   "time_exited" : null,
-   "strategy" : "spy",
-   "user" : "morgan",
-   "open" : true,
-   "closed" : false,
-   "exit_placed" : false,
-   "enter_trades" : [ NumberLong("7606023526"), NumberLong("7606023526") ],
-   "exit_trades" : []

## Grammar

-   local variable = @
-   global context = ^
-   White space is meaningful.
-   Column names containing whitespace are escaped with single quotes ''
-   multiple column names are separated by commas
-   value : market attribute [CALL,PUT,MARKET,BUY_TO_OPEN] etc.
-   left : [var|column|panda_expr]
-   range : digit separator digit

### Input DSL

-   S expressions Expr : [var,op,expr|var|value|number]
-   If expr : [if expr then value [elif expr then value] else value]
-   Membership : [[not] in the portfolio]
-   Symbol Attribute: Price,volume etc. REAL TIME
-   Historical symbol Attributes: ... (currently csv/db)
-   Panda Expr : [agg(agg|column|position(days(range))) op expr|var|value|number]
-   Technical analysis: function_name, args

### JSON DSL

-   lazy expr : {"lambda":expr}
-   if expr : {"if:[[expr],value,[expr],value]}
-   math expr : [op,left,right]
-   func expr : [func,args] -> map(s_parser(args))

### Input FILTER GRAMMAR

-   column_expr: Column op expr|var|value|number
-   Membership : [not] in the portfolio
-   Query : given column_expr select panda_expr | where panda_expr select column_expr

### Trade Description Grammar

-   strategy:string
-   symbol_pool: [AAPL,TSLA...] | [positioning !earnings !biotech...]
-   position_description:
-   position_type: [single|spread] | if_expr
-   trade_type: VALUE [BUY|SELL|BUY_TO_OPEN|BUY_TO_CLOSE|SELL_TO_OPEN|SELL_TO_CLOSE] | if_expr
-   entry_point: VALUE [MARKET|2/3rds|MIDPOINT] | if_expr -> how to place the bid/ask
-   asset_type: VALUE [OPTION|EQUITY] | if_expr
-   scheduled_close?: INT [expr] -> trading days from opex
-   spread?:
-   buy:
-   strike: INT expr
-   expiration: datetime.date | var
-   contract_type: [PUT|CALL]
-   sell:
-   ""
-   betsize:
-   max:FLOAT expr -> maximum bankroll alloted for the strategy
-   per_trade:FLOAT expr -> maximum bankroll alloted per trade
-   stop?: FLOAT expr -> LAZY EVAL depends on open_position.symbol_filter typically distance from current symbol - price to place stop loss
-   open_position?:
-   on: [days digit separator digit]|market|day digit
-   at: hr:min [hr:min...]
-   when:
-   [expr expr...]
-   symbol_filter?:
-   [filter_expr filter_expr...]
-   close_position?:
-   ""

## Compiler

syntax context is understood on a single pass
Reqs:
All tokens and token types.
All valid operations with tokens and sequences.

Compiles nested dictionary of trade description
Scans tokens (regex)
Computes types on tokens
Checks types for errors
prepends local vars and context with @ and ^
orders symbol_filter according to api fetching
Converts text format into json format for interpreting

## Global context

-   portfolio -> Symbols, Balance, Buying power etc.
-   real time attributes -> price lookup
-   CSVs -> positioning, stock_fundamentals, iv

symbol_pool symbols
user set variables (just in case)

Local context:
current symbol

intermediate layer that fetches data and sends data for the interpreter.
has access to the db, csvs and tda api.
When the interpreter queries a value like SPY. it needs to return the price. This would be all the symbol tickers.
various portfolio
historical spy is csv lookup. which should be stored for the market duration.
any other csv lookup should also be stored for the duration.

## Interpreter

Uses the context interface to query data and send orders.
Uses pulled operations functions to resolve symbol filters

Evals all the expressions using queried data
Uses symbol filter functions
loads state lazily as needed
lazy s parser for parsing s expressions and more customized expressions

## Lazy evaluation

If the variable returns None, return the dependancy. Traverse the dependancy tree and solve all dependancies required
to run the function. this way no preload step is required. Everything will be loaded on a as needed basis.
there will be a repository layer, that shuttles requests from the interpreter to TDA and csvs. Depending on the request,
it will store the result in redis (spy 20 day mean for example) with high or low expiration timeout.

### Global context

global context is computed in sequence

1. Market Context: state of the market at that time, time of day, opex date, distance.
2. Trade Context: computed by the interpreter at runtime.

### Local State

batch fetch symbol attrs.
local state when filter symbols 1 at a time, consisting of all the symbol attributes and local function vars. These are more like getters.

### Filter functions

Have a forward and a backward component
forward always returns a list of symbols
backward returns None
Forward filters the function normally. Each function has access to the global context of the interpreter and local symbol attributes.
Backward is for testing purposes and modifies test CSVs (or potentially dbs) to make sure the desired outcome is satisfied.

input syntax regex
input parser function
forward function
backward function

Data fetch
fetch market context
eval trade description

params['spy] = tda.fetch(spy)
params['spy'] = lambda : tda.fetch(spy)
eval(@spy < 5)

### Extendable

In order for the language to be easily extendable. All filtering functions must stay apart from the interpreter.
All interpreter state global and local is just getters and setters? with setters being optional.
TDA stuff goes through the API which only actually calls if the value has expired.
Local variables will be symbol names and attrs.

## Websocket

Realtime monitors account trades -> updates db when trade is filled.

## Infrastructure

DB interface.

## Testing

Redis and mongodb must be running prior.
Automated testing. Where each side of boolean expressions are tested. Where success and failure modes are tested by passing 1 symbol all the way down or not.
Requires S expressions to be formed in a specific way with the var in the middle and any S expr on the right.
