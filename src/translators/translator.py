from src.language.intermediate_language import IntermediateStructure

class Translator:
    def __init__(self, structure: IntermediateStructure):
        self.structure = structure

    def to_string(self) -> str:
        raise NotImplementedError("Please implement this method")

    def write_to_file(self, file_path: str):
        with open(file_path, "w") as file:
            file.write(self.to_string())
