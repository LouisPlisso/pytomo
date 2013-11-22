#!/usr/bin/env python
"Module to plot cdf from data or file. Can be called directly."

from __future__ import division, print_function

#from optparse import OptionParser
import sys
# AO 201221010 (due to error in win) =>
try:
    import numpy as np
except ImportError:
    np = None
# in case of non-interactive usage
#import matplotlib
#matplotlib.use('PDF')
try:
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.colors import colorConverter
except ImportError:
    plt = None
# <= AO 201221010 (due to error in win)
from itertools import cycle

_VERSION = '2.0'

# possibility to place legend outside graph:
#pylab.subfigure(111)
#pylab.subplots_adjust(right=0.8) or (top=0.8)
#pylab.legend(loc=(1.1, 0.5)

class CdfFigure(object):
    "Hold the figure and its default properties"
    def __init__(self, xlabel='x', ylabel=r'P(X$\leq$x)',
                 title='Empirical Distribution', fontsize='xx-large',
                 legend_fontsize='large', legend_ncol=1, subplot_top=None):
        self._figure = plt.figure()
        if subplot_top:
            self._figure.subplotpars.top = subplot_top
        self._axis = self._figure.add_subplot(111)
        self._lines = {}
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.fontsize = fontsize
        self.legend_fontsize = legend_fontsize
        self.legend_ncol = legend_ncol

    def savefig(self, *args, **kwargs):
        "Saves the figure: interface to plt.Figure.savefig"
        self._figure.savefig(*args, **kwargs)

    def bar(self, *args, **kwargs):
        "Plot in the axis: interface to plt.Axes.bar"
        self._axis.bar(*args, **kwargs)

    def plot(self, *args, **kwargs):
        "Plot in the axis: interface to plt.Axes.plot"
        self._axis.plot(*args, **kwargs)

    def get_xlim(self, *args, **kwargs):
        "Plot in the axis: interface to plt.Axes.get_xlim()"
        return self._axis.get_xlim(*args, **kwargs)

    def set_xlim(self, *args, **kwargs):
        "Plot in the axis: interface to plt.Axes.set_xlim()"
        self._axis.set_xlim(*args, **kwargs)

    def set_ylim(self, *args, **kwargs):
        "Plot in the axis: interface to plt.Axes.set_ylim()"
        self._axis.set_ylim(*args, **kwargs)

    def cdfplot(self, data_in, name='Data', finalize=False):
        """Plot the cdf of a data array
        Wrapper to call the plot method of axes
        """
        data = sorted(filter(lambda x: x is not None, data_in))
        data_len = len(data)
        if data_len == 0:
            print("no data to plot", file=sys.stderr)
            return
        cdf = np.arange(data_len + 1) / data_len
        # to have cdf up to 1
        data.append(data[-1])
        line = self._axis.plot(data, cdf, drawstyle='steps',
                              label=name + ': %d' % len(data))
        self._lines[name] = line[0]
        if finalize:
            self.adjust_plot()

    def ccdfplot(self, data_in, name='Data', finalize=False):
        """Plot the cdf of a data array
        Wrapper to call the plot method of axes
        """
        data = sorted(filter(lambda x: x is not None, data_in))
        data_len = len(data)
        if data_len == 0:
            print("no data to plot", file=sys.stderr)
            return
        ccdf = 1 - np.arange(data_len + 1) / data_len
        # to have cdf up to 1
        data.append(data[-1])
        line = self._axis.plot(data, ccdf, drawstyle='steps',
                              label=name + ': %d' % len(data))
        self._lines[name] = line[0]
        if finalize:
            self.adjust_plot()

    def show(self):
        "Show the figure, and hold to do interactive drawing"
        self._figure.show()
        self._figure.hold(True)

    @staticmethod
    def generate_line_properties():
        "Cycle through the lines properties"
        colors = cycle('mgcb')
        line_width = 2.5
        dashes = cycle([(1, 0), (8, 5)]) #self.dash_generator()
        linestyles = cycle(['-'])
        #alphas = cycle([.3, 1.])
        markers = cycle(' oxv*d')
        while True:
            dash = dashes.next()
            yield (colors.next(), line_width, dash, linestyles.next(),
                   markers.next())
            yield (colors.next(), line_width, dash, linestyles.next(),
                   markers.next())
            dash = dashes.next()
            yield (colors.next(), line_width, dash, linestyles.next(),
                   markers.next())
            yield (colors.next(), line_width, dash, linestyles.next(),
                   markers.next())

    def adjust_lines(self, dashes=True, leg_loc='best'):
        """Put correct styles in the axes lines
        Should be launch when all lines are plotted
        Optimised for up to 8 lines in the plot
        """
        generator = self.generate_line_properties()
        for key in sorted(self._lines):
            (color, line_width, dash, linestyle, marker) = generator.next()
            line = self._lines[key]
            line.set_color(color)
            line.set_lw(line_width)
            line.set_linestyle(linestyle)
            if dashes:
                line.set_dashes(dash)
            line.set_marker(marker)
            line.set_markersize(12)
            line.set_markeredgewidth(1.5)
            line.set_markerfacecolor('1.')
            line.set_markeredgecolor(color)
            # we want at most 15 markers per line
            markevery = 1 + len(line.get_xdata()) // 15
            line.set_markevery(markevery)
        self.adjust_plot(leg_loc=leg_loc)

    def adjust_plot(self, leg_loc='best'):
        "Adjust main plot properties (grid, ticks, legend)"
        self.put_labels()
        self.adjust_ticks()
        self._axis.grid(True)
        self._axis.legend(loc=leg_loc, ncol=self.legend_ncol)

    def put_labels(self):
        "Put labels for axes and title"
        self._axis.set_xlabel(self.xlabel, size=self.fontsize)
        self._axis.set_ylabel(self.ylabel, size=self.fontsize)
        self._axis.set_title(self.title, size=self.fontsize)

    def legend(self, loc='best'):
        "Plot legend with correct font size"
        font = FontProperties(size=self.legend_fontsize)
        self._axis.legend(loc=loc, prop=font)

    def adjust_ticks(self):
        """Adjusts ticks sizes
        To call after a rescale (log...)
        """
        self._axis.minorticks_on()
        for tick in self._axis.xaxis.get_major_ticks():
            tick.label1.set_fontsize(self.fontsize)
        for tick in self._axis.yaxis.get_major_ticks():
            tick.label1.set_fontsize(self.fontsize)

    def setgraph_logx(self):
        "Set graph in xlogscale and adjusts plot (grid, ticks, legend)"
        self._axis.semilogx(nonposy='clip', nonposx='clip')

    def setgraph_logy(self):
        "Set graph in xlogscale and adjusts plot (grid, ticks, legend)"
        self._axis.semilogy(nonposy='clip', nonposx='clip')

    def setgraph_loglog(self):
        "Set graph in xlogscale and adjusts plot (grid, ticks, legend)"
        self._axis.loglog(nonposy='clip', nonposx='clip')

    def cdfplotdata(self, list_data_name, **kwargs):
        "Method to be able to append data to the figure"
        cdfplotdata(list_data_name, figure=self, **kwargs)

    def ccdfplotdata(self, list_data_name, **kwargs):
        "Method to be able to append data to the figure"
        cdfplotdata(list_data_name, figure=self, cdf=True, **kwargs)

def cdfplotdata(list_data_name, figure=None, xlabel='x', loc='best',
                fs_legend='large', title = 'Empirical Distribution', logx=True,
                logy=False, cdf=True, dashes=True, legend_ncol=1):
    "Plot the cdf of a list of names and data arrays"
    if not figure:
        figure = CdfFigure(xlabel=xlabel, title=title,
                           legend_fontsize=fs_legend, legend_ncol=legend_ncol)
    else:
        figure.title = title
        figure.xlabel = xlabel
        figure.legend_fontsize = fs_legend
        figure.legend_ncol = legend_ncol
    if not list_data_name:
        print("no data to plot", file=sys.stderr)
        return figure
    for name, data in list_data_name:
        if cdf:
            figure.cdfplot(data, name=name)
        else:
            figure.ccdfplot(data, name=name)
    if logx and logy:
        figure.setgraph_loglog()
    elif logy:
        figure.setgraph_logy()
    elif logx:
        figure.setgraph_logx()
    figure.adjust_lines(dashes=dashes, leg_loc=loc)
    return figure

def cdfplot(in_file, col=0):
    "Plot the cdf of a column in file"
    data = np.loadtxt(in_file, usecols = [col])
    cdfplotdata(('Data', data))

def scatter_plot(data, title='Scatterplot', xlabel='X', ylabel='Y',
                 logx=False, logy=False):
    "Plot a scatter plot of data"
    figure = CdfFigure(title=title, xlabel=xlabel, ylabel=ylabel)
    x, y = zip(*data)
    figure.plot(x, y, linestyle='', marker='^', markersize=8,
             markeredgecolor='b', markerfacecolor='w')
    if logx and logy:
        figure.setgraph_loglog()
    elif logy:
        figure.setgraph_logy()
    elif logx:
        figure.setgraph_logx()
    figure.adjust_plot()
    return figure

def scatter_plot_multi(datas, title='Scatterplot', xlabel='X', ylabel='Y',
                 logx=False, logy=False):
    "Plot a scatter plot of dictionary"
    figure = CdfFigure(title=title, xlabel=xlabel, ylabel=ylabel)
    markers = cycle('^xo')
    colors = cycle('brm')
    transparent = colorConverter.to_rgba('w', alpha=1)
    total_nb = len([x for y in datas.values() for x in y])
    for label, data in sorted(datas.items()):
        x, y = zip(*data)
        figure.plot(x, y,
                    label=(r'%s: %d (\textbf{%d\%%})'
                           % (label, len(data), 100 *len(data) // total_nb)),
                    linestyle='', marker=markers.next(), markersize=8,
                    markeredgecolor=colors.next(), markerfacecolor=transparent)
    if logx and logy:
        figure.setgraph_loglog()
    elif logy:
        figure.setgraph_logy()
    elif logx:
        figure.setgraph_logx()
    figure.adjust_plot()
    return figure

def bin_plot(datas, title='Bin Plot', xlabel='X', ylabel='Y',
             logx=False, logy=False):
    "Plot a bin plot of dictionary"
    figure = CdfFigure(title=title, xlabel=xlabel, ylabel=ylabel)
#    linestyles = cycle(('-', '--'))
#    markers = cycle('^xo')
#    colors = cycle('brm')
#    for label, data in datas:
    left, width, height, yerr = zip(*datas)
    figure.bar(left, height, width, linewidth=0) #, yerr=yerr)
#                    linestyle=linestyles.next(), marker=markers.next(),
#                    markersize=6, markeredgecolor=colors.next(),
#                    markerfacecolor='w')
    if logx and logy:
        figure.setgraph_loglog()
    elif logy:
        figure.setgraph_logy()
    elif logx:
        figure.setgraph_logx()
    figure.adjust_plot()
    return figure

