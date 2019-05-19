#!/usr/bin/env python3
#coding: utf8


import re
import string

def ParseOutTag(text):
    pattern = re.compile('(PDF|HTML)')
    tag = pattern.findall(text)
    if tag:
        return tag[0]
    else:
        tag = None
        return tag

def ParseOutURL(text):
    try:
        url = text.strip()
        return url
    except:
        return None

def ParseOutTitle(text, p_key=[], n_key=[], key_score={'p': 1, 'n': -3, 'none': -5}):
    if text:
        title = remove_punctuation(text).strip()
        score = ThesisScore(title, p_key, n_key, key_score)
        return score
    else:
        title = None
        score = ThesisScore(title, p_key, n_key, key_score)
        return score

def ParseOutContent(text, p_key=[], n_key=[], key_score={'p': 1, 'n': -3, 'p_none': 1, 'n_none': -1, 'none': -5}):
    if text:
        content = remove_punctuation(text)
        score = ThesisScore(content, p_key, n_key, key_score)
        return score
    else:
        content = None
        score = ThesisScore(content, p_key, n_key, key_score)
        return score

def ThesisScore(text, p_key, n_key, key_score):
    score = 0
    ### If there is no text, set score = score + key_score['none']
    if text:
        ### If there is no p_key, set score = score + key_score['p_none']
        if p_key:
            ### If there is one element of p_key in text, set score = score + key_score['p']
            for key in p_key:
                if key.lower() in text.lower():
                    score += key_score['p']
        #else:
        #    score += key_score['p_none']
        ### If there is no n_key, set score = score + key_score['n_none']
        if n_key:
            ### If there is one element of n_key in text, set score = score key_score['n']
            for key in n_key:
                if key.lower() in text.lower():
                    score += key_score['n']
        #else:
        #    score += key_score['n_none']
        return score
    else:
        score += key_score['none']
        return score

def remove_punctuation(s_in, s_to=' '):
    translator = str.maketrans('', '', string.punctuation)
    return s_in.translate(translator)