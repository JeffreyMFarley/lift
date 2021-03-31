import io
from functools import cached_property


class Options(object):
    @cached_property
    def starts(self):
        with io.open(self.start_file) as f:
            return [x.strip() for x in f]

    @cached_property
    def ends(self):
        with io.open(self.end_file) as f:
            return [x.strip() for x in f]

    @cached_property
    def highlights(self):
        if not self.highlights_file:
            return []
            
        with io.open(self.highlights_file) as f:
            return [x.strip() for x in f]

    @cached_property
    def markers(self):
        return ['bar']
