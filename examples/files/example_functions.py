from bom_analysis import ureg


class AddMass:
    def __init__(self):
        pass

    def solve(self, assembly):
        flat = assembly.flatten()
        for component in flat.values():
            component.params.mass = 10 * ureg("kg")
