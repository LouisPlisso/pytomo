#!/usr/bin/env python
"""
Module to plot the data and generate the PNG/PDF image file
"""

import sqlite3
import datetime
import sys
import os
import cdfplot_new
from optparse import OptionParser
from collections import defaultdict
from itertools import cycle
try:
    #from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
except ImportError:
    rcParams = None
    plt = None
    mpl = None

DNS_RESOLVERS = ['open', 'google', 'default']

BASE_COLORS = ['orange', 'green', 'blue', 'black', 'cyan',
               'magenta' , 'pink', 'red', 'violet']
COLORS = cycle(BASE_COLORS)

COLOR_DICT = {}
for res in DNS_RESOLVERS:
    COLOR_DICT[res] = COLORS.next()

INTERVAL = 2
UNITS = {
    'DownloadTime' : 'sec',
    'DownloadBytes' : 'bytes',
    'VideoDuration' : 'sec',
    'VideoLength' : 'bytes',
    'InitialData' : 'bytes',
    'InitialRate' : 'kbps',
    'BufferingDuration' : 'sec',
    'BufferDurationAtEnd' : 'sec',
    'MaxInstantThp' : 'kbps',
    'PlaybackDuration' : 'sec',
    'DownloadInterruptions' : '',
    'EncodingRate' : 'kbps',
    'PingMin' : 'msec',
    'PingAvg' : 'msec',
    'PingMax' : 'msec',
    'TimeTogetFirstByte' : 'sec',
    'StatusCode': 'HTTP Code',
    'ResolveTime': 'sec',
}

def plot_function(to_plot, db_file, image_file, cdf_data=None):
    "Function to plot data"
    old_rcParams = rcParams['text.usetex']
    fig = create_fig(os.path.basename(db_file))
    column_names = set()
    # finding the column names from the dict
    for key in to_plot.keys():
        column_names.add(key[0])
    for plot_nb, column_name in enumerate(to_plot, 1):
        line_styles = cycle(['-'])
        axes = fig.add_subplot(len(to_plot), 1, plot_nb)
        fig.subplots_adjust(hspace=0.4)
        args = []
        for resolver, (dates, column_data) in to_plot[column_name].items():
            try:
                axes.plot_date(dates, column_data,
                               linestyle=line_styles.next(),
                               markersize=2,
                               markeredgecolor=COLOR_DICT[resolver],
                               color=COLOR_DICT[resolver], label=resolver)
                if cdf_data:
                    args.append((resolver, cdf_data[column_name][resolver]))
            except ValueError:
                print ''.join(("No data in ", column_name))
        if args:
            cdf_fig = cdfplot_new.cdfplotdata(args, loc='best',
                              title=column_name,
                              xlabel=('%s in %s'
                              % (column_name, UNITS[column_name])))
            cdf_file = os.path.join(os.path.dirname(image_file),
                                   '_'.join(('cdf', column_name.lower(),
                                   os.path.basename(image_file))))
            cdf_fig.savefig(cdf_file)
            print 'cdf of %s saved to %s' % (column_name, cdf_file)
        axes.legend()
        date_fmt = mpl.dates.DateFormatter('%Hh%M')
        axes.xaxis.set_major_formatter(date_fmt)
        axes.autoscale_view()
        try:
            for label in axes.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
        except ValueError:
            print ' '.join(('Column', column_name, 'is empty.'))
        axes.set_ylabel(''.join((column_name, '(', UNITS[column_name],')')))
        axes.grid(True)
    # force non-use of tex
    rcParams['text.usetex'] = False
    fig.savefig(image_file)
    # restore rcParams
    rcParams['text.usetex'] = old_rcParams

#    if not num % 5 :
#        pdf.savefig()
#        fig.suptitle('Pytomo: Youtube Download Statistics \n
#                     Database : %s'
#                     % os.path.basename(db_file), color='brown',
#                     size=16)
#        fig = plt.figure(figsize=(10, 20))
#        fig.suptitle('Pytomo: Youtube Download Statistics',
#                     color='brown', size=16)
#        pdf.close()
#        ##    config_pytomo.LOG.info('The plot has been updated')

def create_fig(db_name):
    "Return the figure"
    #pdf = PdfPages(image_file)
    fig = plt.figure(figsize=(10, 20))
    title = '\n'.join(('Pytomo: Youtube Download Statistics:',
                       'Database Name = %s' % db_name,
                       'Date %s ' % db_name.split('.')[1] +
                       'Start Time : %s' % (db_name.split('.')[2]
                                            .replace('_', ':'))))
    fig.suptitle(title, color='brown', size=16)
    #graph_num = cycle([1, 2, 3, 4, 5])
    return fig

def plot_data(column_names, image_file, db_file=None, cdf=False):
    """Function to plot the data in the database. Creates sub plots for
     the column names.
    """
    if not db_file:
        from . import config_pytomo
        db_file = config_pytomo.DATABASE_TIMESTAMP
    conn = sqlite3.connect(str(db_file),
                           detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()
    user_table = cur.execute('select name from sqlite_master '
                             'where type = "table"').fetchall()[0][0]
    to_plot = defaultdict(dict)
    cdf_data = defaultdict(dict)
    #find the number of resolvers used.
    for column_name in list(column_names):
        for resolver in DNS_RESOLVERS:
            dates = []
            if column_name == 'AvgThp':
                cmd = ' '.join(("select strftime('%Y-%m-%d %H:%M:%S', ID),",
                                "8*DownloadBytes/DownloadTime/1000",
                                "from",
                                user_table,
                                "where Resolver LIKE",
                                ''.join(("'%", resolver, "%'")),
                                "AND DownloadBytes != '' ",
                                "group by strftime('%Y%m%d%H%M',ID)"
                               ))
                cdf_cmd = ' '.join(("select 8*DownloadBytes/DownloadTime/1000",
                                    "from", user_table,
                                    "where Resolver LIKE",
                                    ''.join(("'%", resolver, "%'")),
                                    "AND DownloadBytes != '' "
                                   ))
            else:
                cmd = ' '.join(("select strftime('%Y-%m-%d %H:%M:%S', ID),",
                                "AVG(", column_name, ")",
                                "from",
                                user_table,
                                "where Resolver LIKE",
                                ''.join(("'%", resolver, "%'")),
                                "AND",
                                column_name,
                                "!= ''",
                                "group by strftime('%Y%m%d%H%M',ID)"
                               ))
                cdf_cmd = ' '.join(("select ", column_name,
                                "from", user_table,
                                "where Resolver LIKE",
                                ''.join(("'%", resolver, "%'")),
                                "AND", column_name, "!= ''"
                               ))
            cmd += "/" + str(INTERVAL) + ";"
            cur.execute(cmd)
            column_data = cur.fetchall()
            try:
                times_u, column_data = zip(*column_data)
            except ValueError:
                continue
            for _ in times_u:
                dates.append(datetime.datetime.strptime(_,
                                                        '%Y-%m-%d %H:%M:%S'))
            to_plot[column_name][resolver] = (dates, column_data)
            if cdf:
                cur.execute(cdf_cmd)
                cdf_data[column_name][resolver] = cur.fetchall()
    plot_function(to_plot, db_file, image_file, cdf_data)

def create_options(parser):
    "Add the different options to parser"
    parser.add_option("-w", "--image_file", dest = "image_file",
                      default = "pytomo_graph.pdf",
                      help = "File to store output graphs (png or pdf)")
    parser.add_option("-T", "--DownloadTime", dest = "column_names",
                      action = 'append_const', default = None,
                      const = 'DownloadTime',
                      help = "Plot DownloadTime")
    parser.add_option("-V", "--VideoDuration", dest = "column_names",
                      const = 'VideoDuration',
                      action = 'append_const', default = None,
                      help = "Plot VideoDuration")
    parser.add_option("-L", "--VideoLength", dest = "column_names",
                      const = 'VideoLength',
                      action = 'append_const', default = None,
                      help = "Plot VideoLength")
    parser.add_option("-E", "--EncodingRate", dest = "column_names",
                      const = 'EncodingRate',
                      action = 'append_const', default = None,
                      help = "Plot EncodingRate")
    parser.add_option("-B", "--DownloadBytes", dest = "column_names",
                      const = 'DownloadBytes',
                      action = 'append_const', default = None,
                      help = "Plot DownloadBytes")
    parser.add_option("-U", "--InitialData", dest = "column_names",
                      const = 'InitialData',
                      action = 'append_const', default = None,
                      help = "Plot Data downloaded in first buffer period")
    parser.add_option("-g", "--InitialRate", dest = "column_names",
                      const = 'InitialRate',
                      action = 'append_const', default = None,
                      help = "Plot Data downloaded in first buffer period")
    parser.add_option("-I", "--DownloadInterruptions",
                      const = 'DownloadInterruptions',
                      dest = "column_names",
                      action = 'append_const', default = None,
                      help = "Plot DownloadInterruptions")
    parser.add_option("-F", "--BufferingDuration",
                      const = 'BufferingDuration',
                      action = 'append_const', default = None,
                      dest = "column_names",
                      help = "Plot BufferingDuration")
    parser.add_option("-P", "--PlaybackDuration",
                      const = 'PlaybackDuration',
                      action = 'append_const', default = None,
                      dest = "column_names",
                      help = "Plot PlaybackDuration")
    parser.add_option("-A", "--BufferDurationAtEnd",
                      dest = "column_names",
                      const = 'BufferDurationAtEnd',
                      action = 'append_const', default = None,
                      help = "Plot BufferDurationAtEnd")
    parser.add_option("-M", "--MaxInstantThp",
                      dest = "column_names",
                      const = 'MaxInstantThp',
                      action = 'append_const', default = None,
                      help = "Plot MaxInstantThp")
    parser.add_option("-m", "--PingMin",
                      dest = "column_names",
                      const = 'PingMin',
                      action = 'append_const', default = None,
                      help = "Plot PingMin")
    parser.add_option("-a", "--PingAvg",
                      dest = "column_names",
                      const = 'PingAvg',
                      action = 'append_const', default = None,
                      help = "Plot PingAvg")
    parser.add_option("-x", "--PingMax",
                      dest = "column_names",
                      const = 'PingMax',
                      action = 'append_const', default = None,
                      help = "Plot PingMax")
    parser.add_option('-c', '--cdf',
                      dest = 'cdf',
                      action = 'store_true', default = False,
                      help = 'Plot CDF of the choosen indcators')
    parser.add_option('-v', '--verbose',
                      dest = 'verbose',
                      action = 'store_true', default = False,
                      help = 'verbose')

def main(argv=None):
    "Program wrapper"
    if argv is None:
        argv = sys.argv[1:]
    usage = ("%prog [-w image_file] [-T DownloadTime] "
            "[-V VideoDuration] [-L VideoLength]"
            " [-E EncodingRate] [-B DownloadBytes]"
            " [-I DownloadInterruptions]"
            " [-F BufferingDuration] [-P PlaybackDuration]"
            " [-A BufferDurationAtEnd] [-g InitialRate]"
            " [-M MaxInstantThp]" "[-U] InitialData"
            " [-m PingMin] [-a PingAvg] [-x PingMax]"
            " [-c] database"
            )
    parser = OptionParser(usage=usage)
    create_options(parser)
    (options, args) = parser.parse_args(argv)
    if len(args) < 1:
        print "Incorrect number of arguments"
        print "Must provide at least one database"
    if not options.column_names:
        print("Need to select atleast one column")
        return(1)
    if not options.image_file.endswith('.pdf'):
        print("Can only generate pdf files. Check the file extention")
        return(1)
    for db_nb, database in enumerate(args):
        out_file = os.path.join(os.path.dirname(options.image_file),
                                '_'.join((str(db_nb),
                                os.path.basename(options.image_file))))
        plot_data(options.column_names, out_file, db_file=database,
                 cdf=options.cdf)
        print ' '.join(("The plot for", str(options.column_names),
                        "from the database", database,
                        "has been saved to", out_file))

if __name__ == '__main__':
    sys.exit(main())

