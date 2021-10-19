import re, sqlite3
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


poss = ['NUM', 'X', 'ADJ', 'SYM', 'ADV', 'AUX', 'ADP', 'PROPN', 'NOUN', 'SCONJ', 'CCONJ', 'DET', 'PRON', 'PART', 'VERB', 'INTJ']


first_part_2 = '''
    select first||' '||second, sentence, title, source 
    from
    (select texts.title, b.sentence, texts.source, t.word as first, 
        (select s.word from tokens s 
        join main on s.token_id = main.token_id
        join sentences p on p.sentence_id = main.sentence_id
        where s.token_id = t.token_id + 1 
        and s'''

second_part_2 = ''' and b.sentence_id = p.sentence_id) second
    from 
    tokens t
    join main on t.token_id = main.token_id
    join sentences b on b.sentence_id = main.sentence_id
    join texts on b.text_id = texts.text_id
    where t'''

third_part_2 = ''')
    where not (second is null)'''

first_part_3 = '''
    select first||' '||second||' '||third, sentence, title, source 
    from
    (select texts.title, b.sentence, texts.source, t.word as first,
        (select s.word
        from tokens s
        join main on s.token_id = main.token_id
        join sentences p on p.sentence_id = main.sentence_id
        where s.token_id = t.token_id + 1
        and s'''

second_part_3 = ''' and b.sentence_id = p.sentence_id) second,
        (select s.word from tokens s
        join main on s.token_id = main.token_id
        join sentences p on p.sentence_id = main.sentence_id
        where s.token_id = t.token_id + 2
        and s'''

third_part_3 = ''' and b.sentence_id = p.sentence_id) third
    from 
    tokens t
    join main on t.token_id = main.token_id
    join sentences b on b.sentence_id = main.sentence_id
    join texts on b.text_id = texts.text_id
    where t'''

fourth_part_3 = ''')
    where not (second is null or third is null)'''

exact_form_sql = ('''
    select tokens.word, sentences.sentence, texts.title, texts.source
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    join texts on sentences.text_id = texts.text_id
    where tokens.word = {word}''')

pos_sql = ('''
    select tokens.word, sentences.sentence, texts.title, texts.source
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    join texts on sentences.text_id = texts.text_id
    where tokens.pos = {pos}''')

word_pos_sql = ('''
    select tokens.word, sentences.sentence, texts.title, texts.source
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    join texts on sentences.text_id = texts.text_id
    where tokens.lemma = {lemma} and tokens.pos = {pos}''')

lemma_sql = ('''
    select tokens.word, sentences.sentence, texts.title, texts.source
    from main
    join tokens on tokens.token_id = main.token_id
    join sentences on sentences.sentence_id = main.sentence_id
    join texts on sentences.text_id = texts.text_id
    where tokens.lemma = {lemma}''')


def one_item(item):
    if '+' in item:
        word = re.search('[а-яА-ЯёЁ]+', item)[0].lower()
        pos = '"' + re.search('[A-Z]+', item)[0] + '"'
        doc = Doc(word)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        token = doc.tokens[0]
        token.lemmatize(morph_vocab)
        lemma = '"' + token.lemma + '"'
        return word_pos_sql.format(lemma=lemma, pos=pos)

    elif item in poss:
        pos = '"' + item + '"'
        return pos_sql.format(pos=pos)

    elif '"' in item:
        exact_form = '"' + re.search('[а-яА-ЯёЁ]+', item)[0].lower() + '"'
        return exact_form_sql.format(word=exact_form)

    else:
        doc = Doc(item)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)

        token = doc.tokens[0]
        token.lemmatize(morph_vocab)
        lemma = '"' + token.lemma + '"'
        return lemma_sql.format(lemma=lemma)


def for_item_maker(item, num):
    for_item = ''
    if '"' in item:
        exact_form = re.search('[а-яА-ЯёЁ]+', item)[0].lower()
        for_item = '.word = "' + exact_form + '"'

    elif item in poss:
        for_item = '.pos = "' + item + '"'

    elif '+' in item:
        word = re.search('[а-яА-ЯёЁ]+', item)[0].lower()
        pos = re.search('[A-Z]+', item)[0]
        doc = Doc(word)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        token = doc.tokens[0]
        token.lemmatize(morph_vocab)
        lemma = token.lemma
        if num == 0:
            for_item = '.lemma = "' + lemma + '" and t.pos = "' + pos + '"'
        else:
            for_item = '.lemma = "' + lemma + '" and s.pos = "' + pos + '"'

    else:
        doc = Doc(item)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemma = token.lemma
            for_item = '.lemma = "' + lemma + '"'
    return for_item


def compilator(request_items):
    for_items = []

    if len(request_items) == 1:
        query = one_item(request_items[0])


    elif len(request_items) == 2:
        for num, item in enumerate(request_items):
            for_item = for_item_maker(item, num)
            for_items.append(for_item)
        query = first_part_2 + for_items[1] + second_part_2 + for_items[0] + third_part_2

    elif len(request_items) == 3:
        for num, item in enumerate(request_items):
            for_item = for_item_maker(item, num)
            for_items.append(for_item)
        query = first_part_3 + for_items[1] + second_part_3 + for_items[2] + third_part_3 + for_items[0] + fourth_part_3
    return query

