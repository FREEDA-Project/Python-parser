from typing import Any
from pydantic import BaseModel
from data.application import Application
from data.components import Component
import itertools

class IntermediateLanguage(BaseModel):
    comps: set[str]
    nodes: set[str]
    flav: dict[str,set[str]]
    uses: dict[str,dict[str,set[str]]]
    comReq: dict[str,dict[set,dict[str,Any]]]


class IntermaediateLanguageBuilder():

    def __init__(self,app:Application) -> None:
        self.app=app 


    def build(self)->IntermediateLanguage:
        # Be careful with the order of the following lines
        # cause there are dependencies between them the are 
        # not explicit in the code
        self.comps=self._extract_components()
        self.flav=self._extract_flav()
        self.flavs=self._extract_flavours()
        self.uses=self._extract_uses()
        return IntermediateLanguage(
            comps=self.comps,
            flavs=self.flavs,
            nodes=[],
            flav=self.flav,
            uses=self.uses
        )

    def _extract_uses(self)->dict[str,dict[str,set[str]]]:
        uses={}
        for comp in self.comps:
            for flav in self.flavs:
                if comp not in uses:
                    uses[comp]={}
                uses[comp][flav]=set(self.app.components[comp].flavours.get(flav,[]))
        return uses
        
    def _extract_components(self)->set[str]:
        return set(self.app.components.keys())
        

    def _extract_flav(self)->dict[str,set[str]]:
        flav={}
        for comp in self.comps:
            flav[comp]=set(self.app.components[comp].flavours.keys())
        return flav

    def _extract_requirement_from_app(self)->set[str]:
        for component in self.app.components.values():
            for req in component.component_requirements:
                pass
        return set()


    def _extract_flavours(self)->set[str]:
        return set(
                itertools.chain.from_iterable(
                    map(
                        lambda x:x.flavours.keys(),
                        self.app.components.values()
                    )
                )
            )