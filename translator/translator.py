from abc import ABC, abstractmethod

from translator.intermediate_language import IntermediateLanguage

class Translator(ABC):

    @classmethod
    @abstractmethod
    def from_intermediate_language(cls, intermediate_language:IntermediateLanguage  ) -> "Translator":
        pass


    @abstractmethod
    def to_file_string(self) -> str:
        pass
    
    def write_to_file(self, file_path:str):
        with open(file_path, "w") as file:
            file.write(self.to_file_string())