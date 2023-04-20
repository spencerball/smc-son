import csv
import os
import pandas
from datetime import datetime
from dateutil import tz
import jinja2
import flask
import json
from son.utils.menu import url_link, get_menu_tree

blueprint = flask.Blueprint('filters', __name__)


@jinja2.pass_context
@blueprint.app_template_filter('format_date')
def format_date_filter(context, dt):
    if dt:
        dt = dt.replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz('Europe/London'))
        return datetime.strftime(dt, '%d/%m/%Y %H:%M')
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('url_link')
def url_link_filter(context, link):
    if link:
        return url_link(link)
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('menuitem_isactive')
def menuitem_isactive_filter(context, details):
    if details:
        itemname = details[0]
        selected = details[1]

        if url_link(itemname) == url_link(selected):
            return ' is-active'
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('menuitem_isopen')
def menuitem_isopen_filter(context, details):
    if details:
        menu = details[0]
        itemname = details[1]
        selected = details[2]
        tree = get_menu_tree(menu, selected)

        if itemname in tree:
            return ' is-open'
        return ''
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('content')
def content_filter(context, details):
    if details:
        content = details[0]
        field = details[1]
        for item in content:
            if isinstance(item[1], list):
                if item[0][0] == field:
                    return item[0][1]
                elif item[1][0] == field:
                    return item[1][1]
            else:
                if item[0] == field:
                    return item[1]
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('attribute')
def attribute_filter(context, details):
    if details:
        data = details[0]
        field = details[1]
        try:
            attributes = json.loads(data)
            if field in attributes:
                return attributes[field]
        except:
            pass
    return ''


@jinja2.pass_context
@blueprint.app_template_filter('read_csv')
def read_csv(context, csv_file_name):
    if csv_file_name:
        csv_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'static', 'data-for-drop-down-prototype', csv_file_name)
        return pandas.read_csv(csv_file_path)
    return ''
