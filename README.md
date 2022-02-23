# Trade description grammar

## Outline

Trading DSL for writing trading config text files that can then be compiled into json format and then read by the interpreter to execute the position according to the specifications. Written in key value format using colons. Capitalization is not meaningful.

The config file also specificies the time(s) and day(s) that the trade should trigger at. These are compiled by crontab and set to automatically trigger the interpreter with the given config file at the appropriate time.

Each config file describes a 'Position'. Each position contains one or more trades.

Example text configs and corresponding json outputs are contained in the input_descriptions and output_descriptions folders.

## Trade Description Grammar

-   strategy: `name of your strategy`
-   symbol_pool: `list of symbol names` or `csv file name with optional symbol filters`
-   position_description: `container for all the necessary position attributes`
-   -   trade_type: `[sell_short,buy] for equities. [sell_to_open,buy_to_open] for options`
-   -   position_type: `[single,spread] single trade per position, or spread.`
-   -   asset_type: `[equity,option]`
-   -   scheduled_close: `OPTIONAL. number of days before options expiration to exit position`
-   -   betsize: `container for betsize logic`
-   -   -   per_trade: `FLOAT EXPR [bankroll,net_position] amount per trade`
-   -   -   max_bet: `FLOAT EXPR [bankroll,net_position] maximum amount per position`
-   -   stop: `OPTIONAL FLOAT EXPR [symbol_price] place a stop loss when placing the trade`
-   -   entry_point: `[market,2/3rds,midpoint] how to place the order, market hits the ask/bid, [2/3rds,midpoint] places a limit order in between bid/ask`
-   -   spread: `OPTIONAL. OPTION ONLY. describes an option spread.`
-   -   -   sell: `SELL SIDE`
-   -   -   -   strike: `INT EXPR to calculate strike price.`
-   -   -   -   expiration: `EXPR to calculate expiration.`
-   -   -   -   contract_type: `[put,call]`
-   -   -   buy: `BUY SIDE`
-   -   -   -   strike: `INT EXPR to calculate strike price.`
-   -   -   -   expiration: `EXPR to calculate expiration.`
-   -   -   -   contract_type: `[put,call]`
-   open_position: `container for logic dictating when to enter the position`
-   -   On: `DAY EXPR: [MARKET,days int-int, day int] which days to trigger config`
-   -   At: `TIME EXPR: hr:min | [hr:min,hr:min] what times to trigger config`
-   -   When: `contianer for triggering conditions`
-   -   -   `CONDITIONAL EXPR. can have 1 or more. If more than 1 conditional exprs, join them with and`
-   -   symbol_filter: `container. filters symbols based on some criteria`
-   -   -   `FILTER EXPR`
-   close_position: `container for logic dictating when to exit the position`
-   -   On: `DAY EXPR: [MARKET,days int-int, day int] which days to trigger config`
-   -   At: `TIME EXPR: hr:min | [hr:min,hr:min] what times to trigger config`
-   -   When:`contianer for triggering conditions`
-   -   -   `CONDITIONAL EXPR. can have 1 or more. If more than 1 conditional exprs, join them with or`

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
-   Symbol Attribute: Price,volume etc. FETCHED IN REAL TIME
-   Historical symbol Attributes: ... (currently csv/db)
-   Panda Expr : [agg(agg|column|position(days(range))) op expr|var|value|number]

### Input filter grammar

-   column_expr: Column op expr|var|value|number
-   Membership : [not] in the portfolio
-   Query : given column_expr select panda_expr | where panda_expr select column_expr

## Compiler

syntax context is understood on a single pass

-   Compiles nested dictionary of trade description
-   Scans tokens (regex)
-   Computes types on tokens
-   Checks types for errors
-   prepends local vars and context with @ and ^
-   orders symbol_filter according to api fetching
-   Converts text format into json format for interpreting

### JSON DSL

-   local variable = @
-   global context = ^
-   lazy expr : {"lambda":expr}
-   if expr : {"if:[[expr],value,[expr],value]}
-   math expr : [op,left,right]
-   func expr : [func,args] -> map(s_parser(args))

## Global context

global context is computed in sequence

1. Market Context: state of the market at that time, time of day, opex date, distance.
2. Trade Context: computed by the interpreter at runtime.

4 types of global context

-   portfolio -> Symbols, Balance, Buying power etc.
-   real time attributes -> price lookup
-   CSVs -> positioning, stock_fundamentals, iv
-   user set variables (just in case)

## Local context

during evaluation you can access the current symbol price with symbol_price. For example

-   Volume > 2M and
-   IV > 50 and
-   mean(positioning(days(0 to 4))) < -0.0025 and
-   symbol_price > 2 and
-   order status rejected

interpreter batch fetchs symbol attrs.
local state when filter symbols 1 at a time, consisting of all the symbol attributes and local function vars. These are more like getters.

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

### Filter functions

-   Have a forward and a backward component
-   forward always returns a list of symbols
-   backward returns None
-   Forward filters the function normally. Each function has access to the global context of the interpreter and local symbol attributes.
-   Backward is for testing purposes and modifies test CSVs (or potentially dbs) to make sure the desired outcome is satisfied.

-   input syntax regex
-   input parser function
-   forward function
-   backward function

Data fetch

-   fetch market context
-   eval trade description
-   params['spy] = tda.fetch(spy)
-   params['spy'] = lambda : tda.fetch(spy)
-   eval(@spy < 5)

### Extendability

Everything is built in order to be easily extendable. All filtering functions are apart from the interpreter.
All interpreter state global and local is just getters and setters. With setters being optional.
TDA stuff goes through the API which only calls if the value has expired.
Local variables are symbol names and attrs.

## Websocket

Realtime monitors account trades -> updates db when trade is filled or rejected.

## Testing

-   Redis and mongodb must be running prior.
-   Automated testing. Where each side of boolean expressions are tested. Where success and failure modes are tested by passing 1 symbol all the way down or not.
-   Requires S expressions to be formed in a specific way with the var in the middle and any S expr on the right.
