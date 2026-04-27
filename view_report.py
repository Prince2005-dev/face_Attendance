import pandas as pd

file = input("Enter file path (logs/attendance_YYYY-MM-DD.csv): ")

df = pd.read_csv(file)

print("\n===== ATTENDANCE REPORT =====\n")
print(df)

print("\n===== SUMMARY =====\n")
print(df.groupby(["Subject", "Status"]).size())