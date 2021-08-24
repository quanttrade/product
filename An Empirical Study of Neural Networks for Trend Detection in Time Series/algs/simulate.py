import numpy as np


# %%
class piece_noisy_line:

    def __init__(self, piece=2, noisy_level=1):
        self.piece = piece

    def simulate(self, y0, mu=0, noisy_level=1, size=1000):
        y_gen = np.zeros(shape=(size,))
        for i in range(size):
            y_gen[i] = y0 + mu * i + noisy_level * np.random.randn()
        return y_gen


class piece_ou_process:

    def __init__(self, theta=1, mu=0, sigma=1):
        self.theta = theta
        self.mu = mu
        self.sigma = sigma

    def simulate(self, y0, size=1000):
        y_gen = np.zeros(shape=(size + 1,))
        y_gen[0] = y0
        a = (1 - np.exp(-self.theta)) * self.mu
        b = np.exp(-self.theta)
        c = self.sigma * np.sqrt((1 - np.exp(- 2 * self.theta)) / (2 * self.theta))
        for i in range(size):
            y_gen[i + 1] = a + b * y_gen[i] + c * np.random.randn()
        return y_gen[1:]


class switch_markovian:

    def __init__(self, r=0.001, sigma=1):
        self.r = r
        self.sigma = sigma

    def simulate(self, y0, size=1000, l=1):
        noisy = np.random.randn(size)
        y_gen = np.zeros(shape=(size,))
        for i in range(size):
            y_gen[i] = y0 * np.exp(self.r * l * i + self.sigma * noisy[i])
        return y_gen




# %%
import matplotlib.pyplot as plt

nl = piece_noisy_line()
s_flat = nl.simulate(0)
s_up = nl.simulate(-2, mu=0.004, noisy_level=0.5)
plt.plot(s_flat)
plt.plot(s_up)
plt.show()
# %%

ou = piece_ou_process(mu=1, theta=0.001, sigma=0.1)
s_ou = ou.simulate(0)
plt.plot(s_ou)
plt.show()

# %%

mk = switch_markovian(r=0.001, sigma=1)
s_mk = mk.simulate(1)
plt.plot(s_mk)
plt.show()
