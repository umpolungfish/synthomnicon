import matplotlib.pyplot as plt

data = [
    {'loss': '2.731', 'grad_norm': '1.504', 'learning_rate': '3.673e-05', 'epoch': '0.06215'},
    {'loss': '1.653', 'grad_norm': '1.508', 'learning_rate': '7.755e-05', 'epoch': '0.1243'},
    {'loss': '0.2362', 'grad_norm': '0.2204', 'learning_rate': '0.0001184', 'epoch': '0.1865'},
    {'loss': '0.002605', 'grad_norm': '0.00812', 'learning_rate': '0.0001592', 'epoch': '0.2486'},
    {'loss': '0.0001116', 'grad_norm': '0.01542', 'learning_rate': '0.0002', 'epoch': '0.3108'}
]

epochs = [float(d['epoch']) for d in data]
losses = [float(d['loss']) for d in data]
grad_norms = [float(d['grad_norm']) for d in data]
learning_rates = [float(d['learning_rate']) for d in data]

fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

axes[0].plot(epochs, losses, marker='o', linestyle='-', color='b')
axes[0].set_ylabel('Loss')
axes[0].set_yscale('log')  # log scale because loss drops dramatically
axes[0].grid(True)

axes[1].plot(epochs, grad_norms, marker='o', linestyle='-', color='r')
axes[1].set_ylabel('Gradient Norm')
axes[1].grid(True)

axes[2].plot(epochs, learning_rates, marker='o', linestyle='-', color='g')
axes[2].set_xlabel('Epoch')
axes[2].set_ylabel('Learning Rate')
axes[2].grid(True)

plt.suptitle('Training Metrics vs. Epoch')
plt.tight_layout()
plt.show()
