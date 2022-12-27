"""
Based on the pydantic BaseModel,
the EikoBaseModel allows for linking of Eiko resources
to a more easily useable python model.
"""
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from ._resource import EikoResourceDefinition


class EikoBaseModel(BaseModel):
    """
    Used to handily convert eikoclasses to python classes and back.
    """

    __eiko_resource__: ClassVar[str]
    __eiko_linked_definition__: ClassVar["EikoResourceDefinition"]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def link(cls, resource_cls: "EikoResourceDefinition") -> None:
        """Links a resource to a BaseModel."""
        cls.__eiko_linked_definition__ = resource_cls
        resource_cls.linked_basemodel = cls

    @classmethod
    def get_resource_name(cls) -> str:
        return cls.__eiko_resource__

    @classmethod
    def get_linked_definition(cls) -> "EikoResourceDefinition":
        return cls.__eiko_linked_definition__
