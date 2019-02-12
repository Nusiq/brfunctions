#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from functools import total_ordering
from pymclevel.box import BoundingBox  # pylint: disable=import-error


class ProjectDataRepository(object):
    def brfunction_generator(self):
        raise NotImplementedError()

    def mcfunction_generator(self):
        raise NotImplementedError()

    def get_files(self):
        return self.files  # pylint: disable=no-member

    def get_area(self):
        return self.area  # pylint: disable=no-member

    def get_floor_height(self):
        return self.floor_height  # pylint: disable=no-member

    def get_functions_path(self):
        return self.functions_path  # pylint: disable=no-member

    def get_behavior_pack_uuid(self):
        return self.behavior_pack_uuid  # pylint: disable=no-member

    def get_floor_block(self):
        return self.floor_block  # pylint: disable=no-member

    def get_level(self):
        return self.level  # pylint: disable=no-member

    def get_project_file_path(self):
        return self.project_file_path  # pylint: disable=no-member


class FilePDR(ProjectDataRepository):
    '''
    Implementation of ProjectDataRepository. Uses path to a file
    as a data source. The file can be project.json or .brfunction.
    '''
    def __init__(self, project_file_path, floor_block, level, box,
                 floor_height=255):
        self.project_file_path = project_file_path
        self.floor_block = floor_block
        self.floor_height = floor_height

        self.area = box
        self.level = level

        self.files = None
        self.functions_path = None
        self.behavior_pack_uuid = None

        project_data = None

        is_project = True
        # Test if file is json project file -> project_data, use_as_project
        try:
            with open(project_file_path) as project_file:
                project_data = json.load(project_file)
        except BaseException:
            is_project = False

        if is_project:  # The file is a json project file
            if isinstance(project_data, dict):
                if (('files' not in project_data.keys()) or
                        ('area' not in project_data.keys())):
                    raise Exception('Invalid project file structure. ' +
                                    type(project_data) + ' Code:wiv5af')

                self.files = project_data['files']

                area = project_data['area']
                minx = area[0] if area[0] < area[3] else area[3]
                miny = area[1] if area[1] < area[4] else area[4]
                minz = area[2] if area[2] < area[5] else area[5]
                maxx = area[0] if area[0] > area[3] else area[3]
                maxy = area[1] if area[1] > area[4] else area[4]
                maxz = area[2] if area[2] > area[5] else area[5]
                self.area = BoundingBox(
                    origin=(minx, miny, minz),
                    size=(maxx-minx, maxy-miny, maxz-minz)
                )

                # Save additional options data
                if 'floor_height' in project_data.keys():
                    self.floor_height = project_data['floor_height']
                if 'behavior_pack_uuid' in project_data.keys():
                    self.behavior_pack_uuid = \
                        project_data['behavior_pack_uuid']
                if 'functions_path' in project_data.keys():
                    self.functions_path = project_data['functions_path']
            elif isinstance(project_data, list):
                self.files = project_data
            else:
                raise Exception('Invalid project file structure. ' +
                                type(project_data) + ' Code:x6ibzz')

            path = os.path.split(project_file_path)[0]
            if self.functions_path is not None:
                self.functions_path = os.path.join(path, self.functions_path)

        else:  # The file is a brfunction
            self.files = [os.path.basename(project_file_path)]

    def brfunction_generator(self):
        path = os.path.split(self.project_file_path)[0]

        for item_file_name in self.files:
            full_item_file_name = path + '/' + item_file_name
            with open(full_item_file_name) as f:
                for line_index, l in enumerate(f, 1):
                    yield l, full_item_file_name, line_index

    def mcfunction_generator(self):
        if (self.behavior_pack_uuid is not None and
                self.functions_path is not None):
            for root, _, files in os.walk(self.functions_path):
                for f_name in files:
                    if f_name.endswith('.mcfunction'):
                        source = os.path.join(root, f_name)
                        with open(source) as f:
                            for line_index, l in enumerate(f, 1):
                                yield (l, source[len(self.functions_path)+1:],
                                       line_index)

        else:
            raise StopIteration()  # Empty list of function files / no bp path

# Currently not used
class MultipleSourcePDR(ProjectDataRepository):
    '''
    Implementation of ProjectDataRepository. Joins multiple project data
    repositories into one by joining brfunction_generator and
    mcfunction_generator methods. The first repository that can return
    not Null value is used to provide - get_files, get_area, get_floor_height,
    get_functions_path, get_behavior_pack_uuid, get_floor_block,
    get_level and get_project_file_path methods.
    '''

    def __init__(self, *repositories):
        self.repositories = repositories

    def brfunction_generator(self):
        for repo in self.repositories:
            for val in repo.brfunction_generator():
                yield val

    def mcfunction_generator(self):
        for repo in self.repositories:
            for val in repo.mcfunction_generator():
                yield val

    def get_files(self):
        for repo in self.repositories:
            if repo.get_files() is not None:
                return repo.get_files()
        return None

    def get_area(self):
        for repo in self.repositories:
            if repo.get_area() is not None:
                return repo.get_area()
        return None

    def get_floor_height(self):
        for repo in self.repositories:
            if repo.get_floor_height() is not None:
                return repo.get_floor_height()
        return None

    def get_functions_path(self):
        for repo in self.repositories:
            if repo.get_functions_path() is not None:
                return repo.get_functions_path()
        return None

    def get_behavior_pack_uuid(self):
        for repo in self.repositories:
            if repo.get_behavior_pack_uuid() is not None:
                return repo.get_behavior_pack_uuid()
        return None

    def get_floor_block(self):
        for repo in self.repositories:
            if repo.get_floor_block() is not None:
                return repo.get_floor_block()
        return None

    def get_level(self):
        for repo in self.repositories:
            if repo.get_level() is not None:
                return repo.get_level()
        return None

    def get_project_file_path(self):
        for repo in self.repositories:
            if repo.get_project_file_path() is not None:
                return repo.get_project_file_path()
        return None
