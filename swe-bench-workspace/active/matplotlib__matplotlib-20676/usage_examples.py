
# Example Usage of FixedSpanSelector

from spanselector_event_fix import FixedSpanSelector
import matplotlib.pyplot as plt
import numpy as np

# Basic usage
fig, ax = plt.subplots()
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)

def on_select(xmin, xmax):
    print(f"Selected range: [{xmin:.2f}, {xmax:.2f}]")

# Create SpanSelector with fixed event handling
selector = FixedSpanSelector(
    ax, 
    onselect=on_select,
    direction='horizontal',  # or 'vertical'
    minspan=0.1,            # minimum selection span
    useblit=True,           # for better performance
    interactive=True,       # enable interactive mode
    rectprops={             # customize appearance
        'facecolor': 'blue',
        'alpha': 0.3
    }
)

plt.show()
