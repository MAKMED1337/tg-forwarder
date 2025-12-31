Simple telegram forwarder from one chat/channel to another.

You need to set `API_ID`, `API_HASH`, and optionally `BOT_TOKEN` (if not specified, the bot will forward as an actual user; however, it was **not tested**) in the `.env/bot.env`.

You need to set `{"forwards": [{"from": "channel1", "to": "channel2"}], "debounce_time_ms": 1000}` in the `.env/forward.json`,
where the list of forwards can contain multiple entries (the bot **should** have access both to the sending and receiving channels),
and the field `debounce_time_ms` is optional, defaulting to `1000`.

NOTE: The bot does **not** forward its own messages; for that reason transitivity does **not** work, i.e., `{"forwards": [{"from": "A", "to": "B"}, {"from": "B", "to": "C"}]}` will not forward from `A` to `C`.
If you want to be able to forward from `A` to both `B` and `C` and also retain the ability to forward from `B` to `C`, you should use `{"forwards": [{"from": "A", "to": "B"}, {"from": "B", "to": "C"}, {"from": "A", "to": "C"}]}`.
