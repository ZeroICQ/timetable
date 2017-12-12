from flask import Markup


def markup(get_field_html):
    def wrap(field, val=None, *args, **kwargs):
        params = {
            'val': val if val else '',
            'label': field.title,
            'name': field.qualified_col_name,
            'classes': 'edit-input'
        }

        # TODO: refactor
        html = get_field_html(field, val, params, *args, **kwargs)
        html = '<label>%(label)s</label>' + html
        html += '<div class="input-group input-group-sm server-state-container" style="{style}">' \
                '<span class="input-group-addon">База:</span>' \
                '<input type="text" class="form-control form-control-sm field-server-state" value="{value}" disabled data-res-col-name={res_name}>' \
                '</div>'.format(style=('display:none' if 'modified_value' not in kwargs else ''),
                                value=(str(kwargs['modified_value']) if 'modified_value' in kwargs else ''),
                                res_name=field.resolved_name)
        return Markup(html) % params
    return wrap


@markup
def string_field(field, val, params=None, **kwargs):
    return '<input name="%(name)s" class="form-control form-control-sm %(classes)s" type="text" value="%(val)s">'


@markup
def int_field(field, val, params=None, **kwargs):
    return '<input name="%(name)s" class="form-control form-control-sm %(classes)s" type="number" value="%(val)s">'


@markup
def fk_field(field, val, params=None, **kwargs):
    params['label'] = field.title
    choices = kwargs['choices']

    options = '<option {} value=\'None\'>None</option>'.format('selected' if val is None else '')
    for choice in choices:
        selected = 'selected' if val == choice[0] else ''

        options += ('<option {} value=\'{}\'>{}</option>'.format(selected, Markup.escape(choice[0]), Markup.escape(choice[1])))
    html = '<select name="%(name)s" class="form-control form-control-sm %(classes)s" type="number" value="%(val)s">{}</select>'.format(options)
    return html


@markup
def timestamp_field(field, val, params=None, **kwargs):
    return '<input name="%(name)s" class="form-control form-control-sm %(classes)s" type="datetime" value="%(val)s">'