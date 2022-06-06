class Antagonist:
    def __init__(self):
        pass

    def init(self, output_path, cores, mem_numa, opts):
        raise NotImplementedError

    # Run for a certain duration
    def run(self, duration):
        raise NotImplementedError

    def wait(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def set_instsize(self, size):
        raise NotImplementedError

    def set_pattern(self, pattern):
        raise NotImplementedError
    
    def set_hugepages(self, val):
        raise NotImplementedError

    def set_writefrac(self, val):
        raise NotImplementedError

    
