#!/usr/bin/env bash
# Seeds a repo whose commits span the last 6 days: one revert, src/cart.py reworked in 3 commits after its
# first, a ticket table with one ticket off by x3, and an agent decision (ticket 412) a later fix: commit changed.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval

commit() { # commit <days-ago> <subject>
  local when
  when="$(python3 -I -c "import datetime,sys; print((datetime.datetime.now()-datetime.timedelta(days=int(sys.argv[1]))).replace(microsecond=0).isoformat())" "$1")"
  git add -A
  GIT_AUTHOR_DATE="$when" GIT_COMMITTER_DATE="$when" git commit -qm "$2"
}

mkdir -p src docs/tickets/412
cat > src/cart.py <<'EOF'
from src.pricing import line_total


def total(items):
    return sum(line_total(i) for i in items)
EOF
cat > src/pricing.py <<'EOF'
from decimal import Decimal


def line_total(item):
    return Decimal(str(item["price"])) * item["qty"]
EOF
cat > docs/tickets/README.md <<'EOF'
# Tickets

| ticket | title | estimate | actual | note |
|--------|-------|----------|--------|------|
| 412 | Cart totals | 4h | 12h | float rounding surfaced late; two fix rounds |
| 413 | Promo codes | 6h | 6h | as planned |
| 414 | Order history | 2h | 3h | pagination dropped |
EOF
commit 6 "chore: scaffold cart service"

cat > docs/tickets/412/plan.md <<'EOF'
# Ticket 412 plan

## Steps
- Cart total sums line totals.
- Pricing helper computes one line.

## Auto decisions
- Money as float in pricing.py · why: fixtures use two-decimal prices only · revert: switch src/pricing.py back to Decimal
EOF
commit 5 "docs: ticket 412 plan"

cat >> src/cart.py <<'EOF'


def apply_promo(amount, code):
    return amount * 0.9 if code == "SAVE10" else amount
EOF
commit 5 "feat: apply promo codes in cart"

cat > src/pricing.py <<'EOF'
def line_total(item):
    return item["price"] * item["qty"]
EOF
commit 4 "feat: pricing uses float totals"

cat >> src/cart.py <<'EOF'


def rounded_total(items):
    return round(total(items), 2)
EOF
sed -i.bak 's/return item\["price"\] \* item\["qty"\]/return round(item["price"] * item["qty"], 2)/' src/pricing.py && rm src/pricing.py.bak
commit 3 "fix: cart total off by one cent"

cat >> src/cart.py <<'EOF'


def capped_discount(amount, discount):
    return min(discount, amount)
EOF
commit 2 "fix: cart discount cap"

cat > src/orders.py <<'EOF'
def history(orders, page=1, size=20):
    return orders[(page - 1) * size : page * size]
EOF
commit 2 "feat: paginate order history"

git rm -q src/orders.py
commit 1 "revert: paginate order history"
