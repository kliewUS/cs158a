import glob
import os
import re

import numpy as np
import matplotlib.pyplot as plt

E1_DIR = 'e1'
BUFFER = '1'
DURATION = 60.0
TIMESTEP = 0.1
ERROR_BAR_EVERY = 2.0

timestep_regex = re.compile(r'^\d+\.\d+$')
cwnd_regex = re.compile(r'\bcwnd:(\d+)')
acked_regex = re.compile(r'\bbytes_acked:(\d+)')

"""
    Parse the sampler output file.
    Every sample contains a timestamp and ss output for the connections to rcv0.
    ss output contains cwnd: (packets) and rtt: (Smoothed RTT/variance in ms)
    BBR flows also show bbr:
    Currently only parses timestamp and cwnd for E1 
    as well as the iperf3's control connection to keep track of 
    the socket that has the largest bytes_acked.
"""
def parse_ss(path):
    times, cwnds = [], []
    # best = (bytes_acked, cwnd)
    ts, best = None, None
    
    with open(path) as file:
        for line in file:
            # If we parse a new timestamp, 
            # then append the current timestamp, the socket with the largest bytes_acked, and the cwnd window of said socket.
            if timestep_regex.match(line.strip()):
                if ts is not None and best is not None:
                    times.append(ts)
                    cwnds.append(best[1])

                ts, best = float(line), None

            elif 'cwnd:' in line:
                cwnd = int(cwnd_regex.search(line).group(1))
                match = acked_regex.search(line)
                
                if match:
                    acked = int(match.group(1))
                else:
                    acked = 0
                
                if best is None or acked > best[0]:
                    best = (acked, cwnd)

    # Append the final timestamp and cwnd to the times and cwnds lists.
    if ts is not None and best is not None:
        times.append(ts)
        cwnds.append(best[1])

    return np.array(times), np.array(cwnds, dtype=float)


"""
    Clips the trials results, so that we only get the results from t = 0 to 60 seconds.
    Set any cwnd values outside of this interval to NaN.
"""
def resample(t, cwnd, grid):
    index = np.searchsorted(t, grid, side='right') - 1
    out = cwnd[np.clip(index, 0, None)]
    out[index < 0] = np.nan
    out[grid > t[-1]] = np.nan
    return out

"""
    Plots cwnd(t) single flow for each algorithm.
    Retrieves the _ss.txt files for every algorithm (Reno, Cubic, BBR).
    Parses the timestamp. and the cwnd from the socket with the largest bytes_acked and puts them into separate lists.
    Clips the trial results between 0 and 60 seconds.
    Computes the mean +/- std over five trials and plot it for each algorithm.
"""
def plot_e1():
    grid = np.arange(0.0, DURATION + 1e-9, TIMESTEP)
    step = int(round(ERROR_BAR_EVERY / TIMESTEP))
    algorithms = [('reno', 'Reno', 'tab:blue'),
                  ('cubic', 'Cubic', 'tab:orange'),
                  ('bbr', 'BBR', 'tab:green')
                  ]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, (algorithm, label, color) in enumerate(algorithms):
        files = sorted(glob.glob(os.path.join(E1_DIR, '**', f'e1_b{BUFFER}_{algorithm}_t*_ss.txt'), recursive=True))

        traces = []
        for path in files:
            time, cwnd = parse_ss(path)
            traces.append(resample(time - time[0], cwnd, grid))

        # Vertically stack all of the trial results row wise, so that we can compute the mean and std.
        traces = np.vstack(traces)

        # Compute the mean +/- std over five trials, ignoring NaNs.
        mean = np.nanmean(traces, axis=0)
        std = np.nanstd(traces, axis=0, ddof=1)

        ax.plot(grid, mean, color=color, lw=1.2, label=f'{label} (n={len(files)})')
        
        # Setup error-bars for every algorithm.
        sel = slice(i * step // 3, None, step)
        ax.errorbar(grid[sel], mean[sel], yerr=std[sel], fmt='o', ms=4, color=color, elinewidth=1.2, capsize=3)

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Cwnd (packets)')
    ax.set_title(f"Experiment 1: Single Flow cwnd(t), mean +/- std over 5 trials (buffer = 1)")
    ax.set_xlim(0, DURATION)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(E1_DIR, f'e1_b{BUFFER}_cwnd_mean_std.png'), dpi=150)
    plt.show()

if __name__ == '__main__':
    plot_e1()