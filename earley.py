#!/usr/bin/env python3

import sys
from enum import Enum


class Rule(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f'{self.lhs} -> {" ".join(self.rhs)}'


class Grammar(object):
    def __init__(self, rules, start_rule):
        self.rules = {}
        self.start_rule = start_rule

        for rule in rules:
            if rule.lhs not in self.rules:
                self.rules[rule.lhs] = [rule]
            else:
                self.rules[rule.lhs].append(rule)

    def __repr__(self):
        return '\n'.join(map(
            lambda rules: '\n'.join(map(str, rules)),
            self.rules.values()
        ))


class EarleyItem(object):
    def __init__(self, rule, start, dot, prev=[]):
        self.rule  = rule
        self.start = start
        self.dot   = dot
        self.prev  = prev[:]

    def __eq__(self, other):
        return isinstance(other, EarleyItem) and \
               self.rule  == other.rule      and \
               self.start == other.start     and \
               self.dot   == other.dot

    def __repr__(self):
        rhs = self.rule.rhs[:]
        rhs.insert(self.dot, '•')

        return f'{self.rule.lhs} -> {" ".join(map(str, rhs))} ({self.start})'


class ItemSet(list):
    def append(self, val):
        if not list.__contains__(self, val):
            list.append(self, val)

    def extend(self, values):
        for val in values:
            self.append(val)


class EarleyState(Enum):
    Complete    = 0
    Terminal    = 1
    NonTerminal = 2


def next_symb(earley_item, terminals):
    symb = None
    state = EarleyState.Complete

    if earley_item.dot < len(earley_item.rule.rhs):
        symb = earley_item.rule.rhs[earley_item.dot]
        state = EarleyState.Terminal if symb in terminals else EarleyState.NonTerminal

    return state, symb


def predict(grammar, item_set, symb, i):
    item_set.extend([EarleyItem(rule, i, 0) for rule in grammar.rules[symb]])


def scan(earley_item_set, item, symb, word, i):
    if symb == word:
        earley_item_set[i+1].append(EarleyItem(
            item.rule, item.start, item.dot+1, item.prev[:]
        ))


def complete(earley_item_set, item_set, item, terminals):
    item_set.extend(map(
        lambda it: EarleyItem(it.rule, it.start, it.dot+1, it.prev + [item]),
        filter(
            lambda old_item: next_symb(old_item, terminals)[1] == item.rule.lhs,
            earley_item_set[item.start]
        )
    ))


def earley(grammar, terminals, sentence):
    earley_item_set = list(map(ItemSet, [
        [EarleyItem(rule, 0, 0) for rule in grammar.rules[grammar.start_rule]],
        *[[] for _ in range(len(sentence))]
    ]))


    for i, (word, item_set) in enumerate(zip(sentence, earley_item_set)):
        for item in item_set:
            state, symb = next_symb(item, terminals)

            if state is EarleyState.Complete:
                complete(earley_item_set, item_set, item, terminals)
            elif state is EarleyState.NonTerminal:
                predict(grammar, item_set, symb, i)
            elif state is EarleyState.Terminal:
                scan(earley_item_set, item, symb, word, i)

    for item in earley_item_set[-1]:
        state, symb = next_symb(item, terminals)

        if state is EarleyState.Complete:
            complete(earley_item_set, earley_item_set[-1], item, terminals)

    return earley_item_set


def to_lr(item):
    return sum(map(to_lr, item.prev), []) + [item.rule]


if __name__ == '__main__':
    if sys.version_info < (3, 6):
        sys.exit('Python 3.6 or later is required.\n')

    debug = len(sys.argv) == 3 and sys.argv[2] == '--debug'

    rules = [
        Rule('expr', ['expr', '+', 'expr']),
        Rule('expr', ['expr', '-', 'expr']),
        Rule('expr', ['expr', '*', 'expr']),
        Rule('expr', ['expr', '/', 'expr']),
        Rule('expr', ['(', 'expr', ')']),
        Rule('expr', ['term']),
        *[Rule('term', [str(i)]) for i in range(10)]
    ]

    start_rule = 'expr'
    terminals = set('1234567890+-*/()')

    grammar = Grammar(rules, start_rule)
    sentence = list(sys.argv[1])

    earley_set = earley(grammar, terminals, sentence)


    if debug:
        print(f'Sentence: {" ".join(sentence)}\n')
        print(f'Rules:')
        print(grammar)

        for i, item_set in enumerate(earley_set):
            print(f"\n{'='*15}\n{str(i).center(15)}\n{'='*15}")

            for item in item_set:
                print(item)

        print('='*15)


    if len(earley_set) != len(sentence) + 1:
        print('Incorrect sentence.')
        exit(1)

    for item in earley_set[-1]:
        if      item.dot == len(item.rule.rhs) and \
                item.start == 0                and \
                item.rule.lhs == start_rule:
           last = item
           break
    else:
        print('Incorrect sentence.')
        exit(1)
    
    print('\n'.join(map(str, reversed(to_lr(last)))))