# -*- coding: utf-8 -*-
"""
"""

import matplotlib
from matplotlib.dates import date2num
from obspy.clients.fdsn.header import FDSNNoDataException, DEFAULT_USER_AGENT, FDSNException

# We need to set the matplotlib backend to something that doesn't require a display
matplotlib.use("AGG")  # NOQA: E402

from io import BytesIO
from matplotlib import pyplot
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import URL_MAPPINGS
from obspy import UTCDateTime
from logging import getLogger
from distutils.util import strtobool

LOGGER = getLogger(__name__)

USER_AGENT = 'es-plotter/0.1 (+http://earthscope.org/plotter) %s' % DEFAULT_USER_AGENT

# The labels used by fedcatalog don't all match up with the names used by ObsPy
FEDCATALOG_TO_OBSPY_DC = {
    "GEOFON": "GFZ",
    "USPSC": "USP",
    "IRISDMC": "IRIS",
    "SED": "ETH",
    "UIB-NORSAR": "http://eida.geo.uib.no/",  # ObsPy doesn't have this so use the URL
}


def get_obspy_client_label(dc):
    """ Return the ObsPy client label for the given datacenter """
    obspy_label = FEDCATALOG_TO_OBSPY_DC.get(dc, dc)
    if obspy_label in URL_MAPPINGS:
        return obspy_label
    else:
        return None


class PlotParamException(Exception):
    """
    Indicates bad input parameters for plotting
    """
    pass


class PlotMissingParamException(PlotParamException):
    """
    Parameters are missing
    """
    pass


class NoDataFoundException(Exception):
    """
    Indicates that the service doesn't have the requested data
    """
    pass


class NoDataServiceException(Exception):
    """
    Indicates that the data center doesn't provide a dataselect service
    """
    pass


class Plot(object):
    """
    Encapsulates a single plot
    """

    # Very small plots can cause problems, mainly due to ObsPy trying to set fixed margins.
    # So if the height is below this threshold, we will render it larger and scale it down on output
    MIN_PLOT_HEIGHT = 150

    # Other base plotting values
    LINE_WIDTH = 0.3
    LINE_COLOR = '0.2'

    # Colors for phase arrival markers
    PHASE_COLORS = {
        "P": '#FF0000',
        "PP": '#FF9900',
        "PKP": '#FFCC00',
        "S": '#0000FF',
        "SS": '#00AAFF',
        "SKS": '#00CC66',
    }

    def __init__(self, st, start, end, width=500, height=200, frame=False, arrivals=None):
        self.start = UTCDateTime(start)
        self.end = UTCDateTime(end)
        self.width = int(width)
        self.height = int(height)
        self.frame = strtobool(str(frame))
        self.plot_dpi = 100

        # ObsPy hardcodes the margins in a way that breaks if the height is too small.
        # If that's going to happen, make the plot larger with thicker lines, and reduce the output resolution
        scale = 1.0
        if self.height < self.MIN_PLOT_HEIGHT:
            scale = (self.MIN_PLOT_HEIGHT / self.height)
        self.scale = scale

        plot_height = self.height * self.scale
        plot_width = self.width * self.scale
        linewidth = self.LINE_WIDTH * self.scale
        labelsize = 'small' if self.scale == 1 else 'medium'

        LOGGER.debug("Plotting with scale=%s (h=%s, w=%s, lw=%s)", self.scale, plot_height, plot_width, linewidth)

        # Use the rc_context to configure some matplotlib variables
        # This is only for things that ObsPy doesn't override, and that we can't cleanly change
        # after plotting
        rc = {
            'axes.formatter.limits': [-3, 3],
            'axes.formatter.use_mathtext': True,
            'axes.labelpad': 0,
            'axes.labelsize': labelsize,
            'axes.xmargin': 0,
            'axes.ymargin': 0,
            'ytick.major.pad': 1,
        }
        with matplotlib.rc_context(rc):
            # Plot and grab a handle to the figure; we will modify it before output
            self.figure = st.plot(
                size=(plot_width, plot_height),
                dpi=self.plot_dpi,
                linewidth=linewidth,
                color=self.LINE_COLOR,
                transparent=True,
                handle=True
            )

        self.clean_plot()
        if arrivals:
            self.add_arrivals(arrivals)

    def to_png(self, cleanup=True):
        """
        Generate a PNG image, and return it as a byte stream
        """
        output_dpi = self.plot_dpi / self.scale
        png = BytesIO()
        self.figure.savefig(png, format="png", dpi=output_dpi, transparent=True)
        if cleanup:
            self.cleanup()
        png.seek(0)
        return png

    def cleanup(self):
        """
        Release any held resources
        """
        pyplot.close(self.figure)

    def clean_plot(self):
        """
        Remove various bits of clutter from the generated figure
        """
        # Remove the title
        for c in self.figure.get_children():
            if isinstance(c, matplotlib.text.Text):
                c.set_visible(False)
        # Resize the frame
        if self.frame:
            left_padding = 60.0 / (self.width * self.scale)
            bottom_padding = 24.0 / (self.height * self.scale)
            self.figure.subplots_adjust(bottom=bottom_padding, left=left_padding, right=.99, top=.99)
        else:
            self.figure.subplots_adjust(bottom=0, left=0, right=1, top=1)
        # Adjust axes
        for ax in self.figure.axes:
            # Hide any text annotations attached to the axes (ObsPy adds the channel SNCL)
            for c in ax.get_children():
                if isinstance(c, matplotlib.text.Text):
                    try:
                        c.set_visible(False)
                    except Exception:
                        pass
            # Hide axes themselves if frame is turned off
            if not self.frame:
                ax.set_axis_off()
                ax.set_frame_on(False)
            else:
                # Add a y axis title, incorporating any common exponent label produced by Matplotlib
                yaxis_label = "Counts"
                try:
                    exponent_label = ax.get_yaxis().get_offset_text()
                    if exponent_label.get_text():
                        exponent_label.set_visible(False)
                        yaxis_label = "%s (%s)" % (yaxis_label, exponent_label.get_text())
                except Exception:
                    pass
                ax.set_ylabel(yaxis_label)

    def add_arrivals(self, arrivals):
        """
        Given a plot, add markers for the various arrival times
        """
        ax = self.figure.axes[0]
        for k, v in arrivals.items():
            try:
                phase = k.split('_')[0]
                color = self.PHASE_COLORS[phase.upper()]
                arrival_time = UTCDateTime(v)
                ax.axvline(
                    date2num(arrival_time.datetime),
                    linewidth=1.0 * self.scale,
                    color=color
                )
            except Exception as e:
                LOGGER.error("Couldn't add arrival {%s,%s}: %s", k, v, e)


from functools import wraps
import time
def retry(count=3, delay=1, exc_types=Exception):
    def decorator(func):
        @wraps(func)
        def result(*args, **kwargs):
            last_exc = None
            for _ in range(count):
                try:
                    return func(*args, **kwargs)
                except exc_types as e:
                    last_exc = e
                    pass
                LOGGER.info("Retrying")
                if delay:
                    time.sleep(delay)
            raise last_exc
        return result
    return decorator


@retry(exc_types=FDSNException)
def get_waveform_data(client, *plot_args):
    try:
        if "dataselect" not in client.services:
            raise NoDataServiceException("No data service provided by %s" % client.base_url)
        return client.get_waveforms(*plot_args)
    except FDSNNoDataException:
        raise NoDataFoundException()
    except FDSNException as e:
        # Some common errors have to be detected by looking at the error message (ugh)
        if 'authentication' in str(e).lower():
            raise NoDataFoundException()
        raise


@retry(exc_types=FDSNException)
def get_client(datacenter, on_behalf_of=None):
    client_label = get_obspy_client_label(datacenter)
    if not client_label:
        raise Exception("Unavailable datacenter: %s", datacenter)
    user_agent = USER_AGENT
    if on_behalf_of:
        user_agent = "%s on behalf of %s" % (user_agent, on_behalf_of)
    LOGGER.debug("User agent is %s", user_agent)
    return Client(client_label, user_agent=user_agent)


class Plotter(object):
    """
    Generates a plot for a given waveform, and returns it as a PNG file-like object.

    Currently this wraps around the ObsPy plotting engine, and alters the returned matplotlib Figure.
    This is relatively slow and fragile, but the plotting is complicated so it might be the best option.
    """

    def plot_from_query(self, **query):
        """
        Generate a single plot from a set of query parameters
        """
        plot_args = []
        try:
            for param in 'net sta loc cha'.split():
                plot_args.append(query[param])
            start = UTCDateTime(query['start'])
            end = UTCDateTime(query['end'])
            plot_args.extend((start, end,))
        except KeyError as e:
            raise PlotMissingParamException('Missing parameter: %s' % e)

        datacenter = query.get("dc", "IRISDMC")
        try:
            client = get_client(datacenter, on_behalf_of=query.get('on_behalf_of'))
        except Exception as e:
            LOGGER.warning(e)
            raise NoDataFoundException
        try:
            st = get_waveform_data(client, *plot_args)
        except NoDataServiceException as e:
            LOGGER.warning(e)
            raise NoDataFoundException
        except NoDataFoundException:
            raise
        except Exception as e:
            LOGGER.error("Failed to get data from %s", datacenter, exc_info=1)
            raise

        arrivals = {}
        for k, v in query.items():
            if k.endswith('_arrival'):
                phase = k.split('_')[0].upper()
                arrivals[phase] = UTCDateTime(v)

        plot_kwargs = {}
        for param in 'width height frame'.split():
            if param in query:
                plot_kwargs[param] = query[param]

        plot = Plot(st, start, end, arrivals=arrivals, **plot_kwargs)
        return plot.to_png()


if __name__ == '__main__':
    """
    Running this file directly will generate a test plot
    """
    print("Generating sample plot")
    plotter = Plotter()
    png = plotter.plot_from_query(
        net='IU',
        sta='ANMO',
        loc='00',
        cha='LHZ',
        start='2004-12-26T01:00:00',
        end='2004-12-26T07:00:00',
    )
    from tempfile import NamedTemporaryFile
    f = NamedTemporaryFile(suffix='.png', delete=False)
    f.write(png.getvalue())
    print("Plotted to %s" % f.name)
