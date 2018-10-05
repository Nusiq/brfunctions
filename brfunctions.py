#https://github.com/Nusiq/brfunctions
from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_Float
from pymclevel import TAG_String
from pymclevel import TAG_Long
from pymclevel import TAG_Int_Array
from pymclevel import alphaMaterials
import json
import string
import os



class Builder:
	y_down, y_up, z_down, z_up, x_down, x_up = range(6)
	cb_impulse, cb_repeat, cb_chain = range(3)

	def place_block(x, y, z, block, level):
		chunk = level.getChunk(x/16, z/16)
		level.setBlockAt(x, y, z, block.ID)
		level.setBlockDataAt(x, y, z, block.blockData)
		chunk.dirty = True
	place_block = staticmethod(place_block)
	
	def place_comparator(x,y,z, level, direction, signal, compare):
		signal = 0 if signal < 0 else (15 if signal > 15 else signal)
		comparator_directions = {Builder.z_up:0,Builder.x_down:1,Builder.z_down:2,Builder.x_up:3}
		
		comparator = TAG_Compound()
		comparator["OutputSignal"]= TAG_Int(signal)
		comparator["id"] = TAG_String(u'Comparator')
		comparator["isMoveable"] = TAG_Byte(1)
		comparator["x"] = TAG_Int(x)
		comparator["y"] = TAG_Int(y)
		comparator["z"] = TAG_Int(z)
		
		chunk = level.getChunk(x/16, z/16)
		#Usuwanie istniejacych na tym miejscu tileEntities jesli takie istnieja
		te = level.tileEntityAt(x, y, z)
		if te != None:
			chunk.TileEntities.remove(te)
		chunk.TileEntities.append(comparator)
		chunk.dirty = True
		direction = comparator_directions[direction]
		if signal > 0:
			direction += 8
		if compare == False:
			direction += 4
		#Wywolanie funkcji wewnatrz drugiej funkcji
		Builder.place_block(x, y, z, alphaMaterials[149, direction], level)#Zwroc uwage na odwolanie sie do odpowiedniego elementu alphaMaterials
	place_comparator = staticmethod(place_comparator)
	
	
	def place_cmdblock(x, y, z, level, cmdBlockType, direction, command, conditional):
		cb_types = {Builder.cb_impulse:137, Builder.cb_chain:189, Builder.cb_repeat:188}
		cb_directions = {Builder.y_down:0,Builder.y_up:1,Builder.z_down:2,Builder.z_up:3,Builder.x_down:4,Builder.x_up:5}
		
		tileCB = TAG_Compound()
		tileCB["Command"] = TAG_String(command)
		tileCB["CustomName"] = TAG_String(u'')
		tileCB["LPCommandMode"] = TAG_Int(0)
		tileCB["LPCondionalMode"] = TAG_Byte(0)
		tileCB["LPRedstoneMode"] = TAG_Byte(0)
		tileCB["LastExecution"] = TAG_Long(0L)
		tileCB["LastOutput"] = TAG_String(u'OUTPUT')
		tileCB["LastOutputParams"] = TAG_List([TAG_String(u'1'),TAG_String(u'2'),TAG_String(u'3')])
		tileCB["SuccessCount"] = TAG_Int(0)
		tileCB["TrackOutput"] = TAG_Byte(1)
		tileCB["Version"] = TAG_Int(8)
		tileCB["auto"] = TAG_Byte(1 if cmdBlockType == Builder.cb_chain else 0)
		tileCB["conditionMet"] = TAG_Byte(0)
		tileCB["id"] = TAG_String(u'CommandBlock')
		tileCB["isMovable"] = TAG_Byte(1)
		tileCB["powered"] = TAG_Byte(0)
		tileCB["x"] = TAG_Int(x)
		tileCB["y"] = TAG_Int(y)
		tileCB["z"] = TAG_Int(z)
		chunk = level.getChunk(x/16, z/16)
		#Usuwanie istniejacych na tym miejscu tileEntities jesli takie istnieja
		te = level.tileEntityAt(x, y, z)
		if te != None:
			chunk.TileEntities.remove(te)
			
		chunk.TileEntities.append(tileCB)
		chunk.dirty = True
		
		direction =  cb_directions[direction]
		if conditional == True:
			direction += 8 
		#Wywolanie funkcji wewnatrz drugiej funkcji
		Builder.place_block(x, y, z, alphaMaterials[cb_types[cmdBlockType], direction], level)#Zwroc uwage na odwolanie sie do odpowiedniego elementu alphaMaterials
	place_cmdblock = staticmethod(place_cmdblock)

	
	def place_hooper(x, y, z, level, items,direction, disabled):
		hopper_directions = {Builder.y_down:0,Builder.z_down:2,Builder.z_up:3,Builder.x_down:4,Builder.x_up:5}
	
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
		chunk = level.getChunk(x/16, z/16)
		#Usuwanie istniejacych na tym miejscu tileEntities jesli takie istnieja
		te = level.tileEntityAt(x, y, z)
		if te != None:
			chunk.TileEntities.remove(te)
			
		chunk.TileEntities.append(hooper)
		chunk.dirty = True
		direction = hopper_directions[direction]
		if disabled == True:
			direction += 8 
		#Wywolanie funkcji wewnatrz drugiej funkcji
		Builder.place_block(x, y, z, alphaMaterials[154, direction], level)#Zwroc uwage na odwolanie sie do odpowiedniego elementu alphaMaterials
	place_hooper = staticmethod(place_hooper)
	
	
class Token:
	state, create_state, position, create_position, custom, create_custom, impulse, create_impulse, repeat, create_repeat, dialog, create_dialog, comment, conditional, new_dialog_chain, command,new_line = range(17)
	def __init__(self, type=None, value=None, name=None, line=None, file_name=None):
		self.type = type
		self.value = value
		self.name = name
		self.file_name = file_name
		self.line = line
	
	def __str__(self):
		types = ['state', 'create_state', 'position', 'create_position', 'custom', 'create_custom', 'impulse', 'create_impulse', 'repeat', 'create_repeat', 'dialog', 'create_dialog', 'comment', 'conditional', 'new_dialog_chain','command','new_line']
		return str({'type':types[self.type],'value':self.value,'name':self.name})
		
	def __repr__(self):
		types = ['state', 'create_state', 'position', 'create_position', 'custom', 'create_custom', 'impulse', 'create_impulse', 'repeat', 'create_repeat', 'dialog', 'create_dialog', 'comment', 'conditional', 'new_dialog_chain','command','new_line']
		return str({'type':types[self.type],'value':self.value,'name':self.name})
	
class Parser:
	state_blocks = ('wool 0', 'wool 1', 'wool 2', 'wool 3', 'wool 4', 'wool 5', 'wool 6',
	'wool 7', 'wool 8', 'wool 9', 'wool 10', 'wool 11', 'wool 12', 'wool 13', 'wool 14', 'wool 15',
	'stained_hardened_clay 0', 'stained_hardened_clay 1', 'stained_hardened_clay 2',
	'stained_hardened_clay 3', 'stained_hardened_clay 4', 'stained_hardened_clay 5',
	'stained_hardened_clay 6', 'stained_hardened_clay 7', 'stained_hardened_clay 8',
	'stained_hardened_clay 9', 'stained_hardened_clay 10', 'stained_hardened_clay 11',
	'stained_hardened_clay 12', 'stained_hardened_clay 13', 'stained_hardened_clay 14',
	'stained_hardened_clay 15')
	off_on = ('lapis_block 0','redstone_block 0')
	def __init__(self):
		self.states = {}
		self.positions = {}
		self.custom_values = {}
		self.impulse_chains = {}
		self.repeat_chains = {}
		self.dialogs = {}
		self.tokens = []
	def parse_coordinates(command, count=3,allow_fraction=True):
		def parse_coordinate(command,allow_fraction=True):
			start, type,sign, integer, fraction = range(5)
			state=start
			i=0
			success = False
			for c in command:
				if state==start:
					if c == '-':
						i+=1
						state=sign
					elif c == '.' and allow_fraction:
						i+=1
						state=fraction
					elif c in string.digits:
						i+=1
						state=integer
						success = True
					else:
						break
				elif state==type:
					if c == '-':
						i+=1
						state=sign
					elif c == '.':#Jesli typ nie jest globalny to dozwolone sa ulamki
						i+=1
						state=fraction
					elif c in string.digits:
						i+=1
						state=integer
						success = True
					else:
						break
				elif state==sign:
					if c == '.' and allow_fraction:#Jesli typ nie jest globalny to dozwolone sa ulamki
						i+=1
						state=fraction
					elif c in string.digits:
						i+=1
						state=integer
						success = True
					else:
						i-=1
						break
				elif state==integer:
					if c == '.'  and allow_fraction:
						i+=1
						state=fraction
					elif c in string.digits:
						i+=1
					else:
						break
				elif state==fraction:
					if c in string.digits:
						success = True
						i+=1
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
			sep, val, success = parse_coordinate(command[i:],allow_fraction=allow_fraction)
			if not success:
				return i, info, False, "Unexpected character"
			
			info.append(val)
			i += sep
			if n < count-1:
				if i >= len(command):
					return i, info, False, "Unexpected end of vector."
				if command[i] == ' ':
					i += 1
				else:
					break
		return i, info, True,''
	parse_coordinates = staticmethod(parse_coordinates)
	
	def cut_word(command,separators=' \n\r\t',escape_characters=None,allowed_chars=None):
		length = 0
		escape = False
		for c in command:
			length += 1
			if ( c in separators ) and ( escape == False ):
				return length-1, True
			if allowed_chars != None:
				if c not in allowed_chars:
					return length-1, False
			if escape_characters != None:
				if c in escape_characters:
					escape = True
				else:
					escape = False
		return length, True
	cut_word = staticmethod(cut_word)
	
	def parse(input,input_line_index,input_file_name):
		input = input.strip()
		tokens = []
		if input.startswith('#') or input == '':
			return tokens
		start, start2, command, special, end, comment =  range(6)
		#start2 - after conditional or new_dialog_chain
		tokens = []
		state = start
		input_len = len(input)
		i = 0
		consumed_input = 0
		while True:
			if state == start:#Skip whitespaces and go to command, special or comment
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
						i+=1
						tokens.append(Token(Token.new_dialog_chain, None, None, input_line_index, input_file_name))
						consumed_input = i
						for c in input[consumed_input:]:
							if c in ' \t':
								i+=1
								consumed_input = 1
							else:
								break
					elif input[i] == ">":
						i+=1
						tokens.append(Token(Token.conditional, None, None, input_line_index, input_file_name))
						consumed_input = i
						for c in input[consumed_input:]:
							if c in ' \t':
								i+=1
								consumed_input = 1
							else:
								break
					else:
						state = command
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
					else:
						state = command
						consumed_input = i
				else:
					return tokens
			elif state == command:
				length, _ = Parser.cut_word(input[i:],separators='`#',escape_characters='\\',allowed_chars=None)
				i += length
				if i >= input_len:
					tokens.append(Token(Token.command, input[consumed_input:i], None, input_line_index, input_file_name))
					return tokens
				if input[i] == '`':
					tokens.append(Token(Token.command, input[consumed_input:i], None, input_line_index, input_file_name))
					i+=1
					consumed_input = i
					state = special
				elif input[i] == '#':
					tokens.append(Token(Token.command, input[consumed_input:i], None, input_line_index, input_file_name))
					i+=1
					consumed_input = i
					state = comment	
			elif state == special:
				
				if input[i] == '/':
					i+=1
					if i >= input_len:
						raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
					if input[i] == 's':#state
						if input[i:].startswith('state'):
							i += len('state')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '(':
							i+=1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							length, position, success, error = Parser.parse_coordinates(input[i:], count=3,allow_fraction=False)
							if not success: raise Exception(error+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += length
							if not success: raise Exception(error+' at line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.create_state, position, name,input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.create_state, position, name, input_line_index, input_file_name))
								consumed_input = i
								state = end	
						else:
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.create_state, None,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.create_state, None,name, input_line_index, input_file_name))
								consumed_input = i
								state = end
					elif input[i] == 'p':#position
						if input[i:].startswith('position'):
							i += len('position')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '(': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, position, success, error = Parser.parse_coordinates(input[i:], count=6,allow_fraction=False)
						if not success:
							length, position, success, error = Parser.parse_coordinates(input[i:], count=3,allow_fraction=False)
						if not success: raise Exception(error+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += length
						if not success: raise Exception(error+' at line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.create_position, position, name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.create_position, position, name, input_line_index, input_file_name))
							consumed_input = i
							state = end	
					elif input[i] == 'c':#custom
						if input[i:].startswith('custom'):
							i += len('custom')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '(': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						
						length, _ = Parser.cut_word(input[i:],separators=')',escape_characters='\\',allowed_chars=None)
						value = input[i:i+length]
						i += length
						if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.create_custom, value, name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.create_custom, value, name, input_line_index, input_file_name))
							consumed_input = i
							state = end	
					elif input[i] == 'i':#impulse
						if input[i:].startswith('impulse'):
							i += len('impulse')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.create_impulse, None, name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.create_impulse, None, name, input_line_index, input_file_name))
							consumed_input = i
							state = end	
					elif input[i] == 'r':#repeat
						if input[i:].startswith('repeat'):
							i += len('repeat')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.create_repeat, None, name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.create_repeat, None, name, input_line_index, input_file_name))
							consumed_input = i
							state = end	
					elif input[i] == 'd':#dialog
						if input[i:].startswith('dialog'):
							i += len('dialog')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.create_dialog, None, name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.create_dialog, None, name, input_line_index, input_file_name))
							consumed_input = i
							state = end	
					else:
						raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
				else:
					if input[i] == 's':#state
						if input[i:].startswith('state'):
							i += len('state')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '(': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						
						length, _ = Parser.cut_word(input[i:],separators=')',escape_characters='\\',allowed_chars=string.digits)
						value = int(input[i:i+length])
						i += length
						if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							#if value.strip() != '':
							tokens.append(Token(Token.state, value,name, input_line_index, input_file_name))
							return tokens
						else:
							tokens.append(Token(Token.state, value,name, input_line_index, input_file_name))
							consumed_input = i
					elif input[i] == 'p':#position
						if input[i:].startswith('position'):
							i += len('position')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						position_type = 'normal'
						if input[i] == '@':
							position_type = 'selector'
							i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.position, position_type, name, input_line_index, input_file_name))
							return tokens
						else:
							consumed_input = i
							tokens.append(Token(Token.position, position_type, name, input_line_index, input_file_name))
					elif input[i] == 'c':#custom
						if input[i:].startswith('custom'):
							i += len('custom')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
						i += 1
						if i >= input_len:
							tokens.append(Token(Token.custom, None, name, input_line_index, input_file_name))
							return tokens
						else:
							consumed_input = i
							tokens.append(Token(Token.custom, None, name, input_line_index, input_file_name))
					elif input[i] == 'i':#impulse
						if input[i:].startswith('impulse'):
							i += len('impulse')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '(':
							i+=1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] not in '01': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							value = int(input[i])
							i += 1
							if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.impulse, value,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.impulse, value,name, input_line_index, input_file_name))
								consumed_input = i
						else:
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.impulse, 1, name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.impulse, 1, name, input_line_index, input_file_name))
								consumed_input = i
					elif input[i] == 'r':#repeat
						if input[i:].startswith('repeat'):
							i += len('repeat')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '(':
							i+=1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] not in '01': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							value = int(input[i])
							i += 1
							if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.repeat, value,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.repeat, value,name, input_line_index, input_file_name))
								consumed_input = i
						else:
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.repeat, 1,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.repeat, 1,name, input_line_index, input_file_name))
								consumed_input = i
					elif input[i] == 'd':#dialog
						if input[i:].startswith('dialog'):
							i += len('dialog')
						else:
							i += 1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '[': i+=1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						length, _ = Parser.cut_word(input[i:],separators=']',escape_characters='\\',allowed_chars=None)
						name = input[i:length+i]
						i += length+1
						if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
						if input[i] == '(':
							i+=1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] not in '01': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							value = int(input[i])
							i += 1
							if input[i] != ')': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len: raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.dialog, value,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.dialog, value,name, input_line_index, input_file_name))
								consumed_input = i
						else:
							if input[i] != '`': raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
							i += 1
							if i >= input_len:
								tokens.append(Token(Token.dialog, 1,name, input_line_index, input_file_name))
								return tokens
							else:
								tokens.append(Token(Token.dialog, 1,name, input_line_index, input_file_name))
								consumed_input = i
					else:
						raise Exception('Unexpected character'+' at line '+str(input_line_index)+' in file '+input_file_name)
					

					if input[i] == '#':
						consumed_input = i
						state = comment
					elif input[i] == '`':
						consumed_input = i
						state = special
					else:
						consumed_input = i
						state = command
			elif state == end:#Skip whitespaces and go to comment
				if i >= input_len:
					return tokens
				elif input[i] == '#':
					consumed_input = i
					state = comment	
				elif input[i] in ' \t':
					consumed_input = i
				else:
					raise Exception('Unexpected symbol'+' at line '+str(input_line_index)+' in file '+input_file_name)
				i += 1
			elif state == comment:#Append comment to tokens and return
				i += 1
				if i >= input_len:
					tokens.append(Token(Token.comment, input[consumed_input:i] ,None, input_line_index, input_file_name))
					return tokens
				
				
			if i >= input_len:
				raise Exception('Unexpected end of line '+str(input_line_index)+' in file '+input_file_name)
	parse = staticmethod(parse)			
				
	def parse_file(self, file_name):
		
		use_as_project = True
		files_list = []
		try:
			with open(file_name) as projectFile:
				files_list = json.load(projectFile)	
		except:
			use_as_project = False
		if isinstance(files_list, list) == False:
			raise Exception('Project file needs to be JSON list of directories. '+type(files_list))
		if use_as_project:
			path = os.path.split(file_name)[0]
			for item_file_name in files_list:
				full_item_file_name = path+'/'+item_file_name
				with open(full_item_file_name) as f:
					line_index = 1
					for l in f:
						p = Parser.parse(l,line_index,file_name)
						self.tokens.extend(p)
						self.tokens.append(Token(Token.new_line, None, None, line_index, full_item_file_name))
						line_index += 1	
		else:
			with open(file_name) as f:
				line_index = 1
				for l in f:
					p = Parser.parse(l,line_index,file_name)
					self.tokens.extend(p)
					self.tokens.append(Token(Token.new_line, None, None, line_index, file_name))
					line_index += 1
		#raise Exception('YOU SHELL NOT PASS')
		#expect_new_line  = [Token.comment]
		#tape, value, name
		expect_comment_or_new_line = (Token.create_state,Token.create_position,Token.create_custom,Token.create_impulse,Token.create_repeat,Token.create_dialog)
		code_tokens = (Token.state,Token.position,Token.custom,Token.impulse,Token.repeat,Token.dialog,Token.command)
		lastToken = Token.new_line
		line = 1
		curr_command_line = []
		is_first = True
		last_command_group = None
		last_command_group_type = None
		new_dialog_chain_started = False
		for t in self.tokens:##################DEFINITIONS
			if t.type == Token.create_state:
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_state" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.states:
					raise Exception('State '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				self.states[t.name] = t.value
			elif t.type == Token.create_position:
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_position" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.positions:
					raise Exception('Position '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				self.positions[t.name] = t.value
			elif t.type == Token.create_custom:
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_custom" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.custom_values:
					raise Exception('Custom value '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				self.custom_values[t.name] = t.value
			elif t.type == Token.create_impulse:#IMPULSE CHAIN
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_impulse" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.impulse_chains:
					raise Exception('Impulse chain '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				self.impulse_chains[t.name] = {'position':t.value, 'commands':[]}				
				last_command_group = t
				is_first = True
			elif t.type == Token.create_repeat:#REPEATING CHAIN
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_repeat" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.repeat_chains:
					raise Exception('Repeating chain '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				self.repeat_chains[t.name] = {'position':t.value, 'commands':[]}
				last_command_group = t
				is_first = True
			elif t.type == Token.create_dialog:#DIALOG CHAIN
				if lastToken != Token.new_line:
					raise Exception('Unexpected "create_dialog" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name in self.dialogs:
					raise Exception('Dialog '+t.name+' is declared more than one time (line '+str(t.line)+' in file '+t.file_name+')')
				new_dialog_chain_started = False
				self.dialogs[t.name] = {'position':t.value, 'commands':[]}				
				last_command_group = t
				is_first = True
			elif t.type in code_tokens:
				if last_command_group == None:
					raise Exception('Unexpected minecraft command before starting command chain token at line '+str(t.line)+' in file '+t.file_name)
				if last_command_group.type == Token.create_dialog and new_dialog_chain_started == False:
					raise Exception('Unexpected minecraft command before starting new dialog command chain (line '+str(t.line)+' in file '+t.file_name+')')
				curr_command_line.append(t)
				is_first = False
			elif t.type == Token.new_dialog_chain:
				new_dialog_chain_started = True
				curr_command_line.append(t)
				is_first = True
			elif t.type == Token.conditional:
				if is_first:
					raise Exception('First command in chain cannot be conditional (line '+str(t.line)+' in file '+t.file_name+')')
				curr_command_line.append(t)
			elif t.type == Token.new_line:
				add_to_chain = True
				if len(curr_command_line) == 1:
					if curr_command_line[0].type == Token.command:
						if curr_command_line[0].value.strip() == '':
							add_to_chain = False
				if len(curr_command_line) == 0:
					add_to_chain = False
				if add_to_chain and last_command_group != None:
					if last_command_group.type == Token.create_impulse:
						self.impulse_chains[last_command_group.name]['commands'].append(curr_command_line)
					elif last_command_group.type == Token.create_repeat:
						self.repeat_chains[last_command_group.name]['commands'].append(curr_command_line)
					elif last_command_group.type == Token.create_dialog:
						self.dialogs[last_command_group.name]['commands'].append(curr_command_line)
				curr_command_line = []
				line+=1
			lastToken = t.type
		
		lastToken = Token.new_line
		line = 1
		for t in self.tokens:###############USING SAVED DATA
			if t.type == Token.state:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "state" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.states:
					raise Exception('Trying to refer to state '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')
			elif t.type == Token.position:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "position" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.positions:
					raise Exception('Trying to refer to position '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')
			elif t.type == Token.custom:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "custom" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.custom_values:
					raise Exception('Trying to refer to custom value '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')
			elif t.type == Token.impulse:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "impulse" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.impulse_chains:
					raise Exception('Trying to refer to impulse chain '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')
			elif t.type == Token.repeat:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "repeat" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.repeat_chains:
					raise Exception('Trying to refer to repeating chain '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')
			elif t.type == Token.dialog:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "dialog" token at line'+str(t.line)+' in file '+t.file_name)
				if t.name not in self.dialogs:
					raise Exception('Trying to refer to dialog '+t.name+' but it has on definition (line '+str(t.line)+' in file '+t.file_name+')')	
			#elif t.type == Token.comment:
			#	pass
			elif t.type == Token.command:
				if lastToken in expect_comment_or_new_line:
					raise Exception('Unexpected "command" token at line'+str(t.line)+' in file '+t.file_name)
			elif t.type == Token.conditional:
				if lastToken != Token.new_line:
					raise Exception('Unexpected "conditional" token at line'+str(t.line)+' in file '+t.file_name)
			elif t.type == Token.new_line:
				line += 1
			lastToken = t.type
	
	def command_to_string(self,command_elements):
		is_new_dialog_chain = False
		is_conditional = False
		command = ""
		for element in command_elements:
			if element.type == Token.state:
				command = command + ' '.join([str(i) for i in self.states[element.name]])+' '+Parser.state_blocks[element.value]
			elif element.type == Token.position:
				if element.value == 'selector':
					positions = self.positions[element.name]
					if len(positions) == 6:
						command = command +'x='+str(positions[0])+',y='+str(positions[1])+',z='+str(positions[2])+',dx='+str(positions[3]-positions[0])+',dy='+str(positions[4]-positions[1])+',dz='+str(positions[5]-positions[2])
					else:#3
						command = command +'x='+str(positions[0])+',y='+str(positions[1])+',z='+str(positions[2])
				else:
					command = command + ' '.join([str(i) for i in self.positions[element.name]])
			elif element.type == Token.custom:
				command  += self.custom_values[element.name]
			elif element.type == Token.impulse:
				command = command + ' '.join([str(i) for i in self.impulse_chains[element.name]['position']])+' '+Parser.off_on[element.value]
			elif element.type == Token.repeat:
				command = command + ' '.join([str(i) for i in self.repeat_chains[element.name]['position']])+' '+Parser.off_on[element.value]
			elif element.type == Token.dialog:
				command = command + ' '.join([str(i) for i in self.dialogs[element.name]['position']])+' '+Parser.off_on[element.value]
			elif element.type == Token.conditional:
				is_conditional = True
			elif element.type == Token.new_dialog_chain:
				is_new_dialog_chain = True
			elif element.type == Token.command:
				command += element.value
		return command, is_conditional, is_new_dialog_chain
		
class Planner:
	zp, zm, up, skip_zp, skip_zm, skip_up = 'zp', 'zm', 'up', 'skip_zp', 'skip_zm', 'skip_up'
	def __init__(self,parser):
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
		if max(chain_lengths) > lim_z-1:#Cannot fit the longest conditional chain
			return None
		def curve(new_x, new_y, new_z, direction):
			if direction == plus or direction == plus_up:
				while True:
					if new_z == lim_z-1:
						plan.append(Planner.skip_up)
						new_y += 1
						break
					elif new_z < lim_z-1:
						plan.append(Planner.skip_zp)
						new_z += 1
					else:
						raise Exception('Planner Error')
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
						raise Exception('Planner Error')
			if direction == plus or direction == plus_up:
				direction = minus
			elif direction == minus or direction == minus_up:
				direction = plus
			
			return new_x, new_y, new_z, direction
		def add_instructions(new_x, new_y, new_z,conditional_len, new_direction):
			new_plan = []
			success = False
			if conditional_len == 1:
				if  new_direction == plus_up:
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
					if new_z == lim_z-1:
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
					if new_z <= lim_z-1:
						success = True
					if new_z == lim_z-1:
						new_direction = plus_up
						
				elif new_direction == minus:
					new_z -= conditional_len
					for i in range(conditional_len):
						new_plan.append(Planner.zm)
					if new_z >= 0:
						success = True
					if new_z == 0:
						new_direction = minus_up
			return new_x,new_y, new_z,  new_plan, new_direction,success
		
		for curr_len in chain_lengths:
			new_x,new_y, new_z,  new_plan, new_direction,success = add_instructions(cursor_x,cursor_y,cursor_z,curr_len, direction)
			if not success:
				cursor_x,cursor_y,cursor_z, direction= curve(cursor_x,cursor_y,cursor_z, direction)
				new_x,new_y, new_z,  new_plan, new_direction,success = add_instructions(cursor_x,cursor_y,cursor_z,curr_len, direction)
				if not success:
					raise Exception('Planner Error')
			cursor_x,cursor_y,cursor_z = new_x,new_y, new_z
			direction = new_direction
			plan.extend(new_plan)
		if cursor_y >= lim_y-1:
			return None
		return plan
	
	def is_space_for_dialog(self,chain_lengths,lim_y,lim_z):		
		lengths = [sum(i) for i in chain_lengths]
		required_y = max(lengths)+2
		if required_y > lim_y:
			return False
		
		required_z = 2 + (len(chain_lengths)-1 if len(chain_lengths)>0 else 0)*4
		if required_z > lim_z:
			return False		
		return True
		

				
				
	def plan_and_build(self,box, level, floor_block):
		limx = box.maxx-box.minx
		limy = box.maxy-box.miny
		limz = box.maxz-box.minz
		
		impulse_chains_projects = {}
		repeat_chains_projects = {}
		
		required_x = 0
		
		
		if limx*(limy-1) < self.states:
			raise Exception('Not enough space for states (increase X size)' )
		
		for k,v in self.impulse_chains.items():
			required_x += 2
			plan = self.plan_chain_space(v, limy-1, limz-4)
			if plan == None:
				raise Exception('Not enough space for "'+k+'" impulse chain (increase Z size)')
			impulse_chains_projects[k] = plan
			
		for k,v in self.repeat_chains.items():
			required_x += 2
			plan = self.plan_chain_space(v, limy-1, limz-4)
			if plan == None:
				raise Exception('Not enough space for "'+k+'" repeating chain (increase Z size)')
			repeat_chains_projects[k] = plan
			
		for k,v in self.dialogs.items():
			required_x += 4
			if not self.is_space_for_dialog(v,limy-1, limz-3):
				raise Exception('Not enough space for "'+k+'" dialog chain (increase Y or Z size)')
			
		if required_x > limx:
			raise Exception('Box to small (increase Z size)')
			
		chain_z = box.minz + 3
		state_z = box.minz
		
		state_positions = []
		for x in range(limx):
			for y in range(limy-1):
				state_positions.append([x,y+1])
		i = 0 
		for k,v in self.parser.states.items():
			if self.parser.states[k] == None:
				self.parser.states[k] = [state_positions[i][0]+box.minx,state_positions[i][1]+box.miny,state_z]
				i += 1
				
		curr_x = 0
		for k,v in self.parser.impulse_chains.items():
			self.parser.impulse_chains[k]['position'] = [curr_x+box.minx,box.miny+1,chain_z]
			curr_x += 2
		
		for k,v in self.parser.repeat_chains.items():
			self.parser.repeat_chains[k]['position'] = [curr_x+box.minx,box.miny+1,chain_z]
			curr_x += 2
			
		curr_x += 1
		for k,v in self.parser.dialogs.items():
			self.parser.dialogs[k]['position'] = [curr_x+box.minx,box.miny+1,chain_z]
			curr_x += 4
		
		
		
		def build(level, floor_block):
			#zp, zm, up, skip_zp, skip_zm, skip_up
			for k,v in self.parser.states.items():
				pos = self.parser.states[k]
				Builder.place_block(pos[0], pos[1], pos[2], alphaMaterials[35,0], level)#Wool 0
				
			for k,v in self.parser.impulse_chains.items():
				pos = self.parser.impulse_chains[k]['position']
				Builder.place_block(pos[0], pos[1], pos[2], alphaMaterials[35,0], level)
				i = 0
				cmd_source = self.parser.impulse_chains[k]['commands']
				cx,cy,cz= pos[0], pos[1], pos[2]+1
				for move in impulse_chains_projects[k]:
					cb_type = Builder.cb_impulse if i==0 else Builder.cb_chain
					#y_down, y_up, z_down, z_up, x_down, x_up
					if move == Planner.zp:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_up, command, is_conditional)
						i += 1
						cz += 1
					elif move == Planner.zm:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_down, command, is_conditional)
						i += 1
						cz -= 1
					elif move == Planner.up:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.y_up, command, is_conditional)
						i += 1
						cy += 1
					elif move == Planner.skip_zp:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_up, "", False)
						cz += 1
					elif move == Planner.skip_zm:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_down, "", False)
						cz -= 1
					elif move == Planner.skip_up:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.y_up, "", False)
						cy += 1
			for k,v in self.parser.repeat_chains.items():
				
				pos = self.parser.repeat_chains[k]['position']
				Builder.place_block(pos[0], pos[1], pos[2], alphaMaterials[35,0], level)
				i = 0
				cmd_source = self.parser.repeat_chains[k]['commands']
				cx,cy,cz= pos[0], pos[1], pos[2]+1
				for move in repeat_chains_projects[k]:
					cb_type = Builder.cb_repeat if i==0 else Builder.cb_chain
					#y_down, y_up, z_down, z_up, x_down, x_up
					if move == Planner.zp:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_up, command, is_conditional)
						i += 1
						cz += 1
					elif move == Planner.zm:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_down, command, is_conditional)
						i += 1
						cz -= 1
					elif move == Planner.up:
						command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(cmd_source[i])
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.y_up, command, is_conditional)
						i += 1
						cy += 1
					elif move == Planner.skip_zp:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_up, "", False)
						cz += 1
					elif move == Planner.skip_zm:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.z_down, "", False)
						cz -= 1
					elif move == Planner.skip_up:
						Builder.place_cmdblock(cx,cy,cz, level, cb_type, Builder.y_up, "", False)
						cy += 1
			
			is_first = True
			for k,v in self.parser.dialogs.items():
				pos = self.parser.dialogs[k]['position']
				Builder.place_block(pos[0], pos[1], pos[2], alphaMaterials[35,0], level)
				cx,cy,cz= pos[0], pos[1], pos[2]
				i = 0
				for command_elements in self.parser.dialogs[k]['commands']:
					command, is_conditional, is_new_dialog_chain = self.parser.command_to_string(command_elements)
					if is_new_dialog_chain:#Za pierwszym razem ten warunek jest zawsze spelniony ale i=0
						if i == 1:
							cz += 2#Pierwszy osdstep jest troche krotszy bo nie trzeba budowac calej struktury
						elif i > 1:
							cz += 4
						i+=1
						cy = pos[1]
						is_first = True
						
					if i==1:#Pierwszy rzadek
						if is_first:
							Builder.place_cmdblock(cx-1,cy,cz, level, Builder.cb_impulse, Builder.y_up, 'setblock ~2 ~ ~2 air', False)
							is_first = False
						cy += 1
						Builder.place_cmdblock(cx-1,cy,cz, level, Builder.cb_chain, Builder.y_up, command, is_conditional)
					else:
						def build_layer(x,y,z, level):
							Builder.place_block(x, y, z, alphaMaterials[152,0], level)#redstone_block
							Builder.place_block(x+1, y, z, alphaMaterials[152,0], level)#redstone_block
							Builder.place_block(x, y, z+1, alphaMaterials[55,15], level)#redstone_dust
							Builder.place_hooper(x+1, y, z+1, level, [10],Builder.z_up, True)#hooper disabled south
							Builder.place_comparator(x,y,z+2, level, Builder.x_up, 0, True)#comparator
							Builder.place_hooper(x+1, y, z+2, level, [64,64,64,64,54],Builder.z_up, True)#hooper
						if is_first:
							build_layer(cx,cy,cz,level)
							Builder.place_block(cx, cy+1, cz+1, floor_block, level)#floor_block
							Builder.place_block(cx+1, cy+1, cz+1, floor_block, level)#floor_block
							Builder.place_block(cx, cy+1, cz+2, floor_block, level)#floor_block
							Builder.place_block(cx+1, cy+1, cz+2, floor_block, level)#floor_block
							build_layer(cx,cy+2,cz,level)
							Builder.place_cmdblock(cx-1,cy,cz+2, level, Builder.cb_impulse, Builder.y_up, 'clone ~1 ~2 ~-2 ~2 ~2 ~ ~1 ~ ~-2', False)
							cy += 1
							Builder.place_cmdblock(cx-1,cy,cz+2, level, Builder.cb_chain, Builder.y_up, 'setblock ~2 ~-1 ~2 air', False)
							is_first = False
						cy += 1
						Builder.place_cmdblock(cx-1,cy,cz+2, level, Builder.cb_chain, Builder.y_up, command, is_conditional)
		
		for x in range(box.minx,box.maxx):
			for y in range(box.miny,box.maxy):
				for z in range(box.minz,box.maxz):
					if y == box.miny:
						Builder.place_block(x, y, z, floor_block, level)
					else:
						Builder.place_block(x, y, z, alphaMaterials[0,0], level)
		
		build(level, floor_block)
		
	def analyse(self):
		for name, chain in self.parser.impulse_chains.items():#Create list of lengths of conditional chains needed for impulse chains
			curr_chain = 0
			last_conditional = True
			self.impulse_chains[name] = []
			for command in chain['commands']:
				if command[0].type == Token.conditional:
					curr_chain += 1
				else:
					if curr_chain > 0:#If not first
						self.impulse_chains[name].append(curr_chain)
					curr_chain = 1
			self.impulse_chains[name].append(curr_chain)
		for name, chain in self.parser.repeat_chains.items():#Create list of lengths of conditional chains needed for repeat chains
			curr_chain = 0
			last_conditional = True
			self.repeat_chains[name] = []
			for command in chain['commands']:
				if command[0].type == Token.conditional:
					curr_chain += 1
				else:
					if curr_chain > 0:#If not first
						self.repeat_chains[name].append(curr_chain)
					curr_chain = 1
			self.repeat_chains[name].append(curr_chain)
		for name, chain in self.parser.dialogs.items():#Create list of lengths of conditional chains and modules needed for dialogs
			curr_chain = 0
			last_conditional = True
			curr_module = None
			
			self.dialogs[name] = []
			for command in chain['commands']:
				if command[0].type == Token.new_dialog_chain:
					if curr_module != None:#If not first
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
		
		self.states = 0#Get number of states with unknown position
		for k,v in self.parser.states.items():
			if v != None:
				self.states += 1
		
		
		
########   FILTER CODE   ########################################################################
displayName = "Nusiq's brfunctions - v0.1"

inputs = (
	("File path","file-open"),
	("Floor block", alphaMaterials[159,0])#White stained clay
	#("Kierunek", tuple(Builder.direction.keys())),
	#("Typ", tuple(Builder.type.keys())),
	#("Conditional", False)
)	
def perform(level, box, options):
	os.system('cls')
	parser = Parser()
	parser.parse_file(str(options["File path"]))
	planner = Planner(parser)
	floor_block = options["Floor block"]
	
	planner.plan_and_build(box, level, floor_block)
	

		
		
		
		