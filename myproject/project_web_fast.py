from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from math import ceil
import fast_search
import sqlite3
# import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'avadakedavra'
form = ''
n_pages = 0
result = []
req = ''
l = 0
conn = sqlite3.connect('Harry_Potter80_filled.db', check_same_thread=False)

class RequestForm(FlaskForm):
    request = StringField('', validators=[DataRequired()])
    submit = SubmitField('Найти!')


@app.route('/', methods=['GET', 'POST'])
def index():
    global form, result, n_pages, req, l
    form = RequestForm()
    cur = conn.cursor()
    if form.validate_on_submit():
        req = form.request.data
        request_items = req.split()
        query = fast_search.compilator(request_items)
        cur.execute(query)
        result = cur.fetchall()
        l = len(result)
        n_pages = ceil(l / 20)
        ind = 0
        form.request.data = ''
        return render_template('result.html', req=req, form=form, result=result, n_pages=n_pages, ind=ind, l=l)
    else:
        req = None
        result = []
        return render_template('main.html', req=req, form=form, result=result)


@app.route('/result')
def pages():
    page_no = request.args.get('page')
    return render_template('result.html', req=req, form=form, result=result, n_pages=n_pages, ind=int(page_no)-1, l=l)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=False)
