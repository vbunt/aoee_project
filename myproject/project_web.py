from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from math import ceil
import slow_search

app = Flask(__name__)
app.config['SECRET_KEY'] = 'avadakedavra'
form = ''
n_pages = 0
result = []
req = ''

class RequestForm(FlaskForm):
    request = StringField('', validators=[DataRequired()])
    submit = SubmitField('Найти!')


@app.route('/', methods=['GET', 'POST'])
def index():
    global form, result, n_pages, req
    form = RequestForm()
    if form.validate_on_submit():
        req = form.request.data
        request_items = req.split()
        result = slow_search.searcher(request_items)
        n_pages = ceil(result[1] / 20)
        ind = 0
        form.request.data = ''
        return render_template('result.html', req=req, form=form, result=result, n_pages=n_pages, ind=ind)
    else:
        req = None
        result = []
        return render_template('main.html', req=req, form=form, result=result)


@app.route('/result')
def pages():
    page_no = request.args.get('page')
    return render_template('result.html', req=req, form=form, result=result, n_pages=n_pages, ind=int(page_no)-1)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=False)
