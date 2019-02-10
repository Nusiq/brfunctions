import json
import os


class ProjectDataRepository(object):
    def get_brfunction_generator(self):
        raise NotImplementedError()

    def get_mcfunction_generator(self):
        raise NotImplementedError()

    def get_files(self):
        raise NotImplementedError()

    def get_area(self):
        raise NotImplementedError()

    def get_floor_height(self):
        raise NotImplementedError()

    def get_functions_path(self):
        raise NotImplementedError()

    def get_behavior_pack_uuid(self):
        raise NotImplementedError()

    def get_floor_block(self):
        raise NotImplementedError()

    def get_level(self):
        raise NotImplementedError()


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

        project_data = None  # 1597

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

    def get_brfunction_generator(self):
        path = os.path.split(self.file_path)[0]

        for item_file_name in self.files:
            full_item_file_name = path + '/' + item_file_name
            with open(full_item_file_name) as f:
                for line_index, l in enumerate(f, 1):
                    yield l, full_item_file_name, line_index

    def get_mcfunction_generator(self):
        if (self.behavior_pack_uuid is not None and
                self.functions_path is not None):
            for root, _, files in os.walk(self.functions_path):
                for f_name in files:
                    if f_name.endswith('.mcfunction'):
                        source = os.path.join(root, f_name)
                        with open(source) as f:
                            for line_index, l in enumerate(f, 1):
                                yield l, source, line_index

        else:
            raise StopIteration()  # Empty list of function files / no bp path

    def get_files(self):
        return self.files

    def get_area(self):
        return self.area

    def get_floor_height(self):
        return self.floor_height

    def get_functions_path(self):
        return self.functions_path

    def get_behavior_pack_uuid(self):
        return self.behavior_pack_uuid

    def get_floor_block(self):
        return self.floor_block

    def get_level(self):
        return self.level
