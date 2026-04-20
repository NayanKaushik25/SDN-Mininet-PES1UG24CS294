import pandas as pd
import matplotlib.pyplot as plt

csv_path = "/home/nayan-kaushik/sdn_project/pox/traffic_report.csv"

# Support both headered reports and older headerless rows.
df = pd.read_csv(csv_path)

if {"generated_at", "total_packets"}.issubset(df.columns):
    df = df[["generated_at", "total_packets"]].rename(
        columns={"generated_at": "time", "total_packets": "packets"}
    )
else:
    df = pd.read_csv(csv_path, header=None)
    df = df.iloc[:, [0, 3]].copy()
    df.columns = ["time", "packets"]

df["time"] = pd.to_numeric(df["time"], errors="coerce")
df["packets"] = pd.to_numeric(df["packets"], errors="coerce")
df = df.dropna(subset=["time", "packets"])

df = df.sort_values("time")

# Convert to relative time
df["time"] = df["time"] - df["time"].iloc[0]

# Compute packets per interval (difference)
df["packets_per_sec"] = df["packets"].diff()

df = df.dropna()

# Convert time to int seconds
df["time_sec"] = df["time"].astype(int)

plt.figure()
plt.plot(df["time_sec"], df["packets_per_sec"], marker='o')
plt.xlabel("Time (seconds)")
plt.ylabel("Packets per Second")
plt.title("Packets per Second (Actual)")
plt.grid()
plt.show()