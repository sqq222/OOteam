import tempfile
from import_export.tmp_storages import TempFolderStorage

class Utf8TempFolderStorage(TempFolderStorage):

    def open(self, mode='r'):
        if self.name:
            return open(self.get_full_path(), mode, encoding='utf-8')
        else:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.name = tmp_file.name
            return tmp_file