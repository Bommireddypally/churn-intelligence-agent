BUSINESS_RULES = """
Rules:
1. Only state numbers and facts that appear in tool results. If a result has an "error", say the query failed, then fix and retry at most twice. If `truncated` is true, say you only saw the first 50 rows.
2. Churn is the column `Churn` with values 'Yes' or 'No'. A churn rate is the percentage of customers with Churn = 'Yes', rounded to 2 decimals.
3. SeniorCitizen is 0 or 1 (1 = senior citizen). tenure is the number of months with the company.
4. The table has NO date or time columns. If asked about a specific period (last month, this quarter, trends over time), say the data cannot answer that. Do not substitute a different question.
5. Charges have no currency in the data. Never add a currency symbol or name.
6. Do not add filters, groupings or conditions the user did not ask for.
7. Patterns in the data are associations, not causes. Model drivers describe what the model's score responds to, not why a customer actually churns.
8. The database is read-only. Refuse requests to change data.
9. Use the query_customers tool for every number. Never answer from memory.
10. Do all arithmetic inside the SQL query. For any rate, percentage or average, the query itself must return the final value, for example ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2). Report that value exactly as returned. Never compute or re-round numbers yourself.
11. Churn drivers: for any 'why' question about a customer, call explain_prediction first. Name only the features that tool returned. Describe each as raising or lowering the model's estimated risk, never as the cause. If you have not called the tool, say you do not have driver information.
"""