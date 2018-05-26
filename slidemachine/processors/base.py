__description__ = \
"""
Define base processor class.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-05-10"

import os, hashlib, shutil, re, json, copy

def _split_string(s, delim, escape='\\'):
    """
    Split a string on delim, properly accounting for escape. Not particularly
    fast, but I'm not anticipating parsing huge markdown files.

    Code taken from solution by Taha Jahangir on stackoverflow.

    https://stackoverflow.com/questions/18092354/python-split-string-without-splitting-escaped-character
    """
    ret = []
    current = []
    itr = iter(s)
    for ch in itr:
        if ch == escape:
            try:
                current.append(next(itr))
            except StopIteration:
                current.append(escape)
        elif ch == delim:
            # split! (add current to the list and reset it)
            ret.append(''.join(current))
            current = []
        else:
            current.append(ch)
    ret.append(''.join(current))
    return ret

class Processor:
    """
    Base class for all processor subclasses in slidemachine.
    """

    def __init__(self,target_dir,pattern="!\[sm.dummy\]"):
        """
        target_dir: place to store output files
        pattern: markdown pattern that should invoke this processor
        """

        self._target_dir = target_dir
        self._pattern = re.compile(pattern)

        # Dictionary of every file seen during processing. key is the
        # md5 hash of the file; value is the filename.  This is used to
        # minimize the number of files in the final output.  Only unique
        # files are copied into _target_dir
        self._file_seen_dict = {}

        # Dictionary holding every file processed that will be written out
        # as "target_dir/prev-build.json".  Keys will be md5 hashes of input
        # files; values will depend on subclass.
        self._this_proc_dict = {}

        # List of output files associated with this processor
        self._output_files = []

        self._name = self.__class__.__name__
        self._prev_build_dict = {}

    def _get_file_md5(self,input_file):
        """
        Determine the md5 hash of the input file
        """

        hash_md5 = hashlib.md5()
        with open(input_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()

        return file_hash

    def _copy_file(self,input_file):
        """
        Copies input_file into the target_dir, returning the new file name as a
        string.  If multiple lines in the markdown point to the same image file
        (even if they have different names) the file is only copied once.  If
        two different files have the same name, the second file renamed to
        avoid the conflict.  Return a string with the path of the final, copied
        file.
        """

        file_hash = self._get_file_md5(input_file)

        # see if this file has been seen before
        try:
            new_file = self._file_seen_dict[file_hash]

        # if not, process it
        except KeyError:

            file_root = os.path.split(input_file)[1]
            new_file = os.path.join(self._target_dir,file_root)

            # name conflict, add counter until no conflict
            counter = 0
            while os.path.isfile(new_file):
                new_root = "{:05d}_{:s}".format(counter,file_root)
                new_file = os.path.join(self._target_dir,new_root)
                counter += 1

            self._file_seen_dict[file_hash] = new_file

            shutil.copy(input_file,new_file)

            self._output_files.append(new_file)

        return new_file

    def _parse_markdown_line(self,line,delim=","):
        """
        Parse a slidemachine markdown line, returning the input file and the
        arguments passed.  If there are no arguments, return args = None.
        """

        tmp = _split_string(line,"(")[1]
        tmp2 = _split_string(tmp,")")

        # Get input file
        input_file = tmp2[0]

        # If there's leftovers after the input file, treat them as comma-
        # separated arguments.
        args = None
        if len(tmp2) > 1:
            if tmp2[1].strip() != "":

                if delim is None:
                    args = tmp2[1].strip()
                else:
                    args = tmp2[1].split(delim)
                    args = [a.strip() for a in args]

        return input_file, args

    def add_previous_build_information(self,prev_build_dict):
        """
        Load a dictionary of previous build information.
        """

        self._prev_build_dict = copy.deepcopy(prev_build_dict)

    def write_build_json(self):
        """
        Write build information from this run to prev-build.json.
        """

        # Json output file
        json_file = os.path.join(self._target_dir,"prev-build.json")

        # Get current json content
        try:
            current_json_contents = json.load(open(json_file,'r'))
        except FileNotFoundError:
            current_json_contents = {}

        # Add this processor to the content
        current_json_contents[self.name] = copy.deepcopy(self._this_proc_dict)

        # Write out
        f = open(json_file,'w')
        json.dump(current_json_contents,f)
        f.close()


    def process(self,line):
        """
        Dummy method.  Overwritten in subclasses.
        """

        return line

    @property
    def target_dir(self):
        return self._target_dir

    @target_dir.setter
    def target_dir(self,target_dir):
        self._target_dir = target_dir

    @property
    def name(self):
        return self._name

    @property
    def output_files(self):
        return self._output_files
