# teller

Command-line tool the tellers of one branch office use to look up a customer's account and record cash withdrawals. One SQLite file per branch, a handful of tellers at a time.

```
python -m src.cli lookup "Nguyen Van A"
python -m src.cli withdraw 42 500000
```
