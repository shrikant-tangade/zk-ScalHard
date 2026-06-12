import matplotlib.pyplot as plt
import numpy as np

# Data points (Number of ECUs)
ecus = np.array([1, 25, 50, 75, 100])

# Uptane Data: Linear Growth O(n)
# Ms. Bansi's new data: 100 ECUs = 98,644 Bytes
# slope = 98644 / 100 = 986.44 Bytes per ECU
slope = 986.44
uptane_kb = (slope * ecus) / 1024  # Convert to KB for the graph

# zk-ScalHard Data: Constant O(1)
# Your experimental result: 809 Bytes
zk_scalhard_kb = np.full(ecus.shape, 809 / 1024)

# Create the figure
plt.figure(figsize=(8, 5.5))
plt.rcParams.update({'font.size': 12, 'font.family': 'serif'})

# Plotting the lines
plt.plot(ecus, uptane_kb, label='Legacy (Uptane VVM) - $O(n)$', 
         color='#d62728', marker='o', markersize=8, linestyle='--', linewidth=2)

plt.plot(ecus, zk_scalhard_kb, label='zk-ScalHard (Ours) - $O(1)$', 
         color='#1f77b4', marker='s', markersize=8, linestyle='-', linewidth=3)

# Shading the gap (The "Victory Area")
plt.fill_between(ecus, zk_scalhard_kb, uptane_kb, color='green', alpha=0.1)

# Axis Customization
plt.xlim(0, 105)
plt.ylim(0, 110) # Set max Y to 110 KB to show the 98.6KB peak clearly
plt.xticks([0, 25, 50, 75, 100])
plt.xlabel('Number of ECUs in Zonal SDV', fontweight='bold')
plt.ylabel('V2I Payload Size (KB)', fontweight='bold')
#plt.title('Asymptotic Communication Complexity: $O(n)$ vs. $O(1)$', fontsize=14, fontweight='bold')

# Grid and Legend
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', frameon=True, shadow=True)

# THE NEW KILL-SHOT ANNOTATION (99.2% Reduction)
# Math: 1 - (809 / 98644) = 0.99179...
plt.annotate('99.2% Bandwidth Reduction', xy=(100, 1), xytext=(45, 30),
             arrowprops=dict(facecolor='black', shrink=0.08, width=2, headwidth=10),
             fontsize=13, color='darkgreen', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="green", lw=2))

# Save as high-quality PDF for Overleaf
plt.tight_layout()
plt.savefig('bandwidth_scalability_v2.pdf')
print("Success: bandwidth_scalability_v2.pdf has been generated.")