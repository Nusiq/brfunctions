#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://github.com/Nusiq/brfunctions

from pymclevel import (
    TAG_List, TAG_Byte, TAG_Int, TAG_Compound, TAG_Short,
    TAG_String, TAG_Long, alphaMaterials,
)
import json
import string
import os
import hashlib
import errno


class CustomBox:
    def __init__(self):
        self.minx = None
        self.miny = None
        self.minz = None
        self.maxx = None
        self.maxy = None
        self.maxz = None


class Builder:
    y_down, y_up, z_down, z_up, x_down, x_up = range(6)
    cb_impulse, cb_repeat, cb_chain = range(3)

    def place_block(x, y, z, block, level):
        chunk = level.getChunk(x / 16, z / 16)
        level.setBlockAt(x, y, z, block.ID)
        level.setBlockDataAt(x, y, z, block.blockData)
        chunk.dirty = True
    place_block = staticmethod(place_block)

    def place_comparator(x, y, z, level, direction, signal, compare):
        signal = 0 if signal < 0 else (15 if signal > 15 else signal)
        comparator_directions = {
            Builder.z_up: 0, Builder.x_down: 1,
            Builder.z_down: 2, Builder.x_up: 3,
        }

        comparator = TAG_Compound()
        comparator["OutputSignal"] = TAG_Int(signal)
        comparator["id"] = TAG_String(u'Comparator')
        comparator["isMoveable"] = TAG_Byte(1)
        comparator["x"] = TAG_Int(x)
        comparator["y"] = TAG_Int(y)
        comparator["z"] = TAG_Int(z)

        chunk = level.getChunk(x / 16, z / 16)
        # Remove tileEntities if they exist.
        te = level.tileEntityAt(x, y, z)
        if te is not None:
            chunk.TileEntities.remove(te)
        chunk.TileEntities.append(comparator)
        chunk.dirty = True
        direction = comparator_directions[direction]
        if signal > 0:
            direction += 8
        if not compare:
            direction += 4
        Builder.place_block(x, y, z, alphaMaterials[149, direction], level)
    place_comparator = staticmethod(place_comparator)

    def place_cmdblock(x, y, z, level, cmdBlockType, direction, command,
                       conditional, customName=u''):
        cb_types = {Builder.cb_impulse: 137, Builder.cb_chain: 189,
                    Builder.cb_repeat: 188,
                    }
        cb_directions = {Builder.y_down: 0, Builder.y_up: 1, Builder.z_down: 2,
                         Builder.z_up: 3, Builder.x_down: 4, Builder.x_up: 5,
                         }

        tileCB = TAG_Compound()
        tileCB["Command"] = TAG_String(command)
        tileCB["CustomName"] = TAG_String(customName)
        tileCB["LPCommandMode"] = TAG_Int(0)
        tileCB["LPCondionalMode"] = TAG_Byte(0)
        tileCB["LPRedstoneMode"] = TAG_Byte(0)
        tileCB["LastExecution"] = TAG_Long(0)
        tileCB["LastOutput"] = TAG_String(u'OUTPUT')
        tileCB["LastOutputParams"] = TAG_List([
            TAG_String(u'1'),
            TAG_String(u'2'), TAG_String(u'3'),
        ])
        tileCB["SuccessCount"] = TAG_Int(0)
        tileCB["TrackOutput"] = TAG_Byte(0)
        tileCB["Version"] = TAG_Int(8)
        tileCB["auto"] = TAG_Byte(1 if cmdBlockType == Builder.cb_chain else 0)
        tileCB["conditionMet"] = TAG_Byte(0)
        tileCB["id"] = TAG_String(u'CommandBlock')
        tileCB["isMovable"] = TAG_Byte(1)
        tileCB["powered"] = TAG_Byte(0)
        tileCB["x"] = TAG_Int(x)
        tileCB["y"] = TAG_Int(y)
        tileCB["z"] = TAG_Int(z)
        chunk = level.getChunk(x / 16, z / 16)
        # Remove tileEntities if they exist.
        te = level.tileEntityAt(x, y, z)
        if te is not None:
            chunk.TileEntities.remove(te)

        chunk.TileEntities.append(tileCB)
        chunk.dirty = True

        direction = cb_directions[direction]
        if conditional:
            direction += 8
        # Wywolanie funkcji wewnatrz drugiej funkcji
        Builder.place_block(
            x, y, z, alphaMaterials[cb_types[cmdBlockType], direction], level
        )
    place_cmdblock = staticmethod(place_cmdblock)

    def place_hooper(x, y, z, level, items, direction, disabled):
        hopper_directions = {
            Builder.y_down: 0, Builder.z_down: 2,
            Builder.z_up: 3, Builder.x_down: 4, Builder.x_up: 5,
        }

        hooper = TAG_Compound()
        hooper["Items"] = TAG_List()
        i = 0
        for it in items:
            if i == 5:
                break
            item = TAG_Compound()
            item["Count"] = TAG_Byte(it)
            item["Damage"] = TAG_Short(0)
            item["Slot"] = TAG_Byte(i)
            item["id"] = TAG_Short(22)
            hooper["Items"].append(item)
            i += 1
        hooper["TransferCooldown"] = TAG_Int(0)
        hooper["id"] = TAG_String(u'Hopper')
        hooper["isMovable"] = TAG_Byte(1)
        hooper["x"] = TAG_Int(x)
        hooper["y"] = TAG_Int(y)
        hooper["z"] = TAG_Int(z)
        chunk = level.getChunk(x / 16, z / 16)
        # Remove tileEntities if they exist.
        te = level.tileEntityAt(x, y, z)
        if te is not None:
            chunk.TileEntities.remove(te)

        chunk.TileEntities.append(hooper)
        chunk.dirty = True
        direction = hopper_directions[direction]
        if disabled:
            direction += 8
        # Wywolanie funkcji wewnatrz drugiej funkcji
        Builder.place_block(x, y, z, alphaMaterials[154, direction], level)
    place_hooper = staticmethod(place_hooper)


class Token:
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


class Parser:
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

    def __init__(self):
        self.states = {}
        self.positions = {}
        self.custom_values = {}
        self.impulse_chains = {}
        self.repeat_chains = {}
        self.dialogs = {}
        self.tokens = []
        self.functions_tokens = []
        self.functions = {}
        self.box = None
        self.floor_height = None
        self.behavior_pack_uuid = None
        self.functions_path = None

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
            sep, val, success = parse_coordinate(command[i:],
                                                 allow_fraction=allow_fraction)
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
    parse_coordinates = staticmethod(parse_coordinates)

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
    cut_word = staticmethod(cut_word)

    def parse(input, input_line_index, input_file_name):
        input = input.strip()
        tokens = []
        if input.startswith('#') or input == '':
            return tokens
        start, start2, command, special, end, comment = range(6)
        # start2 - after conditional, new_dialog_chain or nothing
        # (check if commandblocks is named)
        tokens = []
        state = start
        input_len = len(input)
        i = 0
        consumed_input = 0
        while True:
            # Skip whitespaces and go to command, special or comment
            if state == start:
                if i < input_len:
                    if input[i] == '`':
                        i += 1
                        state = special
                        consumed_input = i
                    elif input[i] == '#':
                        i += 1
                        state = comment
                        consumed_input = i
                    elif input[i] == "+":
                        i += 1
                        tokens.append(Token(Token.new_dialog_chain, None, None,
                                            input_line_index, input_file_name))
                        consumed_input = i
                        for c in input[consumed_input:]:
                            if c in ' \t':
                                i += 1
                                consumed_input = 1
                            else:
                                break
                    elif input[i] == ">":
                        i += 1
                        tokens.append(Token(Token.conditional, None, None,
                                            input_line_index, input_file_name))
                        consumed_input = i
                        for c in input[consumed_input:]:
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
                    if input[i] == '`':
                        i += 1
                        state = special
                        consumed_input = i
                    elif input[i] == '#':
                        i += 1
                        state = comment
                        consumed_input = i
                    elif input[i] == '[':
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:w2p2nw')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        tokens.append(Token(Token.custom_name, name, None,
                                            input_line_index, input_file_name))

                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.command,
                                    '',
                                    None,
                                    input_line_index,
                                    input_file_name))
                            state = end
                        else:
                            consumed_input = i
                            for c in input[consumed_input:]:
                                if c in ' \t':
                                    i += 1
                                else:
                                    break

                            if input[i] == '#':
                                consumed_input = i
                                state = comment
                            elif input[i] == '`':
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
                length, _ = Parser.cut_word(input[i:], separators='`#',
                                            escape_characters='\\',
                                            allowed_chars=None)
                i += length
                if i >= input_len:
                    tokens.append(Token(Token.command,
                                        input[consumed_input:i],
                                        None,
                                        input_line_index,
                                        input_file_name))
                    return tokens
                if input[i] == '`':
                    tokens.append(Token(Token.command,
                                        input[consumed_input:i],
                                        None,
                                        input_line_index,
                                        input_file_name))
                    i += 1
                    consumed_input = i
                    state = special
                elif input[i] == '#':
                    tokens.append(Token(Token.command,
                                        input[consumed_input:i],
                                        None,
                                        input_line_index,
                                        input_file_name))
                    i += 1
                    consumed_input = i
                    state = comment
            elif state == special:

                if input[i] == '/':
                    i += 1
                    if i >= input_len:
                        raise Exception('Unexpected end of line '
                                        + str(input_line_index) + ' in file '
                                        + input_file_name + ' Code:1n7uvj')
                    if input[i] == 's':  # state
                        if input[i:].startswith('state'):
                            i += len('state')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:c08d9d')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:6bd8f2')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:gc4o14')
                        if input[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:0s8x5o')
                            (length, position,
                                success, error,
                             ) = Parser.parse_coordinates(input[i:],
                                                          count=3,
                                                          allow_fraction=False)
                            if not success:
                                raise Exception(
                                    error +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:74gorv')
                            i += length
                            if not success:
                                raise Exception(
                                    error +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:88tnvr')
                            if input[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:p5ftde')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:xlmokx')
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:6w1tvi')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        position,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        position,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                                state = end
                        else:
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:p8hgpl')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        None,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.create_state,
                                        None,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                                state = end
                    elif input[i] == 'p':  # position
                        if input[i:].startswith('position'):
                            i += len('position')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:zbk245')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qw3n9i')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:5w86au')
                        if input[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qgr887')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:vo46qi')
                        (length, position,
                            success, error,
                         ) = Parser.parse_coordinates(input[i:],
                                                      count=6,
                                                      allow_fraction=False)
                        if not success:
                            (length, position,
                                success, error
                             ) = Parser.parse_coordinates(input[i:],
                                                          count=3,
                                                          allow_fraction=False)
                        if not success:
                            raise Exception(
                                error +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:vzb57n')
                        i += length
                        if not success:
                            raise Exception(
                                error +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:nd64bz')
                        if input[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tzqqb3')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:omf5u6')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:o9limx')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_position,
                                    position,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_position,
                                    position,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                            state = end
                    elif input[i] == 'c':  # custom
                        if input[i:].startswith('custom'):
                            i += len('custom')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:4yu0rh')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:hamfrp')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:o0rg29')
                        if input[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:x2mfvz')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tx5p6h')

                        length, _ = Parser.cut_word(input[i:], separators=')',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        value = input[i:i + length]
                        i += length
                        if input[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:dnv39i')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:xholn8')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:14qutf')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_custom,
                                    value,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_custom,
                                    value,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                            state = end
                    elif input[i] == 'i':  # impulse
                        if input[i:].startswith('impulse'):
                            i += len('impulse')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:76lxxq')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tghhi5')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:zi8n8q')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qtkofv')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_impulse,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_impulse,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                            state = end
                    elif input[i] == 'r':  # repeat
                        if input[i:].startswith('repeat'):
                            i += len('repeat')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:7fbixj')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:w4zzkb')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:9r7t8e')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:sfukg3')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_repeat,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_repeat,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                            state = end
                    elif input[i] == 'd':  # dialog
                        if input[i:].startswith('dialog'):
                            i += len('dialog')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:px0vkm')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:4fd23c')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:1rb0e4')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:a04wgv')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.create_dialog,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.create_dialog,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                            state = end
                    else:
                        raise Exception('Unexpected character' + ' at line '
                                        + str(input_line_index) + ' in file '
                                        + input_file_name + ' Code:jtba5b')
                else:
                    if input[i] == 's':  # state
                        if input[i:].startswith('state'):
                            i += len('state')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tzc7vm')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:zdr77w')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qck9d9')
                        if input[i] != '(':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:q885lm')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:rxslfx')

                        length, _ = Parser.cut_word(
                                input[i:], separators=')',
                                escape_characters='\\',
                                allowed_chars=string.digits
                                )
                        value = int(input[i:i + length])
                        i += length
                        if input[i] != ')':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:1ohgt1')
                        i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:jqj1ix')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qd8008')
                        i += 1
                        if i >= input_len:
                            # if value.strip() != '':
                            tokens.append(
                                Token(
                                    Token.state,
                                    value,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            tokens.append(
                                Token(
                                    Token.state,
                                    value,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            consumed_input = i
                    elif input[i] == 'p':  # position
                        if input[i:].startswith('position'):
                            i += len('position')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tzx26k')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:ll2nko')
                        length, _ = Parser.cut_word(
                            input[i:], separators=']',
                            escape_characters='\\', allowed_chars=None
                            )
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:s4d0qi')
                        position_type = 'normal'
                        if input[i] == '@':
                            position_type = 'selector'
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:qxfmur')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:pu0tq7')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.position,
                                    position_type,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            consumed_input = i
                            tokens.append(
                                Token(
                                    Token.position,
                                    position_type,
                                    name,
                                    input_line_index,
                                    input_file_name))
                    elif input[i] == 'c':  # custom
                        if input[i:].startswith('custom'):
                            i += len('custom')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:gcsxnk')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:aij5ws')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:7rmwud')
                        if input[i] != '`':
                            raise Exception(
                                'Unexpected character' +
                                ' at line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:pdp13e')
                        i += 1
                        if i >= input_len:
                            tokens.append(
                                Token(
                                    Token.custom,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                            return tokens
                        else:
                            consumed_input = i
                            tokens.append(
                                Token(
                                    Token.custom,
                                    None,
                                    name,
                                    input_line_index,
                                    input_file_name))
                    elif input[i] == 'i':  # impulse
                        if input[i:].startswith('impulse'):
                            i += len('impulse')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:we1che')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:f2styu')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:519rgu')
                        if input[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:lwub02')
                            if input[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:2ctumy')
                            value = int(input[i])
                            i += 1
                            if input[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:08ejd7')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:qc3xk9')
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:8nwnrx')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                        else:
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:v6ke2l')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.impulse,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                    elif input[i] == 'r':  # repeat
                        if input[i:].startswith('repeat'):
                            i += len('repeat')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:tmbpwk')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:djwcv6')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:nvpbvu')
                        if input[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:hoq00m')
                            if input[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:w95b3k')
                            value = int(input[i])
                            i += 1
                            if input[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:pbew31')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:4a1wx7')
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:sqv4ay')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                        else:
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:dl42q3')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.repeat,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                    elif input[i] == 'd':  # dialog
                        if input[i:].startswith('dialog'):
                            i += len('dialog')
                        else:
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:pvcvuy')
                        if input[i] == '[':
                            i += 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:8u4tvo')
                        length, _ = Parser.cut_word(input[i:], separators=']',
                                                    escape_characters='\\',
                                                    allowed_chars=None)
                        name = input[i:length + i]
                        i += length + 1
                        if i >= input_len:
                            raise Exception(
                                'Unexpected end of line ' +
                                str(input_line_index) +
                                ' in file ' +
                                input_file_name +
                                ' Code:dor3mx')
                        if input[i] == '(':
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:92e5gx')
                            if input[i] not in '01':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:yqhd46')
                            value = int(input[i])
                            i += 1
                            if input[i] != ')':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:4lavyk')
                            i += 1
                            if i >= input_len:
                                raise Exception(
                                    'Unexpected end of line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:5mjike')
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:t5pakw')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        value,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                        else:
                            if input[i] != '`':
                                raise Exception(
                                    'Unexpected character' +
                                    ' at line ' +
                                    str(input_line_index) +
                                    ' in file ' +
                                    input_file_name +
                                    ' Code:9v2or2')
                            i += 1
                            if i >= input_len:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                return tokens
                            else:
                                tokens.append(
                                    Token(
                                        Token.dialog,
                                        1,
                                        name,
                                        input_line_index,
                                        input_file_name))
                                consumed_input = i
                    else:
                        raise Exception('Unexpected character' + ' at line '
                                        + str(input_line_index) + ' in file '
                                        + input_file_name + ' Code:gsg8w7')

                    if input[i] == '#':
                        consumed_input = i
                        state = comment
                    elif input[i] == '`':
                        consumed_input = i
                        state = special
                    else:
                        consumed_input = i
                        state = command
            elif state == end:  # Skip whitespaces and go to comment
                if i >= input_len:
                    return tokens
                elif input[i] == '#':
                    consumed_input = i
                    state = comment
                elif input[i] in ' \t':
                    consumed_input = i
                else:
                    raise Exception('Unexpected symbol' + ' at line '
                                    + str(input_line_index) + ' in file '
                                    + input_file_name + ' Code:vuajva')
                i += 1
            elif state == comment:  # Append comment to tokens and return
                i += 1
                if i >= input_len:
                    tokens.append(Token(Token.comment,
                                        input[consumed_input:i],
                                        None,
                                        input_line_index,
                                        input_file_name))
                    return tokens

            if i >= input_len:
                raise Exception(
                    'Unexpected end of line ' +
                    str(input_line_index) +
                    ' in file ' +
                    input_file_name +
                    ' Code:ng3qnc')
    parse = staticmethod(parse)

    def parse_file(self, file_name):
        use_as_project = True
        project_data = None

        # Test if file is json project file
        try:
            with open(file_name) as projectFile:
                project_data = json.load(projectFile)
        except BaseException:
            use_as_project = False

        if use_as_project:  # The file is a json project file
            if isinstance(project_data, dict):
                if (('files' not in project_data.keys()) or
                        ('area' not in project_data.keys())):
                    raise Exception('Invalid project file structure. '
                                    + type(project_data) + ' Code:wiv5af')

                self.box = CustomBox()
                self.box.minx = project_data['area'][0] if \
                    project_data['area'][0] < project_data['area'][3] else \
                    project_data['area'][3]
                self.box.miny = project_data['area'][1] if \
                    project_data['area'][1] < project_data['area'][4] else \
                    project_data['area'][4]
                self.box.minz = project_data['area'][2] if \
                    project_data['area'][2] < project_data['area'][5] else \
                    project_data['area'][5]
                self.box.maxx = project_data['area'][0] if \
                    project_data['area'][0] > project_data['area'][3] else \
                    project_data['area'][3]
                self.box.maxy = project_data['area'][1] if \
                    project_data['area'][1] > project_data['area'][4] else \
                    project_data['area'][4]
                self.box.maxz = project_data['area'][2] if \
                    project_data['area'][2] > project_data['area'][5] else \
                    project_data['area'][5]

                # Save additional options data
                if 'floor_height' in project_data.keys():
                    self.floor_height = project_data['floor_height']
                if 'behavior_pack_uuid' in project_data.keys():
                    self.behavior_pack_uuid = \
                        project_data['behavior_pack_uuid']
                if 'functions_path' in project_data.keys():
                    self.functions_path = project_data['functions_path']
            elif isinstance(project_data, list):
                project_data = {'files': project_data}
            else:
                raise Exception('Invalid project file structure. '
                                + type(project_data) + ' Code:x6ibzz')

            path = os.path.split(file_name)[0]
            if self.functions_path is not None:
                self.functions_path = os.path.join(path, self.functions_path)

            # Get tokens from brfunctions
            for item_file_name in project_data['files']:
                full_item_file_name = path + '/' + item_file_name
                with open(full_item_file_name) as f:
                    line_index = 1
                    for l in f:
                        p = Parser.parse(l, line_index, full_item_file_name)
                        self.tokens.extend(p)
                        self.tokens.append(
                            Token(
                                Token.new_line,
                                None,
                                None,
                                line_index,
                                full_item_file_name))
                        line_index += 1

            # Get tokens from mcfunctions
            if (self.behavior_pack_uuid is not None and
                    self.functions_path is not None):
                # else: nothing to copy
                # cut = len(self.functions_path) + 1
                for root, dirs, files in os.walk(self.functions_path):
                    for name in files:
                        if name.endswith('.mcfunction'):
                            source = os.path.join(root, name)
                            if source not in self.functions:
                                self.functions[source] = {'commands': []}
                            with open(source) as f:
                                line_index = 1
                                for l in f:
                                    p = Parser.parse(l, line_index, source)
                                    self.functions_tokens.extend(p)
                                    self.functions_tokens.append(
                                        Token(Token.new_line, None, None,
                                              line_index, source))
                                    line_index += 1

        else:  # The file is a brfunction
            with open(file_name) as f:
                line_index = 1
                for l in f:
                    p = Parser.parse(l, line_index, file_name)
                    self.tokens.extend(p)
                    self.tokens.append(Token(Token.new_line, None, None,
                                             line_index, file_name))
                    line_index += 1

        # tape, value, name
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
                    raise Exception('Unexpected "create_state" token at line'
                                    + str(t.line) + ' in file ' + t.file_name
                                    + ' Code:bu20ol')
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
                    raise Exception('Unexpected "create_position" token at'
                                    + 'line' + str(t.line) + ' in file '
                                    + t.file_name + ' Code:zvoi45')
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
                    raise Exception('Unexpected "create_custom" token at line'
                                    + str(t.line) + ' in file ' + t.file_name
                                    + ' Code:js6nq9')
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
                    raise Exception('Unexpected "create_repeat" token at line'
                                    + str(t.line) + ' in file ' + t.file_name
                                    + ' Code:8kazag')
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
                    raise Exception('Unexpected "create_dialog" token at'
                                    + 'line' + str(t.line) + ' in file '
                                    + t.file_name + ' Code:gr5edc')
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
                    raise Exception('Unexpected minecraft command before'
                                    + 'starting command chain token at line '
                                    + str(t.line) + ' in file ' + t.file_name
                                    + ' Code:r9yga8')
                if (last_command_group.type == Token.create_dialog and
                        new_dialog_chain_started is False):
                    raise Exception('Unexpected minecraft command before' +
                                    'starting new dialog command chain (line '
                                    + str(t.line) + ' in file ' +
                                    t.file_name +
                                    ')' +
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
                                    str(t.line) + ' in file ' + t.file_name
                                    + ' Code:gnazon')
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
                                    str(t.line) + ' in file ' + t.file_name
                                    + ' Code:7p1s9w')
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
                                    str(t.line) + ' in file ' + t.file_name
                                    + ' Code:hew5yq')
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
                                    str(t.line) + ' in file '
                                    + t.file_name + ' Code:r8jl1b')
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
                                    str(t.line) + ' in file ' + t.file_name
                                    + ' Code:jn42q3')
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
                                    str(t.line) + ' in file ' + t.file_name
                                    + ' Code:cj8fih')
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
                                    str(t.line) + ' in file '
                                    + t.file_name + ' Code:yk81ta')
            elif t.type == Token.conditional:
                if lastToken != Token.new_line:
                    raise Exception('Unexpected "conditional" token at line' +
                                    str(t.line) + ' in file '
                                    + t.file_name + ' Code:9s38dh')
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
                raise Exception('States cannot be defined inside mcfunctions. '
                                + 'Line:' + str(t.line)
                                + ' File: ' + t.file_name + ' Code:evdlyg')
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


class Planner:
    zp, zm, up, skip_zp, skip_zm, skip_up = ('zp', 'zm', 'up', 'skip_zp',
                                             'skip_zm', 'skip_up')

    def __init__(self, parser):
        self.parser = parser
        self.impulse_chains = {}
        self.repeat_chains = {}
        self.dialogs = {}
        self.states = 0
        self.analyse()

    def plan_chain_space(self, chain_lengths, lim_y, lim_z):
        cursor_x = 0
        cursor_y = 0
        cursor_z = 0
        plus, minus, plus_up, minus_up = range(4)
        direction = plus
        plan = []

        # Cannot fit the longest conditional chain
        if max(chain_lengths) > lim_z - 1:
            return None

        def curve(new_x, new_y, new_z, direction):
            if direction == plus or direction == plus_up:
                while True:
                    if new_z == lim_z - 1:
                        plan.append(Planner.skip_up)
                        new_y += 1
                        break
                    elif new_z < lim_z - 1:
                        plan.append(Planner.skip_zp)
                        new_z += 1
                    else:
                        raise Exception('Planner Error' + ' Code:xauzw6')
            elif direction == minus or direction == minus_up:
                while True:
                    if new_z == 0:
                        plan.append(Planner.skip_up)
                        new_y += 1
                        break
                    elif new_z > 0:
                        plan.append(Planner.skip_zm)
                        new_z -= 1
                    else:
                        raise Exception('Planner Error' + ' Code:5kn9x6')
            if direction == plus or direction == plus_up:
                direction = minus
            elif direction == minus or direction == minus_up:
                direction = plus

            return new_x, new_y, new_z, direction

        def add_instructions(new_x, new_y, new_z, conditional_len,
                             new_direction):
            new_plan = []
            success = False
            if conditional_len == 1:
                if new_direction == plus_up:
                    new_plan.append(Planner.up)
                    new_y += 1
                    success = True
                    new_direction = minus
                elif new_direction == minus_up:
                    new_plan.append(Planner.up)
                    new_y += 1
                    success = True
                    new_direction = plus
                elif new_direction == plus:
                    new_plan.append(Planner.zp)
                    new_z += 1
                    if new_z == lim_z - 1:
                        new_direction = plus_up
                    success = True
                elif new_direction == minus:
                    new_plan.append(Planner.zm)
                    new_z -= 1
                    if new_z == 0:
                        new_direction = minus_up
                    success = True
            else:
                if new_direction == plus:
                    new_z += conditional_len
                    for i in range(conditional_len):
                        new_plan.append(Planner.zp)
                    if new_z <= lim_z - 1:
                        success = True
                    if new_z == lim_z - 1:
                        new_direction = plus_up

                elif new_direction == minus:
                    new_z -= conditional_len
                    for i in range(conditional_len):
                        new_plan.append(Planner.zm)
                    if new_z >= 0:
                        success = True
                    if new_z == 0:
                        new_direction = minus_up
            return new_x, new_y, new_z, new_plan, new_direction, success

        for curr_len in chain_lengths:
            new_x, new_y, new_z, new_plan, new_direction, success = \
                add_instructions(cursor_x, cursor_y, cursor_z, curr_len,
                                 direction)
            if not success:
                cursor_x, cursor_y, cursor_z, direction = curve(
                    cursor_x, cursor_y, cursor_z, direction)
                new_x, new_y, new_z, new_plan, new_direction, success = \
                    add_instructions(cursor_x, cursor_y, cursor_z, curr_len,
                                     direction)
                if not success:
                    raise Exception('Planner Error' + ' Code:kgthp1')
            cursor_x, cursor_y, cursor_z = new_x, new_y, new_z
            direction = new_direction
            plan.extend(new_plan)
        if cursor_y >= lim_y - 1:
            return None
        return plan

    def is_space_for_dialog(self, chain_lengths, lim_y, lim_z):
        lengths = [sum(i) for i in chain_lengths]
        required_y = max(lengths) + 2
        if required_y > lim_y:
            return False

        required_z = 2 + (len(chain_lengths) -
                          1 if len(chain_lengths) > 0 else 0) * 4
        if required_z > lim_z:
            return False
        return True

    def plan_and_build(self, box, level, floor_block, floor_height=255):
        limx = box.maxx - box.minx
        limy = box.maxy - box.miny
        limz = box.maxz - box.minz
        floor_height = floor_height if floor_height < limy else limy
        lim_n_floors = int(limy / floor_height)

        impulse_chains_projects = {}
        repeat_chains_projects = {}

        required_x = []

        # Checking if there is enough space for STATES (wool blocks)
        if limx * (limy - 1) < self.states:
            raise Exception('Not enough space for states (increase X size)'
                            + ' Code:rdeiy6')

        # Checking if there is enough space for command structures
        for k, v in self.impulse_chains.items():
            # required_x += 2
            required_x.append(2)
            # plan = self.plan_chain_space(v, limy-1, limz-4)
            plan = self.plan_chain_space(v, floor_height - 1, limz - 4)
            if plan is None:
                raise Exception(
                    'Not enough space for "' +
                    k +
                    '" impulse chain (increase Z size)' +
                    ' Code:uvwsso')
            impulse_chains_projects[k] = plan

        for k, v in self.repeat_chains.items():
            # required_x += 2
            required_x.append(2)
            # plan = self.plan_chain_space(v, limy-1, limz-4)
            plan = self.plan_chain_space(v, floor_height - 1, limz - 4)
            if plan is None:
                raise Exception(
                    'Not enough space for "' +
                    k +
                    '" repeating chain (increase Z size)' +
                    ' Code:ars5f6')
            repeat_chains_projects[k] = plan

        for k, v in self.dialogs.items():
            # required_x += 4
            required_x.append(4)
            # if not self.is_space_for_dialog(v,limy-1, limz-3):
            if not self.is_space_for_dialog(v, floor_height - 1, limz - 3):
                raise Exception(
                    'Not enough space for "' +
                    k +
                    '" dialog chain (increase Y or Z size)' +
                    ' Code:fgs2ir')

        if 4 > limx:
            raise Exception('Box to small (increase X size)' + ' Code:33o5l6')

        required_floors = 1
        curr_x = 0
        for i in required_x:
            if curr_x + i > limx:
                curr_x = i
                required_floors += 1
                if required_floors > lim_n_floors:
                    raise Exception('Box to small (you need more or biger '
                                    + 'floors)' + ' Code:zno26s')
            else:
                curr_x += i

        # Depth of placing states and chains
        chain_z = box.minz + 3
        state_z = box.minz

        # Calculating states positions
        state_positions = []
        for x in range(limx):
            for y in range(limy - 1):
                state_positions.append([x, y + 1])
        i = 0
        for k, v in self.parser.states.items():
            if self.parser.states[k] is None:
                self.parser.states[k] = [
                    state_positions[i][0] + box.minx,
                    state_positions[i][1] + box.miny,
                    state_z]
                i += 1

        # Calculationg command structures positions
        curr_x = 0
        curr_floor = 0
        for k, v in self.parser.impulse_chains.items():
            if curr_x + 2 > limx:
                curr_x = 0
                curr_floor += 1
            self.parser.impulse_chains[k]['position'] = [
                curr_x + box.minx,
                box.miny + (curr_floor * floor_height) + 1,
                chain_z]
            curr_x += 2

        for k, v in self.parser.repeat_chains.items():
            if curr_x + 2 > limx:
                curr_x = 0
                curr_floor += 1
            self.parser.repeat_chains[k]['position'] = [
                curr_x + box.minx,
                box.miny + (curr_floor * floor_height) + 1,
                chain_z]
            curr_x += 2

        curr_x += 1
        for k, v in self.parser.dialogs.items():
            if curr_x + 4 > limx:
                curr_x = 0
                curr_floor += 1
            self.parser.dialogs[k]['position'] = [
                curr_x + box.minx,
                box.miny + (curr_floor * floor_height) + 1,
                chain_z]
            curr_x += 4

        def build(level, floor_block):
            # zp, zm, up, skip_zp, skip_zm, skip_up
            for k, v in self.parser.states.items():
                pos = self.parser.states[k]
                Builder.place_block(pos[0], pos[1], pos[2],
                                    alphaMaterials[35, 0], level)  # Wool 0

            for k, v in self.parser.impulse_chains.items():
                pos = self.parser.impulse_chains[k]['position']
                Builder.place_block(pos[0], pos[1], pos[2],
                                    alphaMaterials[22, 0], level)
                i = 0
                cmd_source = self.parser.impulse_chains[k]['commands']
                cx, cy, cz = pos[0], pos[1], pos[2] + 1
                for move in impulse_chains_projects[k]:
                    cb_type = Builder.cb_impulse if (
                            i == 0) else Builder.cb_chain
                    # y_down, y_up, z_down, z_up, x_down, x_up
                    if move == Planner.zp:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.z_up,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cz += 1
                    elif move == Planner.zm:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.z_down,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cz -= 1
                    elif move == Planner.up:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.y_up,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cy += 1
                    elif move == Planner.skip_zp:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.z_up, "", False)
                        cz += 1
                    elif move == Planner.skip_zm:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.z_down, "", False)
                        cz -= 1
                    elif move == Planner.skip_up:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.y_up, "", False)
                        cy += 1
            for k, v in self.parser.repeat_chains.items():

                pos = self.parser.repeat_chains[k]['position']
                Builder.place_block(pos[0], pos[1], pos[2],
                                    alphaMaterials[22, 0], level)
                i = 0
                cmd_source = self.parser.repeat_chains[k]['commands']
                cx, cy, cz = pos[0], pos[1], pos[2] + 1
                for move in repeat_chains_projects[k]:
                    cb_type = Builder.cb_repeat if i == 0 else Builder.cb_chain
                    # y_down, y_up, z_down, z_up, x_down, x_up
                    if move == Planner.zp:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.z_up,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cz += 1
                    elif move == Planner.zm:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.z_down,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cz -= 1
                    elif move == Planner.up:
                        (command, is_conditional, is_new_dialog_chain,
                            customName) = \
                            self.parser.command_to_string(cmd_source[i])
                        Builder.place_cmdblock(
                            cx,
                            cy,
                            cz,
                            level,
                            cb_type,
                            Builder.y_up,
                            command,
                            is_conditional,
                            customName)
                        i += 1
                        cy += 1
                    elif move == Planner.skip_zp:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.z_up, "", False)
                        cz += 1
                    elif move == Planner.skip_zm:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.z_down, "", False)
                        cz -= 1
                    elif move == Planner.skip_up:
                        Builder.place_cmdblock(cx, cy, cz, level, cb_type,
                                               Builder.y_up, "", False)
                        cy += 1

            is_first = True
            for k, v in self.parser.dialogs.items():
                pos = self.parser.dialogs[k]['position']
                Builder.place_block(pos[0], pos[1], pos[2],
                                    alphaMaterials[22, 0], level)
                cx, cy, cz = pos[0], pos[1], pos[2]
                i = 0
                for command_elements in self.parser.dialogs[k]['commands']:
                    (command, is_conditional, is_new_dialog_chain,
                        customName) = \
                        self.parser.command_to_string(command_elements)
                    # Za pierwszym razem ten warunek jest zawsze spelniony
                    # ale i=0
                    if is_new_dialog_chain:
                        if i == 1:
                            # Pierwszy osdstep jest troche krotszy bo nie
                            # trzeba budowac calej struktury
                            cz += 2
                        elif i > 1:
                            cz += 4
                        i += 1
                        cy = pos[1]
                        is_first = True

                    if i == 1:  # Pierwszy rzadek
                        if is_first:
                            Builder.place_cmdblock(
                                cx - 1,
                                cy,
                                cz,
                                level,
                                Builder.cb_impulse,
                                Builder.y_up,
                                'setblock ~2 ~ ~2 air',
                                False)
                            is_first = False
                        cy += 1
                        Builder.place_cmdblock(
                            cx - 1,
                            cy,
                            cz,
                            level,
                            Builder.cb_chain,
                            Builder.y_up,
                            command,
                            is_conditional,
                            customName)
                    else:
                        def build_layer(x, y, z, level):
                            Builder.place_block(x, y, z,
                                                alphaMaterials[152, 0],
                                                level)  # redstone_block
                            Builder.place_block(
                                x + 1, y, z, alphaMaterials[152, 0],
                                level)  # redstone_block
                            Builder.place_block(
                                x, y, z + 1, alphaMaterials[55, 15],
                                level)  # redstone_dust
                            Builder.place_hooper(
                                x + 1, y, z + 1, level, [10], Builder.z_up,
                                True)  # hooper disabled south
                            Builder.place_comparator(
                                x, y, z + 2, level, Builder.x_up, 0,
                                True)  # comparator
                            Builder.place_hooper(x + 1, y, z + 2, level,
                                                 [64, 64, 64, 64, 54],
                                                 Builder.z_up, True)  # hooper
                        if is_first:
                            build_layer(cx, cy, cz, level)
                            Builder.place_block(
                                cx, cy + 1, cz + 1,
                                floor_block, level)  # floor_block
                            Builder.place_block(
                                cx + 1, cy + 1, cz + 1,
                                floor_block, level)  # floor_block
                            Builder.place_block(
                                cx, cy + 1, cz + 2,
                                floor_block, level)  # floor_block
                            Builder.place_block(
                                cx + 1, cy + 1, cz + 2,
                                floor_block, level)  # floor_block
                            build_layer(cx, cy + 2, cz, level)
                            Builder.place_cmdblock(
                                cx - 1,
                                cy,
                                cz + 2,
                                level,
                                Builder.cb_impulse,
                                Builder.y_up,
                                'clone ~1 ~2 ~-2 ~2 ~2 ~ ~1 ~ ~-2',
                                False)
                            cy += 1
                            Builder.place_cmdblock(
                                cx - 1,
                                cy,
                                cz + 2,
                                level,
                                Builder.cb_chain,
                                Builder.y_up,
                                'setblock ~2 ~-1 ~2 air',
                                False)
                            is_first = False
                        cy += 1
                        Builder.place_cmdblock(
                            cx - 1,
                            cy,
                            cz + 2,
                            level,
                            Builder.cb_chain,
                            Builder.y_up,
                            command,
                            is_conditional,
                            customName)

        for x in range(box.minx, box.maxx):
            for y in range(box.miny, box.maxy):
                for z in range(box.minz, box.maxz):
                    if (((y - box.miny) % floor_height ==
                         0 and box.minz + 2 <= z) or (y == box.miny)):
                        Builder.place_block(x, y, z, floor_block, level)
                    else:
                        Builder.place_block(x, y, z, alphaMaterials[0, 0],
                                            level)

        build(level, floor_block)

    def get_bp_path(self, world_path):
        bpuuid = self.parser.behavior_pack_uuid
        funcpath = self.parser.functions_path

        if not isinstance(bpuuid, str) and not isinstance(bpuuid, unicode):
            raise Exception('Behavior pack UUID in project file must '
                            + 'be a string. Code:owfuou')
        if not isinstance(funcpath, str) and not isinstance(funcpath, unicode):
            raise Exception('Path to functions in project file must be a '
                            + 'string. Code:7u4lpj')
        if not os.path.isdir(funcpath):
            raise Exception('Path to functions doesn\'t exists. Code:xp833b')

        # FIND BEHAVIORPACK PATH
        def serch(root, uuid):
            if os.path.isdir(root):
                root = [os.path.join(root, i) for i in os.listdir(root) if
                        os.path.isdir(os.path.join(root, i))]
                for bp_path in root:
                    manifest_file_path = os.path.join(bp_path, 'manifest.json')
                    if os.path.isfile(manifest_file_path):
                        try:
                            with open(manifest_file_path) as manifest_file:
                                project_data = json.load(manifest_file)
                                if 'header' not in project_data:
                                    continue
                                if 'uuid' not in project_data['header']:
                                    continue
                                if project_data['header']['uuid'] == uuid:
                                    return os.path.join(bp_path, 'functions')
                                else:
                                    continue
                        except BaseException:
                            continue
            return None
        bp_funcpath = serch(os.path.join(world_path, 'behavior_packs'), bpuuid)
        if bp_funcpath is None:
            dev_bp_path = os.path.dirname(world_path)  # minecraftWorlds
            if not dev_bp_path.endswith('minecraftWorlds'):
                raise Exception('Behaviorpack with UUID ' + bpuuid
                                + ' doesn\'t exist. Code:u30m8n')

            dev_bp_path = os.path.dirname(dev_bp_path)  # com.mojang
            if not dev_bp_path.endswith('com.mojang'):
                raise Exception('Behaviorpack with UUID ' + bpuuid
                                + ' doesn\'t exist. Code:nz8rj9')
            dev_bp_path = os.path.join(
                dev_bp_path,
                'development_behavior_packs')  # development_behavior_packs
            bp_funcpath = serch(dev_bp_path, bpuuid)
        if bp_funcpath is None:
            raise Exception('Behaviorpack with UUID ' + bpuuid
                            + ' doesn\'t exist. Code:47u2aq')
        # BEHAVIORPACK FUNCTIONS PATH IS KNOWN ( bp_funcpath )
        return bp_funcpath

    def create_functions(self, world_path):
        bpuuid = self.parser.behavior_pack_uuid
        funcpath = self.parser.functions_path
        if bpuuid is None or funcpath is None:
            return None  # Nothing to copy

        bp_funcpath = self.get_bp_path(world_path)

        history = None
        # Find files edited with external progrmas
        try:
            with open(os.path.join(funcpath,
                                   'brfunction_last_edit.json'), 'r') as f:
                history = json.load(f)
        except IOError as e:

            # Pass only if error is: "No such file or directory"
            if e.errno != errno.ENOENT:
                raise e

        if history is not None:
            # k - file path, v - object with data describing the file
            for k, v in history.items():
                try:
                    with open(k, 'r') as f:
                        hasher = hashlib.md5()
                        hasher.update(f.read())
                        if v['md5'] != hasher.hexdigest():
                            raise Exception(
                                'File ' +
                                k +
                                ' has been modified with external ' +
                                'application. Delete the file and run ' +
                                'filter again if you are sure that you want' +
                                ' apply changes to it. Code:cs4kwg')
                    try:
                        os.remove(k)
                    except OSError:
                        pass
                except IOError as e:

                    # Pass only if error is: "No such file or directory"
                    if e.errno != errno.ENOENT:
                        raise e

        # Edit files
        cut = len(funcpath) + 1
        new_history = {}
        # source - source file path, v - dictionary with list of commands form
        # the file in v['commands']
        for source, v in self.parser.functions.items():
            target = os.path.join(bp_funcpath, source[cut:])
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))

            file_content = ''
            with open(target, 'w') as f:
                for line in v['commands']:
                    file_content += self.parser.command_to_string(line)[
                        0] + '\n'
                f.write(file_content)
                hasher = hashlib.md5()
                hasher.update(file_content)
                new_history[target] = {'md5': hasher.hexdigest()}

        # Save history of edits
        with open(os.path.join(funcpath, 'brfunction_last_edit.json'),
                  'w') as f:
            json.dump(new_history, f)

    def analyse(self):
        # Create list of lengths of conditional chains needed for impulse
        # chains
        for name, chain in self.parser.impulse_chains.items():
            curr_chain = 0
            # last_conditional = True
            self.impulse_chains[name] = []
            for command in chain['commands']:
                if command[0].type == Token.conditional:
                    curr_chain += 1
                else:
                    if curr_chain > 0:  # If not first
                        self.impulse_chains[name].append(curr_chain)
                    curr_chain = 1
            self.impulse_chains[name].append(curr_chain)
        # Create list of lengths of conditional chains needed for repeat chains
        for name, chain in self.parser.repeat_chains.items():
            curr_chain = 0
            # last_conditional = True
            self.repeat_chains[name] = []
            for command in chain['commands']:
                if command[0].type == Token.conditional:
                    curr_chain += 1
                else:
                    if curr_chain > 0:  # If not first
                        self.repeat_chains[name].append(curr_chain)
                    curr_chain = 1
            self.repeat_chains[name].append(curr_chain)
        # Create list of lengths of conditional chains and modules needed for
        # dialogs
        for name, chain in self.parser.dialogs.items():
            curr_chain = 0
            # last_conditional = True
            curr_module = None

            self.dialogs[name] = []
            for command in chain['commands']:
                if command[0].type == Token.new_dialog_chain:
                    if curr_module is not None:  # If not first
                        self.dialogs[name].append(curr_module)
                        curr_module.append(curr_chain)
                    curr_module = []
                    curr_chain = 1
                elif command[0].type == Token.conditional:
                    curr_chain += 1
                else:
                    curr_module.append(curr_chain)
                    curr_chain = 1
            curr_module.append(curr_chain)
            self.dialogs[name].append(curr_module)

        self.states = 0  # Get number of states with unknown position
        for k, v in self.parser.states.items():
            if v is not None:
                self.states += 1


# ##############   FILTER CODE   ##############################################
displayName = "Nusiq's brfunctions - v1.5.2"

inputs = (
    ("File path", "file-open"),
    ("Floor block", alphaMaterials[169, 0]),  # Sea lantern
    ("Floor height", (255, 1, 255))
)


def perform(level, box, options):
    os.system('cls')
    parser = Parser()
    parser.parse_file(str(options["File path"]))
    planner = Planner(parser)
    floor_block = options["Floor block"]

    mybox = parser.box if parser.box is not None else box
    myFloorHeight = parser.floor_height if (
            parser.floor_height is not None) else options["Floor height"]

    planner.plan_and_build(mybox, level, floor_block, myFloorHeight)
    planner.create_functions(level.filename)
