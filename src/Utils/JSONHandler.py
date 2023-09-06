import json
import os


class JSONHandler:
    def __init__(self, filename, message, **decode_kwargs):
        self.filename = filename
        self.message = message
        self.decode_kwargs = decode_kwargs

    def __enter__(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f'JSON file {self.filename} does not exist')
        try:
            with open(self.filename, 'r', encoding="utf-8") as stream:
                return json.load(stream, **self.decode_kwargs)
        except json.decoder.JSONDecodeError as e:
            raise json.decoder.JSONDecodeError(f'{self.message}: {str(e)}') from e

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass
