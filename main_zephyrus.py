#!/usr/bin/env python

from loader import load_application, load_infrastructure, load_resources
from src.data.resources import default_resources
from src.language.intermediate_language import IntermediateStructure
from src.translators.minizinc.dzn import DZNTranslator
from src.translators.zephyrus import ZephyrusTranslator

def main(
    components_data,
    infrastructure_data,
    priority,
    additional_resources_data=None
):
    if additional_resources_data is not None:
        default_resources.update(additional_resources_data)
    resources = load_resources(default_resources)

    infrastructure = load_infrastructure(infrastructure_data, resources)
    app = load_application(components_data, resources)

    intermediate_structure = IntermediateStructure(
        app,
        infrastructure,
        priority
    )

    translated_minizinc = DZNTranslator(intermediate_structure).to_string()
    translated_zephyrus = ZephyrusTranslator(intermediate_structure).to_string()

    return translated_minizinc, translated_zephyrus
