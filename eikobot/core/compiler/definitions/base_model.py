"""
Based on the pydantic BaseModel,
the EikoBaseModel allows for linking of Eiko resources
to a more easily useable python model.
"""
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from ...errors import EikoCompilationError

if TYPE_CHECKING:
    from ._resource import EikoResourceDefinition
    from .base_types import EikoResource


class EikoBaseModel(BaseModel):
    """
    Used to handily convert eikoclasses to python classes and back.
    """

    raw_resource: Any
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
        """Returns the __eiko_resource__ class variable"""
        try:
            return cls.__eiko_resource__
        except AttributeError as e:
            raise EikoCompilationError(
                f"EikoBaseModel '{cls.__name__}' requires a `__eiko_resource__` field "
                "to link to it's resource."
            ) from e

    @classmethod
    def get_linked_definition(cls) -> "EikoResourceDefinition":
        return cls.__eiko_linked_definition__
