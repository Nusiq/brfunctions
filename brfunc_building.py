from pymclevel import (  # pylint: disable=import-error
    TAG_List, TAG_Byte, TAG_Int, TAG_Compound, TAG_Short,
    TAG_String, TAG_Long, alphaMaterials,
)


class Builder(object):
    y_down, y_up, z_down, z_up, x_down, x_up = range(6)
    cb_impulse, cb_repeat, cb_chain = range(3)

    @staticmethod
    def place_block(x, y, z, block, level):
        chunk = level.getChunk(x / 16, z / 16)
        level.setBlockAt(x, y, z, block.ID)
        level.setBlockDataAt(x, y, z, block.blockData)
        chunk.dirty = True

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
