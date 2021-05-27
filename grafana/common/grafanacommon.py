# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Visualizer-specific GrafanaLib items

import os
import re
import string

import grafanalib.core as GCore

import attr
import attr.validators

import dsv.common.NodeFlag as dnf

COND_NOT_HIDDEN = '(bitAnd(flags, {}) = 0)'.format(dnf.NodeFlag.HIDDEN.value & dnf.NodeFlag.INACTIVE.value)
COND_NOT_HIDDEN_TEST = '(bitAnd(flags, {}) = 0)'.format(dnf.NodeFlag.HIDDEN_TEST.value & dnf.NodeFlag.INACTIVE.value)

NODE_SELECT_SQL = '( SELECT toUInt16(node_id) FROM dsv.node_text WHERE name IN ($Node) AND server_name IN ($Server) )'

NODE_SELECT_TEMPLATE_LIST = [
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Server',
        query = 'SELECT server_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' GROUP BY server_name',
        multi = True,
        includeAll = True,
        default = 'All'
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Region',
        query = 'SELECT region_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' AND server_name IN ($Server) GROUP BY region_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Country',
        query = 'SELECT country_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' AND server_name IN ($Server) AND region_name IN ($Region) GROUP BY country_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'City',
        query = 'SELECT city_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' AND server_name IN ($Server) AND region_name IN ($Region) AND country_name IN ($Country) GROUP BY city_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Instance',
        query = 'SELECT instance_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' AND server_name IN ($Server) AND region_name IN ($Region) AND country_name IN ($Country) AND city_name IN ($City) GROUP BY instance_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Node',
        query = 'SELECT name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN_TEST + ' AND server_name IN ($Server) AND region_name IN ($Region) AND country_name IN ($Country) AND city_name IN ($City) AND instance_name IN ($Instance) GROUP BY name',
        multi = True,
        includeAll = True
    )
]

NODE_SELECT_TEMPLATE = GCore.Templating(
    list = NODE_SELECT_TEMPLATE_LIST
)


INSTANCE_SELECT_SQL = '( SELECT toUInt16(node_id) FROM dsv.node_text WHERE instance_name IN ($Instance) AND server_name IN ($Server) AND region_name in ($Region) and country_name in ($Country) and city_name in ($City) )'

INSTANCE_SELECT_TEMPLATE_LIST = [
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Server',
        query = 'SELECT server_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN + ' GROUP BY server_name',
        multi = True,
        includeAll = True,
        default = 'All'
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Region',
        query = 'SELECT region_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN + ' AND server_name IN ($Server) GROUP BY region_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Country',
        query = 'SELECT country_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN + ' AND server_name IN ($Server) AND region_name IN ($Region) GROUP BY country_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'City',
        query = 'SELECT city_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN + ' AND server_name IN ($Server) AND country_name IN ($Country) GROUP BY city_name',
        multi = True,
        includeAll = True
    ),
    GCore.Template(
        dataSource = 'Visualizer',
        name = 'Instance',
        query = 'SELECT instance_name FROM dsv.node_text WHERE ' + COND_NOT_HIDDEN + ' AND server_name IN ($Server) AND city_name IN ($City) GROUP BY instance_name',
        multi = True,
        includeAll = True
    )
]

INSTANCE_SELECT_TEMPLATE = GCore.Templating(
    list = INSTANCE_SELECT_TEMPLATE_LIST
)

def DSVVersion():
    try:
        return os.environ['DSVVERSION']
    except KeyError:
        return '(no version)'

def HTMLPanel(filename, title='', transparent=False):
    version = DSVVersion()
    with open(filename) as f:
        text = string.Template(f.read())
    return GCore.Text(
        title = title,
        editable = False,
        mode = GCore.TEXT_MODE_HTML,
        content = text.substitute(version=version),
        transparent = transparent
    )

def MarkdownPanel(filename, title='', transparent=False):
    version = DSVVersion()
    with open(filename) as f:
        text = string.Template(f.read())
    return GCore.Text(
        title = title,
        editable = False,
        mode = GCore.TEXT_MODE_MARKDOWN,
        content = text.substitute(version=version),
        transparent = transparent
    )

FOOTER_TEXT = HTMLPanel('grafana/common/footer.html', transparent=True)
TEST_FOOTER_TEXT = HTMLPanel('grafana/common/footer_test.html', transparent=True)

FOOTER_ROW = GCore.Row(
    panels = [ FOOTER_TEXT ],
)
TEST_FOOTER_ROW = GCore.Row(
    panels = [ TEST_FOOTER_TEXT ],
)

@attr.s
class ClickHouseTarget(object):
    """Generate ClickHouse datasource target JSON structure

    :param database: ClickHouse database name
    :param query: ClickHouse data source query
    :param refId: target reference ID
    :param table: Table to query
    :param format: Target format
    :param intervalFactor: Resolution
    :param round: Rounding for $from and $to timestamps
    :param refId: Target reference - 'A', 'B' etc.
    :param table: Main database table to query
    """

    database = attr.ib(default='dsv')
    query = attr.ib(default='')
    refId = attr.ib(default='')
    table = attr.ib(default='')
    format = attr.ib(default=GCore.TIME_SERIES_TARGET_FORMAT)
    intervalFactor = attr.ib(default=1)
    interval = attr.ib(validator=attr.validators.instance_of(str), default='')
    dateColDataType = attr.ib(default='Date')
    dateLoading = attr.ib(validator=attr.validators.instance_of(bool), default=False)
    dateTimeColDataType = attr.ib(default='DateTime')
    dateTimeType = attr.ib(default='DATETIME')
    datetimeLoading = attr.ib(validator=attr.validators.instance_of(bool), default=False)
    round = attr.ib(default='60s')
    tableLoading = attr.ib(validator=attr.validators.instance_of(bool), default=False)

    def to_json_data(self):
        return {
            'database': self.database,
            'dateColDataType': self.dateColDataType,
            'dateLoading': self.dateLoading,
            'dateTimeColDataType': self.dateTimeColDataType,
            'dateTimeType': self.dateTimeType,
            'datetimeLoading': self.datetimeLoading,
            'format': self.format,
            'query': self.query,
            'intervalFactor': self.intervalFactor,
            'refId': self.refId,
            'round': self.round,
            'table': self.table,
            'tableLoading': self.tableLoading,
        }

def QPSGraph(**kwargs):
    if 'title' not in kwargs or 'targets' not in kwargs:
        raise TypeError("'title' and 'targets' parameters required")
    res = GCore.Graph(
        title = '',
        targets = [],
        lineWidth = 1,
        dataSource = 'Visualizer',
        nullPointMode = GCore.NULL_AS_ZERO,
        tooltip = GCore.Tooltip(
            sort = GCore.SORT_DESC,
            valueType = GCore.INDIVIDUAL
        ),
        yAxes = GCore.single_y_axis(
            format = GCore.SHORT_FORMAT,
            label = 'Queries per second'
        ),
    )
    return attr.evolve(res, **kwargs)

def QPMGraph(**kwargs):
    if 'title' not in kwargs or 'targets' not in kwargs:
        raise TypeError("'title' and 'targets' parameters required")
    res = GCore.Graph(
        title = '',
        targets = [],
        lineWidth = 1,
        dataSource = 'Visualizer',
        nullPointMode = GCore.NULL_AS_ZERO,
        tooltip = GCore.Tooltip(
            sort = GCore.SORT_DESC,
            valueType = GCore.INDIVIDUAL
        ),
        yAxes = GCore.single_y_axis(
            format = GCore.SHORT_FORMAT,
            label = 'Queries per minute'
        ),
    )
    return attr.evolve(res, **kwargs)

def RPSGraph(**kwargs):
    if 'title' not in kwargs or 'targets' not in kwargs:
        raise TypeError("'title' and 'targets' parameters required")
    res = GCore.Graph(
        title = '',
        targets = [],
        lineWidth = 1,
        dataSource = 'Visualizer',
        nullPointMode = GCore.NULL_AS_ZERO,
        tooltip = GCore.Tooltip(
            sort = GCore.SORT_DESC,
            valueType = GCore.INDIVIDUAL
        ),
        yAxes = GCore.single_y_axis(
            format = GCore.SHORT_FORMAT,
            label = 'Responses per second'
        ),
    )
    return attr.evolve(res, **kwargs)

@attr.s
class TimePicker(GCore.TimePicker):
    nowDelay = attr.ib()
    hidden = attr.ib(default=False, validator=attr.validators.instance_of(bool))

    def to_json_data(self):
        res = super().to_json_data()
        res['hidden'] = self.hidden
        res['nowDelay'] = self.nowDelay
        return res

def Dashboard(**kwargs):
    if 'title' not in kwargs or 'rows' not in kwargs:
        raise TypeError("'title' and 'rows' parameters required")
    res = GCore.Dashboard(
        title = '',
        rows = [],
        editable = False,
        time = GCore.Time('now-24h', 'now'),
        refresh = None,
    )
    return attr.evolve(res, **kwargs)

def NodeTemplateDashboard(**kwargs):
    return Dashboard(
        templating = NODE_SELECT_TEMPLATE,
        **kwargs
    )

def InstanceTemplateDashboard(**kwargs):
    return Dashboard(
        templating = INSTANCE_SELECT_TEMPLATE,
        time = GCore.Time('now-24h', 'now-1h'),
        **kwargs
    )

GRAPH_THRESHOLD_OK = 'ok'
GRAPH_THRESHOLD_WARNING = 'warning'
GRAPH_THRESHOLD_CRITICAL = 'critical'

GRAPH_THRESHOLD_OP_GT = 'gt'
GRAPH_THRESHOLD_OP_LT = 'lt'

GRAPH_THRESHOLD_YAXIS_LEFT = 'left'
GRAPH_THRESHOLD_YAXIS_RIGHT = 'right'

def choice_validator(choices):
    def validate(instance, attribute, value):
        if value not in choices:
            raise ValueError('{attr} should be one of {choice}'.format(
                attr=attribute, choice=choices))
    return validate

@attr.s
class GraphThreshold(object):
    """A chart threshold.

    :param colorMode: Colour scheme for threshold line, if any
    :param fill: Fill region
    :param line: Threshold line
    :param op: Operator
    :param value: Threshold value
    :param yaxis: Show on Y axis - Left, Right
    """

    colorMode = attr.ib(default=GRAPH_THRESHOLD_CRITICAL, validator=choice_validator((GRAPH_THRESHOLD_OK, GRAPH_THRESHOLD_WARNING, GRAPH_THRESHOLD_CRITICAL)))
    fill = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    line = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    op = attr.ib(default=GRAPH_THRESHOLD_OP_GT, validator=choice_validator((GRAPH_THRESHOLD_OP_GT, GRAPH_THRESHOLD_OP_LT)))
    value = attr.ib(default=0)
    yaxis = attr.ib(default=GRAPH_THRESHOLD_YAXIS_LEFT, validator=choice_validator((GRAPH_THRESHOLD_YAXIS_LEFT, GRAPH_THRESHOLD_YAXIS_RIGHT)))

    def to_json_data(self):
        return {
            'colorMode': self.colorMode,
            'fill': self.fill,
            'line': self.line,
            'op': self.op,
            'value': self.value,
            'yaxis': self.yaxis,
        }

@attr.s
class GraphWithThresholds(GCore.Graph):
    thresholds = attr.ib(default=None)

    def to_json_data(self):
        res = super().to_json_data()
        if self.thresholds:
            del res['grid']
            res['thresholds'] = self.thresholds
        return res

@attr.s
class XAxis(GCore.XAxis):

    def to_json_data(self):
        res = super().to_json_data()
        res['mode'] = self.mode
        res['name'] = self.name
        res['values'] = self.values
        return res

BAR_CHART_AXIS_RANGEMODE_AUTO = 'normal'
BAR_CHART_AXIS_RANGEMODE_BETWEEN = 'between'
BAR_CHART_AXIS_RANGEMODE_TOZERO = 'tozero'
BAR_CHART_AXIS_RANGEMODE_NONNEGATIVE = 'nonnegative'

BAR_CHART_AXIS_TYPE_AUTO = ''
BAR_CHART_AXIS_TYPE_LINEAR = 'linear'
BAR_CHART_AXIS_TYPE_LOG = 'log'
BAR_CHART_AXIS_TYPE_DATE = 'date'
BAR_CHART_AXIS_TYPE_CATEGORY = 'category'
BAR_CHART_AXIS_TYPE_MULTICATEGORY = 'multicategory'

@attr.s
class BarChartAxis:
    autotick = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    dtick = attr.ib(default=0)
    axrange = attr.ib(default=attr.Factory(list))
    rangemode = attr.ib(default=BAR_CHART_AXIS_RANGEMODE_AUTO, validator=choice_validator((BAR_CHART_AXIS_RANGEMODE_AUTO, BAR_CHART_AXIS_RANGEMODE_BETWEEN, BAR_CHART_AXIS_RANGEMODE_TOZERO, BAR_CHART_AXIS_RANGEMODE_NONNEGATIVE)))
    showgrid = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    tick0 = attr.ib(default=0)
    tickangle = attr.ib(default=0)
    tickmargin = attr.ib(default=0)
    title = attr.ib(default='')
    axtype = attr.ib(default=BAR_CHART_AXIS_TYPE_AUTO, validator=choice_validator((BAR_CHART_AXIS_TYPE_AUTO, BAR_CHART_AXIS_TYPE_LINEAR, BAR_CHART_AXIS_TYPE_LOG, BAR_CHART_AXIS_TYPE_DATE, BAR_CHART_AXIS_TYPE_CATEGORY, BAR_CHART_AXIS_TYPE_MULTICATEGORY)))
    zeroline = attr.ib(default=True, validator=attr.validators.instance_of(bool))

    def to_json_data(self):
        axisObject = {
            'autotick': self.autotick,
            'dtick': self.dtick,
            'rangemode': self.rangemode,
            'tick0': self.tick0,
            'tickangle': self.tickangle,
            'title': self.title,
            'type': self.axtype,
            'zeroline': self.zeroline,
        }
        if len(self.axrange) == 2:
            axisObject['range'] = self.axrange
        if self.tickmargin > 0:
            axisObject['tickmargin'] = self.tickmargin
        return axisObject

BAR_CHART_ORIENTATION_HORIZONTAL = 'h'
BAR_CHART_ORIENTATION_VERTICAL = 'v'

BAR_CHART_LEGEND_TRACEORDER_NORMAL = 'normal'
BAR_CHART_LEGEND_TRACEORDER_REVERSED = 'reversed'

@attr.s
class BarChartLegend:
    orientation = attr.ib(default=BAR_CHART_ORIENTATION_VERTICAL, validator=choice_validator((BAR_CHART_ORIENTATION_VERTICAL, BAR_CHART_ORIENTATION_HORIZONTAL)))
    traceorder = attr.ib(default=BAR_CHART_LEGEND_TRACEORDER_NORMAL, validator=choice_validator((BAR_CHART_LEGEND_TRACEORDER_NORMAL, BAR_CHART_LEGEND_TRACEORDER_REVERSED)))

    def to_json_data(self):
        return {
            'orientation': self.orientation,
            'traceorder': self.traceorder,
        }

BAR_CHART_LAYOUT_MODE_GROUP = 'group'
BAR_CHART_LAYOUT_MODE_STACK = 'stack'

BAR_CHART_LAYOUT_DRAGMODE_SELECT = 'select'
BAR_CHART_LAYOUT_DRAGMODE_ZOOM = 'zoom'
BAR_CHART_LAYOUT_DRAGMODE_PAN = 'pan'
BAR_CHART_LAYOUT_DRAGMODE_LASSO = 'lasso'

@attr.s
class BarChartLayout:
    barmode = attr.ib(default=BAR_CHART_LAYOUT_MODE_GROUP, validator=choice_validator((BAR_CHART_LAYOUT_MODE_GROUP, BAR_CHART_LAYOUT_MODE_STACK)))
    dragmode = attr.ib(default=BAR_CHART_LAYOUT_DRAGMODE_ZOOM, validator=choice_validator((BAR_CHART_LAYOUT_DRAGMODE_SELECT, BAR_CHART_LAYOUT_DRAGMODE_ZOOM, BAR_CHART_LAYOUT_DRAGMODE_PAN, BAR_CHART_LAYOUT_DRAGMODE_LASSO)))
    legend = attr.ib(
        default=attr.Factory(BarChartLegend),
        validator=attr.validators.instance_of(BarChartLegend)
    )
    showlegend = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    xaxis = attr.ib(
        default=attr.Factory(BarChartAxis),
        validator=attr.validators.instance_of(BarChartAxis)
    )
    yaxis = attr.ib(
        default=attr.Factory(BarChartAxis),
        validator=attr.validators.instance_of(BarChartAxis)
    )
    zaxis = attr.ib(
        default=attr.Factory(BarChartAxis),
        validator=attr.validators.instance_of(BarChartAxis)
    )

    def to_json_data(self):
        return {
            'barmode': self.barmode,
            'dragmode': self.dragmode,
            'legend': self.legend,
            'showlegend': self.showlegend,
            'xaxis': self.xaxis,
            'yaxis': self.yaxis,
            'zaxis': self.zaxis,
        }

@attr.s
class BarChartTrace:
    text = attr.ib()
    x = attr.ib()
    y = attr.ib()
    name = attr.ib(default=None)
    color = attr.ib(default=None)
    showlines = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    showmarkers = attr.ib(default=False, validator=attr.validators.instance_of(bool))

    def to_json_data(self):
        res = {
            'mapping': {
                'text': self.text,
                'x': self.x,
                'y': self.y,
            },
            'settings': {
                'barmarker': {
                }
            },
            'show': {
                'lines': self.showlines,
                'markers': self.showmarkers,
            },
        }
        if self.name:
            res['name'] = self.name
        if self.color:
            res['settings']['barmarker']['color'] = self.color
        return res

def ClickHouseTableTarget(**kwargs):
    res = ClickHouseTarget(
        format = GCore.TABLE_TARGET_FORMAT,
    )
    return attr.evolve(res, **kwargs)

BAR_CHART_TYPE = 'sinodun-natel-plotly-panel'

PLOTLY_CHART_TYPE_BAR = 'bar'
PLOTLY_CHART_TYPE_SCATTER = 'scatter'

@attr.s
class BarChart:
    """
    Generates a bar chart using (our modified) sinodun-natel-plotly-panel.

    :param dataSource: DataSource's name
    :param title: Panel title
    """

    title = attr.ib()
    targets = attr.ib(default=attr.Factory(list))
    dataSource = attr.ib(default='Visualizer')
    description = attr.ib(default=None)
    id = attr.ib(default=None)
    layout = attr.ib(
        default=attr.Factory(BarChartLayout),
        validator=attr.validators.instance_of(BarChartLayout)
    )
    autotrace = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    orientation = attr.ib(default=BAR_CHART_ORIENTATION_VERTICAL, validator=choice_validator((BAR_CHART_ORIENTATION_VERTICAL, BAR_CHART_ORIENTATION_HORIZONTAL)))
    plottype = attr.ib(default=PLOTLY_CHART_TYPE_BAR, validator=choice_validator((PLOTLY_CHART_TYPE_BAR, PLOTLY_CHART_TYPE_SCATTER)))
    span = attr.ib(default=None)
    traces = attr.ib(default=attr.Factory(list))
    timeFrom = attr.ib(default=None)
    timeShift = attr.ib(default=None)

    def to_json_data(self):
        return {
            'datasource': self.dataSource,
            'description': self.description,
            'id': self.id,
            'pconfig': {
                'layout': self.layout,
                'settings': {
                    'autotrace': self.autotrace,
                    'orientation': self.orientation,
                    'type': self.plottype,
                },
                'traces': self.traces,
            },
            'span': self.span,
            'targets': self.targets,
            'timeFrom': self.timeFrom,
            'timeShift': self.timeShift,
            'title': self.title,
            'type': BAR_CHART_TYPE,
        }

WORLDMAP_TYPE = 'grafana-worldmap-panel'

@attr.s
class WorldMap:
    """
    Generates a grafana-worldmap-panel.

    :param dataSource: DataSource's name
    :param title: Panel title
    """
    title = attr.ib()
    circleMaxSize = attr.ib(default=30)
    circleMinSize = attr.ib(default=2)
    datasource = attr.ib(default='Visualizer')
    initialZoom = attr.ib(default=2)
    locationData = attr.ib(default='countries')
    mapCenter = attr.ib(default='(0, 0)')
    mapCenterLatitude = attr.ib(default=0)
    mapCenterLongitude = attr.ib(default=0)
    showLegend = attr.ib(default=False)
    stickyLabels = attr.ib(default=False)
    thresholds = attr.ib(default='0')
    unitPlural = attr.ib(default='QPS')
    unitSingle = attr.ib(default='QPS')
    id = attr.ib(default=None)
    targets = attr.ib(default=attr.Factory(list))
    description = attr.ib(default=None)
    span = attr.ib(default=None)
    labelField = attr.ib(default=None)
    geohashField = attr.ib(default='geohash')
    latitudeField = attr.ib(default='latitude')
    longitudeField = attr.ib(default='longitude')
    metricField = attr.ib(default='metric')
    queryType = attr.ib(default='geohash')
    valueName = attr.ib(default='total')
    decimals = attr.ib(default=5)

    def to_json_data(self):
        return {
            'circleMaxSize': self.circleMaxSize,
            'circleMinSize': self.circleMinSize,
            'datasource': self.datasource,
            'initialZoom': self.initialZoom,
            'locationData': self.locationData,
            'mapCenter': self.mapCenter,
            'mapCenterLatitude': self.mapCenterLatitude,
            'mapCenterLongitude': self.mapCenterLongitude,
            'showLegend': self.showLegend,
            'stickyLabels': self.stickyLabels,
            'thresholds': self.thresholds,
            'title': self.title,
            'type': WORLDMAP_TYPE,
            'unitPlural': self.unitPlural,
            'unitSingle': self.unitSingle,
            'id': self.id,
            'targets': self.targets,
            'description': self.description,
            'span': self.span,
            'valueName': self.valueName,
            'decimals': self.decimals,
            'tableQueryOptions': {
                'labelField': self.labelField,
                'geohashField': self.geohashField,
                'latitudeField': self.latitudeField,
                'longitudeField': self.longitudeField,
                'metricField': self.metricField,
                'queryType': self.queryType,
            },
        }

# Dashboard tags.
DASH_MAIN_SITE = 'main'
DASH_TEST_SITE = 'test'
DASH_MONITORING = 'monitor'
DASH_PER_SEC_GRAPHS = 'graphs'
DASH_5MIN_GRAPHS = 'graphs 5min data'
DASH_OTHER_PLOTS = 'graphs'

@attr.s
class Dashlist:
    """
    Generates a dashlist panel.

    :param title: Panel title
    """

    title = attr.ib()
    description = attr.ib(default='')
    folderId = attr.ib(default=None)
    headings = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    id = attr.ib(default=None)
    limit = attr.ib(default=None)
    query = attr.ib(default='')
    recent = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    search = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    span = attr.ib(default=None)
    starred = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    tags = attr.ib(default=attr.Factory(list))

    def to_json_data(self):
        listObject = {
            'description': self.description,
            'folderId': self.folderId,
            'headings': self.headings,
            'id': self.id,
            'limit': self.limit,
            'query': self.query,
            'recent': self.recent,
            'search': self.search,
            'span': self.span,
            'starred': self.starred,
            'tags': self.tags,
            'title': self.title,
            'type': 'dashlist',
        }
        return listObject

FiveMinuteAggregationInfo = {
    'database': 'dsv_five_minute',
    'nodeinfo_database': 'dsv',
    'raw_database': 'dsv',
    'table_suffix': '',
    'graph_tag': DASH_5MIN_GRAPHS,
    'interval_divisor': '(300 * (1 + intDiv($interval - 1, 300)))',
    'round': 300,
    'period': 300,
    'description': '5 minutes',
}

def MakeTestAggDashboard(dash, uid, agginfo, **kwargs):
    res = dash(uid, agginfo, NODE_SELECT_SQL, **kwargs)
    res.rows.append(TEST_FOOTER_ROW)
    if 'tags' in kwargs:
        res.tags.extend(kwargs['tags'])
    else:
        res.tags.append(DASH_TEST_SITE)
    return attr.evolve(res, templating = NODE_SELECT_TEMPLATE)

def MakeAggDashboard(dash, uid, **kwargs):
    res = dash(uid, FiveMinuteAggregationInfo, INSTANCE_SELECT_SQL, **kwargs)
    res.rows.append(FOOTER_ROW)
    if 'tags' in kwargs:
        res.tags.extend(kwargs['tags'])
    else:
        res.tags.append(DASH_MAIN_SITE)
    return attr.evolve(res, templating = INSTANCE_SELECT_TEMPLATE)
