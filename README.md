# Financial Fraud Analysis

## 📌 Project Overview

![Financial Fraud Analysis Dashboard](dashboard_screenshot.png)

This project focuses on identifying patterns and trends in fraudulent financial transactions. By leveraging **SQL, Power BI, and Excel**, we analyze a dataset of 10,000 transactions to uncover key insights related to fraud behavior, risk scores, geographical hotspots, and merchant categories. 

The goal of this analysis is to provide actionable intelligence that can help financial institutions mitigate risks and improve their fraud detection systems.

## 🛠️ Tools Used
- **SQL:** Used for querying, filtering, and aggregating the dataset to extract meaningful insights (e.g., finding the top fraud locations and analyzing high-value fraud transactions).
- **Power BI:** Used for building an interactive and dynamic dashboard (`dashboard.pbix`) to visualize fraud trends, making it easier for stakeholders to understand the data at a glance.
- **Excel:** Used for initial data inspection, cleaning, and managing the raw dataset (`financial_fraud_dataset_10000.csv`).

## 📊 Dataset Description
The dataset contains 10,000 transaction records with the following key attributes:
- `Transaction_ID` & `Customer_ID`
- `Amount` & `Transaction_Date`
- `Transaction_Type` (e.g., Deposit, Withdrawal, Transfer)
- `Payment_Method` (e.g., Credit Card, UPI, Net Banking)
- `Fraud_Status` (Legitimate vs. Fraud)
- `Risk_Score` (System-generated risk assessment)
- `City`, `Age_Group`, and `Bank_Name`

## 💡 Key SQL Queries & Analysis
The `fraud_analysis_queries.sql` file contains queries that answer critical business questions:
1. **Geographical Impact:** Which cities have the highest volume of fraudulent transactions?
2. **Payment Method Vulnerabilities:** What is the average risk score and total fraud amount associated with different payment methods?
3. **Targeted Merchants:** Which merchant categories (e.g., Travel, Electronics, Shopping) experience the highest fraud activity?
4. **High-Value Fraud:** Identifying large fraudulent transactions (Amount > 10,000) for immediate investigation.
5. **Demographic Trends:** Which age groups are most susceptible to financial fraud?

## 🚀 How to Run the Project
1. **SQL:** Run the scripts provided in `fraud_analysis_queries.sql` on your preferred SQL database management system (e.g., SQL Server, MySQL, PostgreSQL) after importing the CSV file.
2. **Power BI:** Open the `dashboard.pbix` file using Power BI Desktop to interact with the visualizations and explore the data.
