#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import string
import errno
import os


class Token(object):
    (state, create_state, position, create_position, custom, create_custom,
     impulse, create_impulse, repeat, create_repeat, dialog, create_dialog,
     comment, conditional, new_dialog_chain, command, new_line, custom_name
     ) = range(18)

    def __init__(self, type=None, value=None, name=None, line=None,
                 file_name=None):
        self.type = type
        self.value = value
        self.name = name

        self.file_name = file_name
        self.line = line

    def __str__(self):
        types = ['state', 'create_state', 'position', 'create_position',
                 'custom', 'create_custom', 'impulse', 'create_impulse',
                 'repeat', 'create_repeat', 'dialog', 'create_dialog',
                 'comment', 'conditional', 'new_dialog_chain', 'command',
                 'new_line', 'custom_name',
                 ]
        return str({
            'type': types[self.type], 'value': self.value, 'name': self.name,
        })

    def __repr__(self):
        types = [
            'state', 'create_state', 'position', 'create_position',
            'custom', 'create_custom', 'impulse', 'create_impulse', 'repeat',
            'create_repeat', 'dialog', 'create_dialog', 'comment',
            'conditional', 'new_dialog_chain', 'command', 'new_line',
            'custom_name'
        ]
        return str({
            'type': types[self.type], 'value': self.value,
            'name': self.name,
        })


class Parser(object):
    state_blocks = (
        'wool 0', 'wool 1', 'wool 2', 'wool 3', 'wool 4', 'wool 5',
        'wool 6', 'wool 7', 'wool 8', 'wool 9', 'wool 10', 'wool 11',
        'wool 12', 'wool 13', 'wool 14', 'wool 15', 'stained_hardened_clay 0',
        'stained_hardened_clay 1', 'stained_hardened_clay 2',
        'stained_hardened_clay 3', 'stained_hardened_clay 4',
        'stained_hardened_clay 5', 'stained_hardened_clay 6',
        'stained_hardened_clay 7', 'stained_hardened_clay 8',
        'stained_hardened_clay 9', 'stained_hardened_clay 10',
        'stained_hardened_clay 11', 'stained_hardened_clay 12',
        'stained_hardened_clay 13', 'stained_hardened_clay 14',
        'stained_hardened_clay 15',
    )
    off_on = ('lapis_block 0', 'redstone_block 0')

    def __init__(self, project_data_repository):
        self.project_data_repository = project_data_repository

        self.states = {}
        self.positions = {}
        self.custom_values = {}
        self.impulse_chains = {}
        self.repeat_chains = {}
        self.dialogs = {}
        self.tokens = []
        self.functions_tokens = []
        self.functions = {}

        # self.box = None
        # self.floor_height = None
        # self.behavior_pack_uuid = None
        # self.functions_path = None

    @staticmethod
    def parse(input_content,
              input_name='<string>',
              input_metadata='No more details...'):

        def parse_coordinates(command, count=3, allow_fraction=True):
            def parse_coordinate(command, allow_fraction=True):
                start, type, sign, integer, fraction = range(5)
                state = start
                i = 0
                success = False
                for c in command:
                    if state == start:
                        if c == '-':
                            i += 1
                            state = sign
                        elif c == '.' and allow_fraction:
                            i += 1
                            state = fraction
                        elif c in string.digits:
                            i += 1
                            state = integer
                            success = True
                        else:
                            break
                    elif state == type:
                        if c == '-':
                            i += 1
                            state = sign
                        # If type is not global decimals are allowed
                        elif c == '.':
                            i += 1
                            state = fraction
                        elif c in string.digits:
                            i += 1
                            state = integer
                            success = True
                        else:
                            break
                    elif state == sign:
                        # If type is not global decimals are allowed
                        if c == '.' and allow_fraction:
                            i += 1
                            state = fraction
                        elif c in string.digits:
                            i += 1
                            state = integer
                            success = True
                        else:
                            i -= 1
                            break
                    elif state == integer:
                        if c == '.' and allow_fraction:
                            i += 1
                            state = fraction
                        elif c in string.digits:
                            i += 1
                        else:
                            break
                    elif state == fraction:
                        if c in string.digits:
                            success = True
                            i += 1
                        else:
                            break
                try:
                    if allow_fraction:
                        return i, float(command[:i]), success
                    else:
                        return i, int(command[:i]), success
                except ValueError:
                    return i, None, False

            i = 0
            info = []
            for n in xrange(count):
                if i == len(command):
                    return i, info, False, "Unexpected end of vector."
                sep, val, success = parse_coordinate(
                        command[i:], allow_fraction=allow_fraction
                )
                if not success:
                    return i, info, False, "Unexpected character"

                info.append(val)
                i += sep
                if n < count - 1:
                    if i >= len(command):
                        return i, info, False, "Unexpected end of vector."
                    if command[i] == ' ':
                        i += 1
                    else:
                        break
            return i, info, True, ''

        def cut_word(command, separators=' \n\r\t', escape_characters=None,
                     allowed_chars=None):
            length = 0
            escape = False
            for c in command:
                length += 1
                if (c in separators) and (escape is False):
                    return length - 1, True
                if allowed_chars is not None:
                    if c not in allowed_chars:
                        return length - 1, False
                if escape_characters is not None:
                    if c in escape_characters:
                        escape = True
                    else:
                        escape = False
            return length, True

        input_content = input_content.strip()
        tokens = []
        if input_content.startswith('#') or input_content == '':
            return tokens
        start, start2, command, special, end, comment = range(6)
        # start2 - after conditional, new_dialog_chain or nothing
        # (check if commandblocks is named)
        tokens = []
        state = start
        input_len = len(input_content)
        i = 0
        consumed_input = 0
        while True:
            # Skip whitespaces and go to command, special or comment
            if state == start:
                if i < input_len:
                    if input_content[i] == '`':
                        i += 1
                        state = special
                        consumed_input = i
                    elif input_content[i] == '#':
                        i += 1
                        state = comment
                        consumed_input = i
                    elif input_content[i] == "+":
                        i += 1
                        tokens.append(Token(Token.new_dialog_chain, None, None,
                                            input_metadata, input_name))
                        consumed_input = i
                        for c in input_content[consumed_input:]:
                            if c in ' \t':
                                i += 1
                                consumed_input = 1
                            else:
                                break
                    elif input_content[i] == ">":
                        i += 1
                        tokens.append(Token(Token.conditional, None, None,
                                            input_metadata, input_name))
                        consumed_input = i
                        for c in input_content[consumed_input:]:
                            if c in ' \t':
                                i += 1
                                consumed_input = 1
                            else:
                                break
                    else:
                        state = start2
                        consumed_input = i
                else:
                    return tokens
            elif state == start2:
                if i < input_len:
                    if input_content[i] == '`':
                        i += 1
                        state = special
                        consumed_input = i
                    elif input_content[i] == '#':
                        i += 1
                        state = comment
                        consumed_input = i
                    elif input_content[i] == '[':
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:w2p2nw')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        tokens.append(Token(Token.custom_name, name, None,
                                            input_metadata, input_name))

                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.command,
                                    '',
                                    None,
                                    input_metadata,
                                    input_name))
                            state = end
                        else:
                            consumed_input = i
                            for c in input_content[consumed_input:]:
                                if c in ' \t':
                                    i += 1
                                else:
                                    break

                            if input_content[i] == '#':
                                consumed_input = i
                                state = comment
                            elif input_content[i] == '`':
                                consumed_input = i
                                state = special
                            else:
                                consumed_input = i
                                state = command
                    else:
                        state = command
                        consumed_input = i
                else:
                    return tokens
            elif state == command:
                length, _ = cut_word(input_content[i:], separators='`#',
                                     escape_characters='\\',
                                     allowed_chars=None)
                i += length
                if i >= input_len:
                    tokens.append(Token(Token.command,
                                        input_content[consumed_input:i],
                                        None,
                                        input_metadata,
                                        input_name))
                    return tokens
                if input_content[i] == '`':
                    tokens.append(Token(Token.command,
                                        input_content[consumed_input:i],
                                        None,
                                        input_metadata,
                                        input_name))
                    i += 1
                    consumed_input = i
                    state = special
                elif input_content[i] == '#':
                    tokens.append(Token(Token.command,
                                        input_content[consumed_input:i],
                                        None,
                                        input_metadata,
                                        input_name))
                    i += 1
                    consumed_input = i
                    state = comment
            elif state == special:

                if input_content[i] == '/':
                    i += 1
                    if i >= input_len:
                        raise Exception('Unexpected end of line ' +
                                        str(input_metadata) + ' in file ' +
                                        input_name + ' Code:1n7uvj')
                    if input_content[i] == 's':  # state
                        if input_content[i:].startswith('state'):
                            i += len('state')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:c08d9d')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:6bd8f2')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:gc4o14')
                        if input_content[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:0s8x5o')
                            (length, position,
                                success, error,
                             ) = parse_coordinates(input_content[i:], count=3,
                                                   allow_fraction=False)
                            if not success:
                                raise Exception(
                                    error +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:74gorv')
                            i += length
                            if not success:
                                raise Exception(
                                    error +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:88tnvr')
                            if input_content[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:p5ftde')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:xlmokx')
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:6w1tvi')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        position,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        position,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                                state = end
                        else:
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:p8hgpl')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        None,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        None,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                                state = end
                    elif input_content[i] == 'p':  # position
                        if input_content[i:].startswith('position'):
                            i += len('position')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:zbk245')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qw3n9i')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:5w86au')
                        if input_content[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qgr887')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:vo46qi')
                        (length, position,
                            success, error,
                         ) = parse_coordinates(input_content[i:], count=6,
                                               allow_fraction=False)
                        if not success:
                            (length, position,
                                success, error
                             ) = parse_coordinates(input_content[i:], count=3,
                                                   allow_fraction=False)
                        if not success:
                            raise Exception(
                                error +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:vzb57n')
                        i += length
                        if not success:
                            raise Exception(
                                error +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:nd64bz')
                        if input_content[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tzqqb3')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:omf5u6')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:o9limx')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_position,
                                    position,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_position,
                                    position,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                            state = end
                    elif input_content[i] == 'c':  # custom
                        if input_content[i:].startswith('custom'):
                            i += len('custom')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:4yu0rh')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:hamfrp')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:o0rg29')
                        if input_content[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:x2mfvz')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tx5p6h')

                        length, _ = cut_word(input_content[i:], separators=')',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        value = input_content[i:i + length]
                        i += length
                        if input_content[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:dnv39i')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:xholn8')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:14qutf')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_custom,
                                    value,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_custom,
                                    value,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                            state = end
                    elif input_content[i] == 'i':  # impulse
                        if input_content[i:].startswith('impulse'):
                            i += len('impulse')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:76lxxq')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tghhi5')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:zi8n8q')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qtkofv')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_impulse,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_impulse,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                            state = end
                    elif input_content[i] == 'r':  # repeat
                        if input_content[i:].startswith('repeat'):
                            i += len('repeat')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:7fbixj')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:w4zzkb')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:9r7t8e')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:sfukg3')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_repeat,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_repeat,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                            state = end
                    elif input_content[i] == 'd':  # dialog
                        if input_content[i:].startswith('dialog'):
                            i += len('dialog')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:px0vkm')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:4fd23c')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:1rb0e4')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:a04wgv')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_dialog,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_dialog,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                            state = end
                    else:
                        raise Exception('Unexpected character' + ' at line ' +
                                        str(input_metadata) + ' in file ' +
                                        input_name + ' Code:jtba5b')
                else:
                    if input_content[i] == 's':  # state
                        if input_content[i:].startswith('state'):
                            i += len('state')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tzc7vm')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:zdr77w')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qck9d9')
                        if input_content[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:q885lm')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:rxslfx')

                        length, _ = cut_word(
                                input_content[i:], separators=')',
                                escape_characters='\\',
                                allowed_chars=string.digits
                                )
                        value = int(input_content[i:i + length])
                        i += length
                        if input_content[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:1ohgt1')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:jqj1ix')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qd8008')
                        i += 1
                        if i >= input_len:
                            # if value.strip() != '':
                            tokens.append(
                                Token(
                                    Token.state,
                                    value,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.state,
                                    value,
                                    name,
                                    input_metadata,
                                    input_name))
                            consumed_input = i
                    elif input_content[i] == 'p':  # position
                        if input_content[i:].startswith('position'):
                            i += len('position')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tzx26k')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:ll2nko')
                        length, _ = cut_word(
                            input_content[i:], separators=']',
                            escape_characters='\\', allowed_chars=None
                            )
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:s4d0qi')
                        position_type = 'normal'
                        if input_content[i] == '@':
                            position_type = 'selector'
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:qxfmur')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:pu0tq7')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.position,
                                    position_type,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            consumed_input = i
                            tokens.append(
                                Token(
                                    Token.position,
                                    position_type,
                                    name,
                                    input_metadata,
                                    input_name))
                    elif input_content[i] == 'c':  # custom
                        if input_content[i:].startswith('custom'):
                            i += len('custom')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:gcsxnk')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:aij5ws')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:7rmwud')
                        if input_content[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:pdp13e')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.custom,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                            return tokens
                        else:
                            consumed_input = i
                            tokens.append(
                                Token(
                                    Token.custom,
                                    None,
                                    name,
                                    input_metadata,
                                    input_name))
                    elif input_content[i] == 'i':  # impulse
                        if input_content[i:].startswith('impulse'):
                            i += len('impulse')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:we1che')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:f2styu')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:519rgu')
                        if input_content[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:lwub02')
                            if input_content[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:2ctumy')
                            value = int(input_content[i])
                            i += 1
                            if input_content[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:08ejd7')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:qc3xk9')
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:8nwnrx')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                        else:
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:v6ke2l')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                    elif input_content[i] == 'r':  # repeat
                        if input_content[i:].startswith('repeat'):
                            i += len('repeat')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:tmbpwk')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:djwcv6')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:nvpbvu')
                        if input_content[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:hoq00m')
                            if input_content[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:w95b3k')
                            value = int(input_content[i])
                            i += 1
                            if input_content[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:pbew31')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:4a1wx7')
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:sqv4ay')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                        else:
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:dl42q3')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                    elif input_content[i] == 'd':  # dialog
                        if input_content[i:].startswith('dialog'):
                            i += len('dialog')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:pvcvuy')
                        if input_content[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:8u4tvo')
                        length, _ = cut_word(input_content[i:], separators=']',
                                             escape_characters='\\',
                                             allowed_chars=None)
                        name = input_content[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_metadata) +
                                ' in file ' +
                                input_name +
                                ' Code:dor3mx')
                        if input_content[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:92e5gx')
                            if input_content[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:yqhd46')
                            value = int(input_content[i])
                            i += 1
                            if input_content[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:4lavyk')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:5mjike')
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:t5pakw')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        value,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                        else:
                            if input_content[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_metadata) +
                                    ' in file ' +
                                    input_name +
                                    ' Code:9v2or2')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        1,
                                        name,
                                        input_metadata,
                                        input_name))
                                consumed_input = i
                    else:
                        raise Exception('Unexpected character' + ' at line ' +
                                        str(input_metadata) + ' in file ' +
                                        input_name + ' Code:gsg8w7')

                    if input_content[i] == '#':
                        consumed_input = i
                        state = comment
                    elif input_content[i] == '`':
                        consumed_input = i
                        state = special
                    else:
                        consumed_input = i
                        state = command
            elif state == end:  # Skip whitespaces and go to comment
                if i >= input_len:
                    return tokens
                elif input_content[i] == '#':
                    consumed_input = i
                    state = comment
                elif input_content[i] in ' \t':
                    consumed_input = i
                else:
                    raise Exception('Unexpected symbol' + ' at line ' +
                                    str(input_metadata) + ' in file ' +
                                    input_name + ' Code:vuajva')
                i += 1
            elif state == comment:  # Append comment to tokens and return
                i += 1
                if i >= input_len:
                    tokens.append(Token(Token.comment,
                                        input_content[consumed_input:i],
                                        None,
                                        input_metadata,
                                        input_name))
                    return tokens

            if i >= input_len:
                raise Exception(
                    'Unexpected end of line ' +
                    str(input_metadata) +
                    ' in file ' +
                    input_name +
                    ' Code:ng3qnc')

    def parse_all(self):
        for content, name, metadata in \
                self.project_data_repository.brfunction_generator():
            # content = file line, name = file name, metadata = file line index
            self.tokens.extend(Parser.parse(content, name, metadata))
            self.tokens.append(
                Token(Token.new_line, None, None, metadata, name)
            )

        for content, name, metadata in \
                self.project_data_repository.mcfunction_generator():
            # content = file line, name = file name, metadata = file line index
            if name not in self.functions:
                self.functions[name] = {'commands': []}
            self.functions_tokens.extend(Parser.parse(content, name, metadata))
            self.functions_tokens.append(
                Token(Token.new_line, None, None, metadata, name)
            )

        # type, value, name
        expect_comment_or_new_line = (
            Token.create_state,
            Token.create_position,
            Token.create_custom,
            Token.create_impulse,
            Token.create_repeat,
            Token.create_dialog,
        )
        code_tokens = (
            Token.state,
            Token.position,
            Token.custom,
            Token.impulse,
            Token.repeat,
            Token.dialog,
            Token.command,
            Token.custom_name,
        )

        # PARSE BRFUNCTIONS
        lastToken = Token.new_line
        curr_command_line = []
        is_first = True
        last_command_group = None
        new_dialog_chain_started = False
        # DEFINITIONS - collets all definitions and checks if tokens are in
        # correct order
        for t in self.tokens:
            if t.type == Token.create_state:
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "create_state" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:bu20ol')
                if t.name in self.states:
                    raise Exception('State ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:uz2hgi')
                self.states[t.name] = t.value
            elif t.type == Token.create_position:
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "create_position" token at' +
                                    'line' + str(t.line) + ' in file ' +
                                    t.file_name + ' Code:zvoi45')
                if t.name in self.positions:
                    raise Exception('Position ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:stx2kl')
                self.positions[t.name] = t.value
            elif t.type == Token.create_custom:
                if lastToken != Token.new_line:
                    raise Exception(
                        'Unexpected "create_custom" token at line' +
                        str(t.line) + ' in file ' + t.file_name +
                        ' Code:js6nq9')
                if t.name in self.custom_values:
                    raise Exception('Custom value ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:kk1laf')
                self.custom_values[t.name] = t.value
            elif t.type == Token.create_impulse:  # IMPULSE CHAIN
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "create_impulse" token at' +
                                    'line' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ' Code:7ylvl9')
                if t.name in self.impulse_chains:
                    raise Exception('Impulse chain ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:d2ju0e')
                self.impulse_chains[t.name] = {'position': t.value,
                                               'commands': [],
                                               }
                last_command_group = t
                is_first = True
            elif t.type == Token.create_repeat:  # REPEATING CHAIN
                if lastToken != Token.new_line:
                    raise Exception(
                        'Unexpected "create_repeat" token at line' +
                        str(t.line) + ' in file ' + t.file_name +
                        ' Code:8kazag')
                if t.name in self.repeat_chains:
                    raise Exception('Repeating chain ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:z8z27x')
                self.repeat_chains[t.name] = {'position': t.value,
                                              'commands': [],
                                              }
                last_command_group = t
                is_first = True
            elif t.type == Token.create_dialog:  # DIALOG CHAIN
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "create_dialog" token at' +
                                    'line' + str(t.line) + ' in file ' +
                                    t.file_name + ' Code:gr5edc')
                if t.name in self.dialogs:
                    raise Exception('Dialog ' +
                                    t.name +
                                    ' is declared more than one time (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:maepru')
                new_dialog_chain_started = False
                self.dialogs[t.name] = {'position': t.value, 'commands': []}
                last_command_group = t
                is_first = True
            elif t.type in code_tokens:
                if last_command_group is None:
                    raise Exception('Unexpected minecraft command before' +
                                    'starting command chain token at line ' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:r9yga8')
                if (last_command_group.type == Token.create_dialog and
                        new_dialog_chain_started is False):
                    raise Exception(
                        'Unexpected minecraft command before' +
                        'starting new dialog command chain (line ' +
                        str(t.line) + ' in file ' + t.file_name + ')' +
                        ' Code:6750wv')
                curr_command_line.append(t)
                is_first = False
            elif t.type == Token.new_dialog_chain:
                new_dialog_chain_started = True
                curr_command_line.append(t)
                is_first = True
            elif t.type == Token.conditional:
                if is_first:
                    raise Exception('First command in chain cannot be' +
                                    'conditional (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:x27nue')
                curr_command_line.append(t)
            elif t.type == Token.new_line:
                add_to_chain = True
                if len(curr_command_line) == 1:
                    if curr_command_line[0].type == Token.command:
                        if curr_command_line[0].value.strip() == '':
                            add_to_chain = False
                if len(curr_command_line) == 0:
                    add_to_chain = False
                if add_to_chain and last_command_group is not None:
                    if last_command_group.type == Token.create_impulse:
                        self.impulse_chains[
                                last_command_group.name]['commands']\
                            .append(curr_command_line)
                    elif last_command_group.type == Token.create_repeat:
                        self\
                            .repeat_chains[
                                    last_command_group.name]['commands']\
                            .append(curr_command_line)
                    elif last_command_group.type == Token.create_dialog:
                        self.dialogs[last_command_group.name]['commands']\
                            .append(curr_command_line)
                curr_command_line = []
            lastToken = t.type

        lastToken = Token.new_line
        # USING SAVED DATA - checks if there are no references to non-existing
        # variables
        for t in self.tokens:
            if t.type == Token.state:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "state" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:gnazon')
                if t.name not in self.states:
                    raise Exception('Trying to refer to state ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:1lfu6i')
            elif t.type == Token.position:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "position" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:7p1s9w')
                if t.name not in self.positions:
                    raise Exception('Trying to refer to position ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:3kzunj')
            elif t.type == Token.custom:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "custom" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:hew5yq')
                if t.name not in self.custom_values:
                    raise Exception('Trying to refer to custom value ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:nbfs33')
            elif t.type == Token.impulse:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "impulse" token at line ' +
                                    str(t.line) + ' in file ' +
                                    t.file_name + ' Code:r8jl1b')
                if t.name not in self.impulse_chains:
                    raise Exception('Trying to refer to impulse chain ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:9k89ng')
            elif t.type == Token.repeat:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "repeat" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:jn42q3')
                if t.name not in self.repeat_chains:
                    raise Exception('Trying to refer to repeating chain ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:dwp1hb')
            elif t.type == Token.dialog:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "dialog" token at line' +
                                    str(t.line) + ' in file ' + t.file_name +
                                    ' Code:cj8fih')
                if t.name not in self.dialogs:
                    raise Exception('Trying to refer to dialog ' +
                                    t.name +
                                    ' but it has on definition (line ' +
                                    str(t.line) +
                                    ' in file ' +
                                    t.file_name +
                                    ')' +
                                    ' Code:zl5lwq')
            # elif t.type == Token.comment:
            #    pass
            elif t.type == Token.command or t.type == Token.custom_name:
                if lastToken in expect_comment_or_new_line:
                    raise Exception('Unexpected "command" token at line' +
                                    str(t.line) + ' in file ' +
                                    t.file_name + ' Code:yk81ta')
            elif t.type == Token.conditional:
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "conditional" token at line' +
                                    str(t.line) + ' in file ' +
                                    t.file_name + ' Code:9s38dh')
            elif t.type == Token.new_line:
                pass
            lastToken = t.type

        # PARSE MCFUNCTIONS
        curr_command_line = []
        new_dialog_chain_started = False
        # DEFINITIONS - collets all mcfunctions commands, make sure there is no
        # variable definitions in mcfunctions, checks if there are no
        # references to non-existing variables
        for t in self.functions_tokens:
            if t.type == Token.create_state:
                raise Exception(
                    'States cannot be defined inside mcfunctions. ' +
                    'Line:' + str(t.line) +
                    ' File: ' + t.file_name + ' Code:evdlyg')
            elif t.type == Token.create_position:
                raise Exception('Positions cannot be defined inside' +
                                'mcfunctions. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:9uqqq4')
            elif t.type == Token.create_custom:
                raise Exception('Custom values cannot be defined inside ' +
                                'mcfunctions. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:i1kiv1')
            elif t.type == Token.create_impulse:  # IMPULSE CHAIN
                raise Exception('Impulse chains cannot be defined inside ' +
                                'mcfunctions. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:qfj4lo')
            elif t.type == Token.create_repeat:  # REPEATING CHAIN
                raise Exception('Repeating chains cannot be defined inside ' +
                                'mcfunctions. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:j355vi')
            elif t.type == Token.create_dialog:  # DIALOG CHAIN
                raise Exception('Dialog chains cannot be defined inside ' +
                                'mcfunctions. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:y7jdhd')
            elif t.type in code_tokens:
                if t.type == Token.state:
                    if t.name not in self.states:
                        raise Exception('Trying to refer to state ' +
                                        t.name +
                                        ' but it has on definition (line ' +
                                        str(t.line) +
                                        ' in file ' +
                                        t.file_name +
                                        ')' +
                                        ' Code:q30qmo')
                elif t.type == Token.position:
                    if t.name not in self.positions:
                        raise Exception('Trying to refer to position ' +
                                        t.name +
                                        ' but it has on definition (line ' +
                                        str(t.line) +
                                        ' in file ' +
                                        t.file_name +
                                        ')' +
                                        ' Code:1vdck4')
                elif t.type == Token.custom:
                    if t.name not in self.custom_values:
                        raise Exception('Trying to refer to custom value ' +
                                        t.name +
                                        ' but it has on definition (line ' +
                                        str(t.line) +
                                        ' in file ' +
                                        t.file_name +
                                        ')' +
                                        ' Code:zotsyv')
                elif t.type == Token.impulse:
                    if t.name not in self.impulse_chains:
                        raise Exception('Trying to refer to impulse chain ' +
                                        t.name +
                                        ' but it has on definition (line ' +
                                        str(t.line) +
                                        ' in file ' +
                                        t.file_name +
                                        ')' +
                                        ' Code:h0qy8l')
                elif t.type == Token.repeat:
                    if t.name not in self.repeat_chains:
                        raise Exception(
                            'Trying to refer to repeating chain ' +
                            t.name +
                            ' but it has on definition (line ' +
                            str(
                                t.line) +
                            ' in file ' +
                            t.file_name +
                            ')' +
                            ' Code:cv0r5q')
                elif t.type == Token.dialog:
                    if t.name not in self.dialogs:
                        raise Exception('Trying to refer to dialog ' +
                                        t.name +
                                        ' but it has on definition (line ' +
                                        str(t.line) +
                                        ' in file ' +
                                        t.file_name +
                                        ')' +
                                        ' Code:dpyerm')
                elif t.type == Token.custom_name:
                    raise Exception(
                        'Unexpected "custom_name" token inside ' +
                        'mcfunction file. Line:' +
                        str(
                            t.line) +
                        ' File: ' +
                        t.file_name +
                        ' Code:qtm2li')
                curr_command_line.append(t)
            elif t.type == Token.new_dialog_chain:
                raise Exception(
                    'Unexpected "new_dialog_chain" token inside ' +
                    'mcfunction file. Line:' +
                    str(
                        t.line) +
                    ' File: ' +
                    t.file_name +
                    ' Code:bi9c9t')
            elif t.type == Token.conditional:
                raise Exception('Unexpected conditional command inside ' +
                                'mcfunction file. Line:' +
                                str(t.line) +
                                ' File: ' +
                                t.file_name +
                                ' Code:wf9p30')
            elif t.type == Token.new_line:
                add_to_chain = True
                if len(curr_command_line) == 1:
                    if curr_command_line[0].type == Token.command:
                        if curr_command_line[0].value.strip() == '':
                            add_to_chain = False
                if len(curr_command_line) == 0:
                    add_to_chain = False
                if add_to_chain:
                    self.functions[t.file_name]['commands']\
                        .append(curr_command_line)
                curr_command_line = []

    def command_to_string(self, command_elements):
        is_new_dialog_chain = False
        is_conditional = False
        command = ""
        customName = ""

        for element in command_elements:
            if element.type == Token.state:
                command = command \
                    + ' '.join([str(i) for i in self.states[element.name]]) \
                    + ' ' + Parser.state_blocks[element.value]
            elif element.type == Token.position:
                if element.value == 'selector':
                    positions = self.positions[element.name]
                    if len(positions) == 6:
                        command = command + 'x=' + str(positions[0]) \
                            + ',y=' + str(positions[1]) \
                            + ',z=' + str(positions[2]) \
                            + ',dx=' + str(positions[3] - positions[0]) \
                            + ',dy=' + str(positions[4] - positions[1]) \
                            + ',dz=' + str(positions[5] - positions[2])
                    else:  # 3
                        command = command + 'x=' + str(positions[0]) + ',y=' \
                            + str(positions[1]) + ',z=' + str(positions[2])
                else:
                    command = command \
                        + ' '.join(
                            [str(i) for i in self.positions[element.name]]
                        )
            elif element.type == Token.custom:
                command += self.custom_values[element.name]
            elif element.type == Token.impulse:
                command = command + ' '.join(
                    [str(i) for i in
                     self.impulse_chains[element.name]['position']]
                ) + ' ' + Parser.off_on[element.value]
            elif element.type == Token.repeat:
                command = command + ' '.join(
                    [str(i) for i in
                     self.repeat_chains[element.name]['position']]
                ) + ' ' + Parser.off_on[element.value]
            elif element.type == Token.dialog:
                command = command + ' '.join(
                    [str(i) for i in self.dialogs[element.name]['position']]
                ) + ' ' + Parser.off_on[element.value]
            elif element.type == Token.conditional:
                is_conditional = True
            elif element.type == Token.new_dialog_chain:
                is_new_dialog_chain = True
            elif element.type == Token.command:
                command += element.value
            elif element.type == Token.custom_name:
                customName = element.value
        return command, is_conditional, is_new_dialog_chain, customName
