from abc import ABC, abstractmethod

from translator.intermediate_language import IntermediateLanguage


class Translator(ABC):
    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate_language = intermediate_language

    @abstractmethod
    def to_file_string(self) -> str:
        pass

    def write_to_file(self, file_path: str):
        with open(file_path, "w") as file:
            file.write(self.to_file_string())

    def solve(self):
        pass