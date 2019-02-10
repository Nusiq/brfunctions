from brfunc_building import Builder
from brfunc_parsing import Token
import hashlib
import json
import errno
from pymclevel import alphaMaterials  # pylint: disable=import-error
import os


class Planner(object):
    zp, zm, up, skip_zp, skip_zm, skip_up = ('zp', 'zm', 'up', 'skip_zp',
                                             'skip_zm', 'skip_up')

    def __init__(self, parser, project_data_repository):
        self.parser = parser
        self.project_data_repository = project_data_repository

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
                    for _ in range(conditional_len):
                        new_plan.append(Planner.zp)
                    if new_z <= lim_z - 1:
                        success = True
                    if new_z == lim_z - 1:
                        new_direction = plus_up

                elif new_direction == minus:
                    new_z -= conditional_len
                    for _ in range(conditional_len):
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

    def plan_and_build(self):
        box = self.project_data_repository.get_area()
        level = self.project_data_repository.get_level()
        floor_block = self.project_data_repository.get_floor_block()
        floor_height = self.project_data_repository.get_floor_height()

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
            raise Exception('Not enough space for states (increase X size)' +
                            ' Code:rdeiy6')

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
                    raise Exception('Box to small (you need more or biger ' +
                                    'floors)' + ' Code:zno26s')
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
            for k, _ in self.parser.states.items():
                pos = self.parser.states[k]
                Builder.place_block(pos[0], pos[1], pos[2],
                                    alphaMaterials[35, 0], level)  # Wool 0

            for k, _ in self.parser.impulse_chains.items():
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
            for k, _ in self.parser.repeat_chains.items():

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
            for k, _ in self.parser.dialogs.items():
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
        bpuuid = self.project_data_repository.get_behavior_pack_uuid()
        funcpath = self.project_data_repository.get_functions_path()

        if not isinstance(bpuuid, str) and not isinstance(bpuuid, unicode):
            raise Exception('Behavior pack UUID in project file must ' +
                            'be a string. Code:owfuou')
        if not isinstance(funcpath, str) and not isinstance(funcpath, unicode):
            raise Exception('Path to functions in project file must be a ' +
                            'string. Code:7u4lpj')
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
                raise Exception('Behaviorpack with UUID ' + bpuuid +
                                ' doesn\'t exist. Code:u30m8n')

            dev_bp_path = os.path.dirname(dev_bp_path)  # com.mojang
            if not dev_bp_path.endswith('com.mojang'):
                raise Exception('Behaviorpack with UUID ' + bpuuid +
                                ' doesn\'t exist. Code:nz8rj9')
            dev_bp_path = os.path.join(
                dev_bp_path,
                'development_behavior_packs')  # development_behavior_packs
            bp_funcpath = serch(dev_bp_path, bpuuid)
        if bp_funcpath is None:
            raise Exception('Behaviorpack with UUID ' + bpuuid +
                            ' doesn\'t exist. Code:47u2aq')
        # BEHAVIORPACK FUNCTIONS PATH IS KNOWN ( bp_funcpath )
        return bp_funcpath

    def create_functions(self):
        world_path = self.project_data_repository.get_level().filename

        bpuuid = self.project_data_repository.get_behavior_pack_uuid()
        funcpath = self.project_data_repository.get_functions_path()

        if bpuuid is None or funcpath is None:
            return None  # Nothing to copy

        bp_funcpath = self.get_bp_path(world_path)

        # Load history of last edit.
        history = None
        try:
            with open(os.path.join(funcpath,
                                   'brfunction_last_edit.json'), 'r') as f:
                history = json.load(f)
        except IOError as e:
            # Pass only if error is: "No such file or directory"
            if e.errno != errno.ENOENT:
                raise e

        # Find files edited with external progrmas
        if history is not None:
            # file_path - file path,
            # hash_obj - object with data describing the file
            for file_path, hash_obj in history.items():
                file_path = os.path.join(bp_funcpath, file_path)
                try:
                    with open(file_path, 'r') as f:
                        hasher = hashlib.md5()
                        hasher.update(f.read())
                        if hash_obj['md5'] != hasher.hexdigest():
                            raise Exception(
                                'File ' + file_path +
                                ' has been modified with external ' +
                                'application. Delete the file and run ' +
                                'filter again if you are sure that you want' +
                                ' apply changes to it. Code:cs4kwg')
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                except IOError as e:

                    # Pass only if error is: "No such file or directory"
                    if e.errno != errno.ENOENT:
                        raise e

        # Edit files
        new_history = {}
        # source - source file path, v - dictionary with list of commands form
        # the file in v['commands']
        for source, v in self.parser.functions.items():
            target = os.path.join(bp_funcpath, source)
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
                new_history[source] = {'md5': hasher.hexdigest()}

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
        for _, v in self.parser.states.items():
            if v is not None:
                self.states += 1
