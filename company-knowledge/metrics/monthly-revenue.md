---
type: metric
name: Monthly Revenue
description: How monthly revenue is calculated and which rules apply
owner: finance-team
links: [orders]
---

# Monthly Revenue

Monthly revenue is the sum of `amount` from the `orders` table
where `status = 'completed'`, grouped by the month of `created_at`.

Rules:
- Refunded orders are NOT counted.
- Cancelled orders are NOT counted.
- All amounts are in INR.
- Do NOT use the old table `orders_old`. It is deprecated since 2025.

Example SQL:

```sql
SELECT DATE_TRUNC('month', created_at) AS month,
       SUM(amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1;
```
