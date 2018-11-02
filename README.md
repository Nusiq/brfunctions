# Overview
Brfunctions is an MCEdit filter for placing down commandblocks on Minecraft bedrock edition world with commands from given files (similar to mcfunctions on java edition). The filter extends the syntax of Minecraft commands to make the code easier to analyze and to make mapmakers work easier.

### Features
- Placing down impulse chains of commandblocks and referring to them like to variables.
- Placing down repeat chains of commandblocks and referring to them like to variable.
- ~~Placing down structures that can run sequences of commands with a delay over multiple ticks.~~ **DEPRECATED** This feature shouldn't be used anymore since the release of scoreboards on Minecerft bedrock edition v. 1.7.
- Saving positions and areas as variables and referring to them inside or outside Minecraft selectors.
- Saving custom strings as variables.
- ~~Defineing and using number variables to store and change the state of command system on a block without the need of knowing the position and the actual type of the block.~~ **DEPRECATED** This feature shouldn't be used anymore since the release of scoreboards on Minecraft bedrock edition v. 1.7.
- The custom syntax allows the user to define which command blocks should be conditional. Commandblocks are placed down safely so conditional commandblocks are never on the curve of the chain of commands.
- Setting names of commandblocks.
- The user can define the area of placing commandblocks inside project file without the need for selecting it inside MCEdit. 
- Comments inside the code.

# How to use it?
## Project file
The project file is a JSON file which tells the MCEdit filter which files should be used to place down commandblocks and where to place them. It can be written in two different ways.
#### The first way - the object with information about the area to edit and the list of files to use:
Example:
```
{
    "area":[1,2,3,40,50,60],
    "files":[
        "file1.brfunction",
        "file2.brfunction",
        "file3.brfunction",
        "file4.brfunction",
        "file5.brfunction"
    ]
}
```
A project file like that would place down commands from files on the "files" list in the area between coordinates x=1,y=2,z=3 and x=40,y=50,z=60. The location of project file is used as root location for serching for files on the "files" list.

#### The second way - the list of files.
Example:
```
[
  "file1.brfunction",
  "file2.brfunction",
  "file3.brfunction",
  "file4.brfunction",
  "file5.brfunction"
]
```
You don't have to define the area to edit inside project file. If you use the second way of writing project file, commandblocks will be placed in the area selected in MCEdit. The location of the project file is used as a root location for searching for files on the "files" list.

#### The secret third way - not using the project file.
The project file is optional. You can just write all commands in one file and use that instead.

## General rules about the syntax
*This part of the README is so that there is no need to repeat the same things many times. If you are reading the whole thing from top to bottom it can make a little sense to you but it should become more clear later.* **I highly recommend reading this section!**

- All references and definitions of variables are surrounded with grave accent symbol ( `` ` `` ).
- If something between grave accents starts with `/` its a definition, if not it's a reference do a value defined earlier.
- All types of variables have a full name or a short name. A short name is always the first letter of the full name of a type of variable. In any case, you can use them interchangeably. Example: There is no difference for the parser used by the MCEdit filter if you write `` `/custom[abc](def)` `` or `` `/c[abc](def)` ``.
- Most of the variable definitions follow this pattern -  `` `/type[name](value) `` where "type" is a type of variable, "name" is a name of a variable that you can use later to refer to it and "value" is an additional value used to create it. Some types of variables don't take the "value" argument.
- Most of the references to variables follow this pattern `` `type[name](value)` `` where "type" is a type of variable, "name" is a name of variable that you are referring to and "value" is an additional value used to get certain result (more about that later). Some types of variables don't take the "value" argument. 

## Types of commandblock structures
Currently, the filter supports 3 different types of structures of commandblocks. You need to choose a type of structure to place before you start writing commands. You can define a name for a structure of commandblocks in order to be able to refer to it in other parts of code but it's not required.
#### Impulse chain
Impulse chain of commandblocks is a chain of commands that start with impulse commandblock.
Example:
```
`/impulse[myImpulseChain]`
say ABC
say DEF
setblock `i[myImpulseChain](0)`
```
This example shows a definition of a chain of commandblocks called "myImpulseChain". The first line of code is a definition. All commands after that (until the next definition of a structure) are considered part of the impulse chain. The last command has a reference to impulse chain (`` `i[myImpulseChain](0)` ``). This reference turns the command chain off. `` `i[myImpulseChain](0)` `` is converted into `X Y Z lapis_block 0`. `` `i[myImpulseChain](1)` `` would be converted into `X Y Z redstone_block 0` and would turn the chain of commands on. `X Y Z` are coordinates of a block next to the first block of the chain of commands. Notice that the mapmaker doesn't need to know the coordinates of that block. They are picked by the filter automatically. 

Remember to turn impulse chain of commands off before you turn it on again or triggering it will have no effect (replacing redstone_block with redstone_block won't trigger impulse commandblock).
#### Repeating chain
Repeating chain of commandblocks is a chain of commands that start with repeating commandblock.
Example:
```
`/repeat[myRepeatingChain]`
say ABC
say DEF
setblock `r[myRepeatingChain](0)`
```
This example shows a definition of a chain of commandblocks called "myRepeatingChain". The first line of code is a definition. All commands after that (until the next definition of a structure) are considered part of the repeating chain. The last command has a reference to repeating chain (`` `r[myRepeatingChain](0)` ``). This reference turns the command chain off. `` `r[myRepeatingChain](0)` `` is converted into `X Y Z lapis_block 0`. `` `r[myRepeatingChain](1)` `` would be converted into `X Y Z redstone_block 0` and would turn the chain of commands on. `X Y Z` are coordinates of a block next to the first block of the chain of commands. Notice that the mapmaker doesn't need to know the coordinates of that block. They are picked by the filter automatically. 
#### Dialog chain **DEPRECATED**
*This feature is deprecated and it won't be supported in future versions of the filter.*

Dialog chain of commandblocks is a structure of blocks that use hoppers to run commands in short intervals.
Example:
```
`/dialog[myDialogChain]`
+ say ABC
say DEF
+ say GHI
setblock `d[myDialogChain](0)`
```
This example shows a definition of a chain of commandblocks called "myDialogChain". The first line of code is a definition. All commands after that (until the next definition of a structure) are considered part of the dialog chain. The last command has a reference to the dialog chain (`` `d[myDialogChain](0)` ``). This reference turns the command chain off. `` `d[myDialogChain](0)` `` is converted into `X Y Z lapis_block 0`. `` `d[myDialogChain](1)` `` would be converted into `X Y Z redstone_block 0` and would turn the chain of commands on. `X Y Z` are coordinates of a block next to the first block of the chain of commands. Notice that the mapmaker doesn't need to know the coordinates of that block. They are picked by the filter automatically. `+` before command in dialog chain is used to group commands that should be executed in the same tick together. First two commands from example above will be executed instantly after activation of "myDialogChain" and the other two will be executed after a few ticks of delay. 
## Custom values
#### Position (position)
You can add names to positions to make your life easier. Example:
```
`/position[myPosition](1 2 3)`
tp @a `p[myPosition]`
say @e[`p[myPosition]@`,r=5]
```
The three examples above show different uses of position. The first one is a definition of a position called "myPosition". The second command uses the reference to this position (it will return `1 2 3`). The third command is the selector reference to "myPosition" and it will return "x=1,y=2,z=3".
#### Position (area)
Putting 6 values into a position will define an area between two positions. Example:
```
`/position[myArea](1 2 3 11 12 13)`
fill `p[myArea]` stone
say @e[`p[myArea]@`]
```
The three examples above show different uses of position. The first one is a definition of an area called "myArea". The second command uses the reference to this position (it will return `1 2 3 11 12 13`). The third command is the selector reference to "myArea" and it will return "x=1,y=2,z=3,dx=10,dy=10,dz=10".
#### Custom
Custom values are used to add a name to any string.
```
`/custom[myCustomValue](Hello world!)`
say `c[myCustomValue]`
```
The example above shows two uses of a custom value. The first use is the definition. The second commands show how to refer to a custom value (the second command will be transformed into `say Hello world!`).
#### State **DEPRECETED**
States were designed to add an easy way to store a value (for example a state of the mechanism). The release of scoreboards made them obsolete. The states record their value by placing the appropriate block in the right place. You don't need to know what kind of block is it and where it is. You can refer to it by its name and numerical value. Example:
```
`/state[myState]`
`/state[myStateWithCoordinates](1 2 3)`
setblock `state[myState](5)`
testforblock `state[myState](3)`
```
The first two lines show how to define states. The first method puts a block to save the state in an unknown position. The second way of defining state is useful when you want to store a state in a certain position. The other two lines of code show how to set and get the value of the state. States can store values from 0 to 31.

## Other elements of the syntax
#### Conditional commandblocks
If you want to make a commandblock conditional just type `>` before its command. Example:
```
scoreboard players test FAKEPLAYER var 1 1
> say the score of FAKEPLAYER in var scoreboard is 1
```
The second command from the example above is conditional.
#### Setting name of commandblocks
If you want to make a commandblock with a custom name just type the name inside square brackets before the commands. Example
```
scoreboard players test FAKEPLAYER var 1 1
>[CustomName] say the score of FAKEPLAYER in var scoreboard is 1
[CustomName] say another commandblock with a custom name.
```

#### Comments
Everything after `#` until the end of the line is a comment.
# Content
- brfunctions.py - the filter.  
- tokens.py - old description of custom syntax.
- highlight.xml - syntax highlighting for Notepad++.  
