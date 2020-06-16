from tfg.stackcollapsers.stackcollapser import StackCollapser

class PySpyCollapser(StackCollapser):
    def parse(self):
        """parse(self) -> list[(list[str], int)]
        """
        result = []
        for i, line in enumerate([x.strip() for x in self._input_file], 1):
            if not line:
                continue
            vals = line.split(";")
            parts = vals[-1].split(" ")
            vals[-1] = " ".join(parts[:-1])
            count = int(parts[-1])
            result.append((vals, count))
        return result
