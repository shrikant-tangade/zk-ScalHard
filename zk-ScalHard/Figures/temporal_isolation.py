import matplotlib.pyplot as plt
import numpy as np

# Data in Milliseconds
# 24 hours = 86,400,000 ms
legacy_window = 86400000 
# zk-ScalHard: Witness Gen (357ms) + Prover (3885ms) approx 4.2 seconds
zk_window = 4242 

labels = ['Legacy (Persistent Key)', 'zk-ScalHard (Ephemeral Witness)']
values = [legacy_window, zk_window]

plt.figure(figsize=(7, 6))
plt.rcParams.update({'font.size': 11})

# Use a bar chart with Logarithmic scale
bars = plt.bar(labels, values, color=['#7f7f7f', '#2ca02c'], alpha=0.85, width=0.6)

# Log scale is critical here to show the magnitude difference
plt.yscale('log')

# Axis Labels and Title
plt.ylabel('Vulnerability Window (ms) - Log Scale', fontweight='bold')
#plt.title('Temporal Attack Surface: Persistent vs. Ephemeral Secrets', fontsize=13, fontweight='bold')

# Add gridlines for the Log scale
plt.grid(True, which="both", ls="-", alpha=0.2)

# Add value labels on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:,} ms', 
             va='bottom', ha='center', fontweight='bold', fontsize=10)

# Annotation for the "99.99% Reduction"
plt.annotate('99.995% Surface Reduction', 
             xy=(1, zk_window), xytext=(0.5, 100000),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
             fontsize=12, color='darkgreen', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="green", lw=1))

# Narrative Footnote (Optional for the plot, but good for the paper)
plt.figtext(0.5, 0.01, "Moving the Security Anchor from Flash (24/7) to a Temporal Window (ms).", 
            ha="center", fontsize=9, style='italic')

plt.tight_layout()
plt.savefig('temporal_isolation.pdf')
print("Success: temporal_isolation.pdf has been generated.")