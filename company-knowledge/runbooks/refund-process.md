---
type: runbook
name: Refund Process
description: Step by step process for handling a customer refund request
owner: support-team
links: [orders]
---

# Refund Process

1. Check the order in the `orders` table using `order_id`.
2. Refunds are allowed only within 30 days of `created_at`.
3. Orders above 10,000 INR need approval from the finance team.
4. After the refund, set `status = 'refunded'` on the order.
5. Send the customer a confirmation email.

Refunds usually reach the customer in 5 to 7 working days.
