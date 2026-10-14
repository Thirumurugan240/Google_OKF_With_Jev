---
type: table
name: orders
description: The orders database table, its columns and status values
owner: data-team
links: [monthly_revenue, refund_process]
---

# orders table

One row per customer order.

| Column | Type | Meaning |
|---|---|---|
| order_id | text | Unique order ID |
| customer_id | text | Who placed the order |
| amount | number | Order value in INR |
| status | text | completed, cancelled or refunded |
| created_at | timestamp | When the order was placed |

Notes:
- The old table `orders_old` is deprecated. Always use `orders`.
- Data refreshes every night at 2 AM IST.
