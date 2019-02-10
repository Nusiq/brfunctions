import json
import os


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


class FilePDR(ProjectDataRepository):
    '''
    Implementation of ProjectDataRepository. Uses path to a file
    as a data source. The file can be project.json or .brfunction.
    '''
    def __init__(self, file_path, floor_block, level, box, floor_height=255):
        self.file_path = file_path
        self.floor_block = floor_block
        self.floor_height = floor_height

        self.area = box
        self.level = level

        self.files = None
        self.functions_path = None
        self.behavior_pack_uuid = None

        class CustomBox(object):
            def __init__(self):
                self.minx = None
                self.miny = None
                self.minz = None
                self.maxx = None
                self.maxy = None
                self.maxz = None

        project_data = None

        is_project = True
        # Test if file is json project file -> project_data, use_as_project
        try:
            with open(file_path) as project_file:
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

                self.area = CustomBox()
                self.area.minx = project_data['area'][0] if \
                    project_data['area'][0] < project_data['area'][3] else \
                    project_data['area'][3]
                self.area.miny = project_data['area'][1] if \
                    project_data['area'][1] < project_data['area'][4] else \
                    project_data['area'][4]
                self.area.minz = project_data['area'][2] if \
                    project_data['area'][2] < project_data['area'][5] else \
                    project_data['area'][5]
                self.area.maxx = project_data['area'][0] if \
                    project_data['area'][0] > project_data['area'][3] else \
                    project_data['area'][3]
                self.area.maxy = project_data['area'][1] if \
                    project_data['area'][1] > project_data['area'][4] else \
                    project_data['area'][4]
                self.area.maxz = project_data['area'][2] if \
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
                self.files = project_data
            else:
                raise Exception('Invalid project file structure. ' +
                                type(project_data) + ' Code:x6ibzz')

            path = os.path.split(file_path)[0]
            if self.functions_path is not None:
                self.functions_path = os.path.join(path, self.functions_path)

        else:  # The file is a brfunction
            self.files = [os.path.basename(file_path)]

    def brfunction_generator(self):
        path = os.path.split(self.file_path)[0]

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


class EntityPathPDR(ProjectDataRepository):
    def __init__(self, project_data_repository=None, files=None, area=None,
                 floor_height=None, functions_path=None,
                 behavior_pack_uuid=None, floor_block=None, level=None):

        if project_data_repository is not None:
            self.files = project_data_repository.get_files()
            self.area = project_data_repository.get_area()
            self.floor_height = project_data_repository.get_floor_height()
            self.functions_path = project_data_repository.get_functions_path()
            self.behavior_pack_uuid = \
                project_data_repository.get_behavior_pack_uuid()
            self.floor_block = project_data_repository.get_floor_block()
            self.level = project_data_repository.get_level()

        # Values passed by arguments are more important than values from
        # project_data_repository
        self.files = files if files is not None else self.files
        self.area = area if area is not None else self.area
        self.floor_height = floor_height if floor_height is not None \
            else self.floor_height
        self.functions_path = functions_path if functions_path is not None \
            else self.functions_path
        self.behavior_pack_uuid = behavior_pack_uuid \
            if behavior_pack_uuid is not None else self.behavior_pack_uuid
        self.floor_block = floor_block if floor_block is not None else \
            self.floor_block
        self.level = level if level is not None else self.level


class MultipleSourcePDR(ProjectDataRepository):
    '''
    Implementation of ProjectDataRepository. Joins multiple project data
    repositories into one by joining brfunction_generator and
    mcfunction_generator methods. The first repository added in constructor is
    used to provide - get_files, get_area, get_floor_height,
    get_functions_path, get_behavior_pack_uuid, get_floor_block and
    get_level methods.
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
        return self.repositories[0].get_files()

    def get_area(self):
        return self.repositories[0].get_area()

    def get_floor_height(self):
        return self.repositories[0].get_floor_height()

    def get_functions_path(self):
        return self.repositories[0].get_functions_path()

    def get_behavior_pack_uuid(self):
        return self.repositories[0].get_behavior_pack_uuid()

    def get_floor_block(self):
        return self.repositories[0].get_floor_block()

    def get_level(self):
        return self.repositories[0].get_level()
