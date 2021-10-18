from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import sqlite3
import re
from natasha import (
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    Doc
)
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

conn = sqlite3.connect('C:/Users/anuta/myproject/Harry_Potter80_filled.db', check_same_thread=False)
cur = conn.cursor()


posser = ['NUM', 'X', 'ADJ', 'SYM', 'ADV', 'AUX', 'ADP', 'PROPN', 'NOUN',
          'SCONJ', 'CCONJ', 'DET', 'PRON', 'PART', 'VERB', 'INTJ']

exact_form_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id, texts.title, texts.source
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.word = ?''')

pos_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.pos = ?''')

word_pos_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.lemma = ? and tokens.pos = ?''')

lemma_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.lemma = ?''')

om_exact_form_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.word = ? and tokens.token_id == ? and sentences.sentence_id = ? ''')

om_pos_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.pos = ? and tokens.token_id == ? and sentences.sentence_id = ?''')

om_word_pos_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.lemma = ? and tokens.pos = ? and tokens.token_id == ? and sentences.sentence_id = ?''')

om_lemma_sql = ('''
    select tokens.word, tokens.token_id, sentences.sentence, sentences.sentence_id
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    where tokens.lemma = ? and tokens.token_id == ? and sentences.sentence_id = ?''')

text_sql = ('''
    select texts.source, texts.title
    from sentences
    join texts on texts.text_id = sentences.text_id
    where sentence = ?''')


def one_item(item):
    if '"' in item:
        exact_form = re.search('[а-яА-ЯёЁ]+', item)[0]
        cur.execute(exact_form_sql, [exact_form])
        data = cur.fetchall()

    elif item in posser:
        cur.execute(pos_sql, [item])
        data = cur.fetchall()

    elif '+' in item:
        word = re.search('[а-яА-ЯёЁ]+', item)[0]
        pos = re.search('[A-Z]+', item)[0]
        doc = Doc(word)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemma = token.lemma
            cur.execute(word_pos_sql, [lemma, pos])
        data = cur.fetchall()

    else:
        doc = Doc(item)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemma = token.lemma
            cur.execute(lemma_sql, [lemma])
        data = cur.fetchall()

    return data


def one_more_item(item, token_id, sentence_id):
    if '"' in item:
        exact_form = re.search('[а-яА-ЯёЁ]+', item)[0]
        cur.execute(om_exact_form_sql, [exact_form, (token_id + 1), sentence_id])
        data = cur.fetchall()

    elif item in posser:
        cur.execute(om_pos_sql, [item, (token_id + 1), sentence_id])
        data = cur.fetchall()

    elif '+' in item:
        word = re.search('[а-яА-ЯёЁ]+', item)[0]
        pos = re.search('[A-Z]+', item)[0]
        doc = Doc(word)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemma = token.lemma
            cur.execute(om_word_pos_sql, [lemma, pos, (token_id + 1), sentence_id])
        data = cur.fetchall()

    else:
        doc = Doc(item)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemma = token.lemma
            cur.execute(om_lemma_sql, [lemma, (token_id + 1), sentence_id])
        data = cur.fetchall()

    return data


def searcher(request_items):
    if len(request_items) == 1:
        issue = []
        for entry in one_item(request_items[0]):
            cur.execute(text_sql, [entry[2]])
            source = cur.fetchall()
            new = (entry[0], entry[2], source)
            issue.append(new)

    elif len(request_items) == 2:
        issue = []
        first = request_items[0]
        second = request_items[1]
        first_answ = one_item(first)
        for entry in first_answ:
            good_entry = one_more_item(second, entry[1], entry[3])
            if len(good_entry) != 0:
                cur.execute(text_sql, [good_entry[0][2]])
                source = cur.fetchall()
                new = (entry[0] + ' ' + good_entry[0][0], good_entry[0][2], source)
                issue.append(new)

    else:
        issue = []
        first = request_items[0]
        second = request_items[1]
        third = request_items[2]
        first_answ = one_item(first)
        for entry in first_answ:
            second_answ = []
            almost_good_entry = one_more_item(second, entry[1], entry[3])
            if len(almost_good_entry) != 0:
                second_answ.append(almost_good_entry)
                for ag_entry in second_answ:
                    good_entry = one_more_item(third, ag_entry[0][1], ag_entry[0][3])
                    if len(good_entry) != 0:
                        cur.execute(text_sql, [good_entry[0][2]])
                        source = cur.fetchall()
                        new = (entry[0] + ' ' + ag_entry[0][0] + ' ' + good_entry[0][0], good_entry[0][2], source)
                        issue.append(new)
    return issue, len(issue)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'avadakedavra'


class RequestForm(FlaskForm):
    request = StringField('', validators=[DataRequired()])
    submit = SubmitField('Найти!')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = RequestForm()
    if form.validate_on_submit():
        request = form.request.data
        request_items = re.split(' ', request)
        result = searcher(request_items)
        form.request.data = ''
        return render_template('result.html', request=request, form=form, result=result)
    else:
        request = None
        result = []
        return render_template('main.html', request=request, form=form, result=result)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=False)
