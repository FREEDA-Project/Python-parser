from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator

class ZephyrusTranslator(Translator):
    def combine_comp_flav(self, c, f):
        separator = "-"
        return str(c) + separator + str(f)

    def __init__(self, struct: IntermediateStructure):
        super(ZephyrusTranslator, self).__init__(struct)

        self.output = []

        self.zephyrus_components = [
            self.combine_comp_flav(c, f)
            for c, flav in struct.flavours.items()
            for f in flav
        ]

        self.output.append(
            "comps = 1.." + str(len(self.zephyrus_components)) + ";"
        )
        self.output.append("locations = 1.." + str(len(struct.nodes)) + ";")
        self.output.append("resources = 1.." + str(len(struct.resources)) + ";\n")

        self.output.append(
            "resource_provisions = [|" +
            "|".join(str(r) for (_, _), r in struct.node_capabilities.items()) +
            "|];"
        )

        self.output.append(
            "resource_consumptions = [|" +
            "|".join(str(r) for (_, _, _), r in struct.component_requirements.items()) +
            "|];"
        )

        self.output.append(
            "costs = [" +
            ",".join(str(r) for (_, _), r in struct.node_cost.items()) +
            "];"
        )

        self.ports = len(self.zephyrus_components)
        self.output.append("\nports = 1.." + str(self.ports) + ";")

        self.requirement_port_nums = []
        for c, flav in struct.flavours.items():
            for f in flav:
                row = []
                if (c, f) in struct.uses:
                    for ct, flavs_t in struct.flavours.items():
                        for ft in flavs_t:
                            row.append("1" if (ct, ft) in struct.uses[c, f] else "0")
                else:
                    row.extend(["0"] * self.ports)
                self.requirement_port_nums.append(", ".join(row))

        self.output.append(
            "requirement_port_nums = [|\n" +
            "|\n".join(self.requirement_port_nums) +
            "\n|];"
        )

        self.output.append(
            "conflicts = [|\n" +
            "|\n".join([
                ", ".join(["true"] * self.ports)
            ] * len(self.zephyrus_components)) +
            "\n|];"
        )

        self.multi_provide_ports = len(self.zephyrus_components)
        self.output.append("multi_provide_ports = 1.." + str(self.multi_provide_ports) + ";")
        self.output.append(
            "multi_provides = [|\n" +
            "|\n".join([
                ", ".join(["true"] * self.multi_provide_ports)
            ] * self.ports) +
            "|];"
        )

        # Importance are all flat, so we can just keep track of each component
        provide = {
            (ct, cf)
            for (cf, _), uses_list in struct.uses.items()
            for ct, _ in uses_list
        }
        self.provide_port_nums = []
        for c1, f1s in struct.flavours.items():
            for _ in f1s:
                self.provide_port_nums.append(
                    ", ".join([
                        "1" if (c1, c2) in provide else "0"
                        for c2, f2s in struct.flavours.items()
                        for _ in f2s
                    ]
                ))
        # for c1, f1s in struct.flavours.items():
        #     for f1 in f1s:
        #         self.provide_port_nums.append(
        #             ", ".join([
        #                 "1" if (c1, f1) in struct.uses and (c2, f2) in struct.uses[(c1, f1)] else "0"
        #                 for c2, f2s in struct.flavours.items()
        #                 for f2 in f2s
        #             ]
        #         ))
        self.output.append(
            "provide_port_nums = [|\n" +
            "|\n".join(self.provide_port_nums) +
            "\n|];"
        )

        # self.output.append("multi_provide_ports = 1..1;")
        # self.output.append(
        #     "multi_provides = [|\n" +
        #     ",".join(["true"] * len(self.zephyrus_components)) +
        #     "|];"
        # )

        # self.output.append("provide_port_nums = [|\n" +
        #     "|".join(
        #         "1" if (c1, f1) in struct.uses else "0"
        #         for c1, f1s in struct.flavours.items()
        #         for f1 in f1s
        #     ) +
        #     "|];\n"
        # )


    def to_string(self) -> str:
        return "\n".join(self.output)
