import matplotlib.pyplot as plt
import numpy as np
import csv


def remove_outliers(arr):
    elements = np.array(arr)

    mean = np.mean(elements, axis=0)
    sd = np.std(elements, axis=0)

    final_list = [x for x in arr if (x > mean - 2 * sd)]
    final_list = [x for x in final_list if (x < mean + 2 * sd)]
    outliers = [x for x in arr if x not in final_list]
    print("  > removed the following outliers", outliers)
    return final_list


def plot_monitor_stats(file_names, scale_factors=[]):
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
    f_i = 0
    for f_name in file_names:
        for name in data[f_name].keys():
            scale_factor = 1 if len(scale_factors) != len(data) else scale_factors[f_i]
            print("### " + f_name + "." + name)
            mbps = [scale_factor * (b*8 / 1000000) for b in data[f_name][name]]
            mbps = remove_outliers(mbps)
            t = [i for i in range(1, len(mbps)+1)]
            plt.plot(t, mbps, value_style[i])
            plt.axis([0, max(t)+1, 0, 20])
            i += 1
            avg = np.mean(np.array(mbps))
            print("  > avg mbps " + str(avg))
        f_i += 1
    # configure axis labels and show plot
    plt.xlabel("time in seconds")
    plt.ylabel("data rate in mbits/s")
    plt.show()