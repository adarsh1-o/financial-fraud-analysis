-- Financial Fraud Analysis SQL Queries

-- 1. Total Number of Fraudulent Transactions by City
SELECT 
    City, 
    COUNT(Transaction_ID) AS Total_Fraud_Cases
FROM 
    financial_fraud_dataset_10000
WHERE 
    Fraud_Status = 'Fraud'
GROUP BY 
    City
ORDER BY 
    Total_Fraud_Cases DESC;

-- 2. Average Risk Score and Total Amount by Payment Method for Fraudulent Transactions
SELECT 
    Payment_Method, 
    ROUND(AVG(Risk_Score), 2) AS Average_Risk_Score,
    ROUND(SUM(Amount), 2) AS Total_Fraud_Amount
FROM 
    financial_fraud_dataset_10000
WHERE 
    Fraud_Status = 'Fraud'
GROUP BY 
    Payment_Method
ORDER BY 
    Total_Fraud_Amount DESC;

-- 3. Top 5 Merchant Categories with the Highest Fraud Activity
SELECT TOP 5
    Merchant_Category, 
    COUNT(Transaction_ID) AS Fraudulent_Transactions
FROM 
    financial_fraud_dataset_10000
WHERE 
    Fraud_Status = 'Fraud'
GROUP BY 
    Merchant_Category
ORDER BY 
    Fraudulent_Transactions DESC;

-- 4. High-Value Fraudulent Transactions (Amount > 10,000)
SELECT 
    Transaction_ID, 
    Customer_ID, 
    Transaction_Date, 
    Amount, 
    Merchant_Category, 
    Risk_Score
FROM 
    financial_fraud_dataset_10000
WHERE 
    Fraud_Status = 'Fraud' AND Amount > 10000
ORDER BY 
    Amount DESC;

-- 5. Fraud Distribution by Age Group
SELECT 
    Age_Group, 
    COUNT(Transaction_ID) AS Total_Frauds,
    ROUND(SUM(Amount), 2) AS Total_Amount_Lost
FROM 
    financial_fraud_dataset_10000
WHERE 
    Fraud_Status = 'Fraud'
GROUP BY 
    Age_Group
ORDER BY 
    Total_Frauds DESC;
