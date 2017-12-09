from flask import Markup

def markup(get_field_html):
    def wrap(field, val=None, *args, **kwargs):
        params = {
            'val': val if val else '',
            'label': field.title,
            'name': field.qualified_col_name
        }

        html = get_field_html(field, val, params, *args, **kwargs)
        html = '<label>%(label)s</label>' + html
        return Markup(html) % params
    return wrap


@markup
def string_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="text" value="%(val)s">'


@markup
def int_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="number" value="%(val)s">'


@markup
def fk_field(field, val, params=None, **kwargs):
    params['label'] = field.title
    choices = kwargs['choices']

    options = ''
    for choice in choices:
        selected = 'selected' if val == choice[0] else ''
        options += ('<option {} value=\'{}\'>{}</option>'.format(selected, Markup.escape(choice[0]), Markup.escape(choice[1])))
    html = '<select name="%(name)s" class="form-control form-control-sm" type="number" value="%(val)s">{}</select>'.format(options)
    return html


@markup
def timestamp_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="datetime" value="%(val)s">'