import numpy as np
import matplotlib.pyplot as plt


# %%
class piece_noisy_line:

    def __init__(self, gamma=0.01, noisy_level=None):
        self.gamma_range = np.linspace(-gamma, gamma, 30)
        self.noisy_level = 0.012 if not noisy_level else noisy_level

    def simulate(self, gamma_range, size=1000):
        y_gen = np.zeros(shape=(size,))
        for i in range(size):
            y_gen[i] = np.random.choice(gamma_range) + np.random.laplace(scale=self.noisy_level)
        return y_gen

    def up_simulate(self, size=100):
        gamma_range = self.gamma_range[self.gamma_range > 0]
        return self.simulate(gamma_range, size=size)

    def down_simulate(self, size=100):
        gamma_range = self.gamma_range[self.gamma_range < 0]
        return self.simulate(gamma_range, size=size)

    def flat_simulate(self, size=100):
        gamma_range = np.zeros_like(self.gamma_range)
        return self.simulate(gamma_range, size=size)


# %%
class piece_ou_process:

    def __init__(self):
        pass

    def simulate(self, y0, sigma, theta, mu, size=1000):
        y_gen = np.zeros(shape=(size + 1,))
        y_gen[0] = y0
        a = (1 - np.exp(-theta)) * mu
        b = np.exp(-theta)
        c = sigma * np.sqrt((1 - np.exp(- 2 * theta)) / (2 * theta))
        for i in range(size):
            y_gen[i + 1] = a + b * y_gen[i] + c * np.random.randn()
        return y_gen[1:]

    def up_high_simulate(self, y0, size=500):
        mu = y0 * 2
        return self.simulate(y0, sigma=60, theta=0.005, mu=mu, size=size)

    def up_slow_simulate(self, y0, size=500):
        mu = y0 * 1.3
        return self.simulate(y0, sigma=30, theta=0.01, mu=mu, size=size)

    def down_high_simulate(self, y0, size=500):
        mu = y0 / 2
        return self.simulate(y0, sigma=60, theta=0.005, mu=mu, size=size)

    def down_slow_simulate(self, y0, size=500):
        mu = y0 * 0.6
        return self.simulate(y0, sigma=30, theta=0.01, mu=mu, size=size)

    def flat_simulate(self, y0, size=500):
        flat_range = np.linspace(-0.1, 0.1, 30)
        mu = y0 * (1 + np.random.choice(flat_range))
        return self.simulate(y0, sigma=20, theta=0.02, mu=mu, size=size)


# %%
class markov_switch:

    def __init__(self,
                 up_switch=[0.1, 0.2, 0.7],
                 down_switch=[0.7, 0.2, 0.1],
                 flat_switch=[0.1, 0.8, 0.1],
                 gamma=0.01, noisy_level=None):
        self.up_switch = up_switch
        self.down_switch = down_switch
        self.flat_switch = flat_switch

        self.gamma_range = np.linspace(-gamma, gamma, 30)
        self.noisy_level = 0.012 if not noisy_level else noisy_level

        self.up_range = self.gamma_range[self.gamma_range > 0]
        self.down_range = self.gamma_range[self.gamma_range < 0]

    def random_return(self, state=0):
        if state == 0:
            r = np.random.choice(self.gamma_range) + np.random.laplace(scale=self.noisy_level)
        if state == -1:
            r = np.random.choice(self.down_range) + np.random.laplace(scale=self.noisy_level)
        if state == 1:
            r = np.random.choice(self.up_range) + np.random.laplace(scale=self.noisy_level)
        return r

    def markov_state_process(self, size=1000):
        states = [-1, 0, 1]
        y_gen = np.zeros(shape=(size + 1,))
        for i in range(size):
            current_state = y_gen[i]
            if current_state == 0:
                next_state = np.random.choice(states, p=self.flat_switch)
            if current_state == 1:
                next_state = np.random.choice(states, p=self.up_switch)
            if current_state == -1:
                next_state = np.random.choice(states, p=self.down_switch)
            y_gen[i + 1] = next_state
        return y_gen[1:]

    def simulate(self, size=1000):
        mk_states = self.markov_state_process(size)
        y_gen = np.zeros(shape=(size,))
        for i in range(size):
            y_gen[i] = self.random_return(mk_states[i])
        return mk_states, y_gen


# %%
if __name__ == '__main__':

    nl = piece_noisy_line()
    snl_up = nl.up_simulate(100)
    snl_down = nl.down_simulate(100)
    snl_flat = nl.flat_simulate(100)
    s = np.hstack([snl_up, snl_flat, snl_down])
    # s_sim = nl.flat_simulate(300)
    s_cum = (s + 1).cumprod()
    plt.vlines(100, s_cum.min(), s_cum.max(), 'r')
    plt.vlines(200, s_cum.min(), s_cum.max(), 'r')
    plt.plot(s_cum)
    plt.show()

    # plt.hist(s_sim, bins=50)
    # plt.hist(s, bins=50)
    # plt.show()
    # %%
    ou = piece_ou_process()
    sou_flat = ou.flat_simulate(2000, size=200)
    sou_up = ou.up_high_simulate(sou_flat[-1], size=300)
    sou_down = ou.down_slow_simulate(sou_up[-1], size=300)

    s = np.hstack([sou_flat, sou_up, sou_down])
    plt.vlines(200, s.min(), s.max(), 'r')
    plt.vlines(500, s.min(), s.max(), 'r')
    plt.plot(s)
    plt.show()

    # %%
    mk = markov_switch()
    mk.up_switch, mk.down_switch, mk.flat_switch = [0.005, 0.005, 0.99], [0.99, 0.005, 0.005], [0.005, 0.99, 0.005]
    mk_stat, mk_ret = mk.simulate()

    lines = []
    for ind, i in enumerate(mk_stat):
        if ind == 0:
            last_state = i
        cur_state = i
        if cur_state != last_state:
            lines.append(ind)
        last_state = i

    s_cum = (mk_ret + 1).cumprod()
    plt.vlines(lines, s_cum.max(), s_cum.min(), 'r')
    plt.plot(s_cum)
    plt.show()

    # %%
    ou = piece_ou_process()
    ou_lines = np.array([0] + lines + [1000])
    sizes = np.diff(ou_lines)
    stats = [mk_stat[i - 1] for i in lines + [1000]]

    flag = 0
    ss = []
    for stat, size in zip(stats, sizes):
        if flag == 0:
            y0 = 2500
            flag = 1
            ss.append(np.array([y0]))

        if stat == 0:
            s = ou.flat_simulate(y0=y0, size=size)

        if stat == 1:
            fl = np.random.choice([0, 1])
            if fl == 0:
                s = ou.up_high_simulate(y0=y0, size=size)
            if fl == 1:
                s = ou.up_slow_simulate(y0=y0, size=size)

        if stat == -1:
            fl = np.random.choice([0, 1])
            if fl == 0:
                s = ou.down_high_simulate(y0=y0, size=size)
            if fl == 1:
                s = ou.down_slow_simulate(y0=y0, size=size)

        y0 = s[-1]
        ss.append(s)
    ou_index = np.hstack(ss)
    ou_ret = np.diff(ou_index) / ou_index[:-1]
    # %%
    plt.vlines(lines, ou_index.max(), ou_index.min(), 'r')
    plt.plot(ou_index)
    plt.show()
