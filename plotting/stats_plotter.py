import matplotlib.pyplot as plt
import csv


def plot_monitor_stats(file_names):
    """
    Plots StatsMonitor data stored in csv files denoted in file_names list.
    :param file_names: list of files to incorporate.
    :return:
    """
    # extract data
    data = {}
    for f_name in file_names:
        data[f_name] = {}
        with open(f_name, "r") as csvfile:
            data_reader = csv.reader(csvfile, delimiter=",")
            i = 0
            for row in data_reader:
                if i == 0:
                    if row[0] != "name" or row[1] != "bytes per second":
                        raise ValueError("incorrect csv format. 'name, bytes per second' expected.")
                else:
                    if row[0] not in data[f_name]:
                        data[f_name][row[0]] = []
                    data[f_name][row[0]].append(float(row[1]))
                i += 1
    # setup plot style
    plot_clr = ["r","g","b"]
    plot_style = ["o", "^", "--", "s"]
    value_style = []
    for s in plot_style:
        for c in plot_clr:
            value_style.append(c+s)
    # plot data
    i = 0
    for monitors in data.values():
        for name in monitors.keys():
            t = [i for i in range(1, len(monitors[name])+1)]
            mbps = [b*8 / 1000000 for b in monitors[name]]
            plt.plot(t, mbps, value_style[i])
            plt.axis([0, max(t)+1, 0, 50])
            i += 1
    # configure axis labels and show plot
    plt.xlabel("time in seconds")
    plt.ylabel("data rate in mbits/s")
    plt.show()