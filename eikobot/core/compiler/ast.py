from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from .definitions.base_types import (
    EikoBaseType,
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoResource,
    EikoStr,
)
from .definitions.context import CompilerContext, StorableTypes
from .definitions.function import FunctionArg, FunctionDefinition
from .definitions.resource import ResourceDefinition, ResourceProperty
from .errors import EikoCompilationError, EikoInternalError
from .ops import BINOP_MATRIX, BinOP
from .token import Token, TokenType


@dataclass
class ExprAST:
    """Base ExprAST. Purely Virtual."""

    token: Token

    def compile(self, _: CompilerContext) -> Optional[StorableTypes]:
        raise NotImplementedError


@dataclass
class EOFExprAST(ExprAST):
    """This ExprAST marks end of parsing."""

    def compile(self, _: CompilerContext) -> None:
        raise NotImplementedError


@dataclass
class IntExprAST(ExprAST):
    """AST representing an integer in the source"""

    def __post_init__(self) -> None:
        self.value = int(self.token.content)

    def compile(self, _: CompilerContext) -> EikoInt:
        return EikoInt(self.value)


@dataclass
class FloatExprAST(ExprAST):
    """AST representing a float in the source."""

    def __post_init__(self) -> None:
        self.value = float(self.token.content)

    def compile(self, _: CompilerContext) -> EikoFloat:
        return EikoFloat(self.value)


@dataclass
class BoolExprAST(ExprAST):
    """AST representing a bool in the source."""

    def __post_init__(self) -> None:
        if self.token.type == TokenType.FALSE:
            self.value = False
        elif self.token.type == TokenType.TRUE:
            self.value = True
        else:
            raise EikoInternalError(
                "Error occured trying to compile BoolExprAST. "
                "This is deffinetly a bug, please report it on github."
            )

    def compile(self, _: CompilerContext) -> EikoBool:
        return EikoBool(self.value)


@dataclass
class StringExprAST(ExprAST):
    """AST representing a string in the source."""

    def __post_init__(self) -> None:
        self.value = self.token.content

    def compile(self, _: CompilerContext) -> EikoStr:
        return EikoStr(self.value)


@dataclass
class UnaryNotExprAST(ExprAST):
    """AST representing a unary not operation."""

    rhs: ExprAST

    def compile(self, _: CompilerContext) -> EikoBaseType:
        raise NotImplementedError


@dataclass
class UnaryNegExprAST(ExprAST):
    """AST representing a unary negative operation."""

    rhs: ExprAST

    def compile(self, context: CompilerContext) -> Union[EikoInt, EikoFloat]:
        rhs = self.rhs.compile(context)
        if isinstance(rhs, EikoInt):
            return EikoInt(-rhs.value)

        if isinstance(rhs, EikoFloat):
            return EikoFloat(-rhs.value)

        if rhs is None:
            raise EikoCompilationError(
                "Unary negative expected value to the right hand side, "
                "but expression didn't return a usable value.",
                token=self.token,
            )

        raise EikoCompilationError(
            f"Unable to perform unary negative on object of type {rhs.type}",
            token=self.token,
        )


@dataclass
class BinOpExprAST(ExprAST):
    """A binary operation taking a left and right hand side."""

    lhs: ExprAST
    rhs: ExprAST

    def __post_init__(self) -> None:
        self.bin_op = BinOP.from_str(self.token.content)

    def compile(self, context: CompilerContext) -> EikoBaseType:
        lhs = self.lhs.compile(context)
        if lhs is None:
            raise EikoCompilationError(
                "Binary operation expected value on left hand side, "
                "but expression didn't return a usable value.",
                token=self.token,
            )

        rhs = self.rhs.compile(context)
        if rhs is None:
            raise EikoCompilationError(
                "Binary operation expected value on right hand side, "
                "but expression didn't return a usable value.",
                token=self.token,
            )

        arg_a_matrix = BINOP_MATRIX.get(lhs.type)
        if arg_a_matrix is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        arg_b_matrix = arg_a_matrix.get(rhs.type)
        if arg_b_matrix is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        op = arg_b_matrix.get(self.bin_op)
        if op is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        return op(lhs, rhs)  # type: ignore


@dataclass
class VariableAST(ExprAST):
    def __post_init__(self) -> None:
        self.identifier = self.token.content

    def compile(self, context: Union[CompilerContext, EikoBaseType]) -> StorableTypes:
        value = context.get(self.identifier)
        if value is None:
            raise EikoCompilationError(
                f"Variable {self.identifier} was accessed before "
                "having been assigned a value.",
                token=self.token,
            )

        return value


@dataclass
class AssignmentAST(ExprAST):
    lhs: ExprAST
    rhs: ExprAST

    def compile(self, context: CompilerContext) -> StorableTypes:
        assignment_val = self.rhs.compile(context)
        if assignment_val is None:
            raise EikoCompilationError(
                "Assignment operation expected value on right hand side, "
                "but expression didn't return a usable value.",
                token=self.rhs.token,
            )

        if isinstance(self.lhs, VariableAST):
            context.set(self.lhs.token.content, assignment_val, self.token)
            return assignment_val

        if isinstance(self.lhs, DotExprAST):
            return self.lhs.assign(assignment_val, context)

        raise EikoCompilationError(
            "Assignment operation expected assignable variable on left hand side",
            token=self.token,
        )


@dataclass
class DotExprAST(ExprAST):
    lhs: ExprAST
    rhs: ExprAST

    def compile(self, context: CompilerContext) -> Optional[StorableTypes]:
        lhs = self.lhs.compile(context)
        if isinstance(self.rhs, VariableAST) and isinstance(lhs, EikoBaseType):
            return self.rhs.compile(lhs)

        elif isinstance(self.rhs, CallExprAst) and isinstance(lhs, ResourceDefinition):
            return self.rhs.compile(lhs)

        raise EikoCompilationError(
            "Unable to perform dit expression on given token.",
            token=self.lhs.token,
        )

    def assign(self, value: StorableTypes, context: CompilerContext) -> StorableTypes:
        lhs = self.lhs.compile(context)
        if isinstance(lhs, EikoResource):
            if isinstance(self.rhs, VariableAST):
                lhs.set(self.rhs.identifier, value, self.rhs.token)
                return value

            raise EikoCompilationError(
                f"Tried to assign value to {self.lhs.token.content}."
                f"{self.rhs.token.content}, but this is not a valid expression.",
                token=self.rhs.token,
            )
        raise EikoCompilationError(
            f"Tried to assign value to {self.lhs.token.content}."
            f"{self.rhs.token.content}, but this is not a valid expression.",
            token=self.lhs.token,
        )


@dataclass
class CallExprAst(ExprAST):
    def __post_init__(self) -> None:
        self.identifier = self.token.content
        self.args: List[ExprAST] = []

    def add_arg(self, expr: ExprAST) -> None:
        self.args.append(expr)

    def compile(
        self, context: Union[CompilerContext, EikoBaseType, ResourceDefinition]
    ) -> Optional[EikoBaseType]:
        eiko_callable: Optional[StorableTypes] = None
        if isinstance(context, CompilerContext):
            resource_definition = context.get(self.identifier)
            if isinstance(resource_definition, ResourceDefinition):
                eiko_callable = resource_definition.get(self.identifier)
        else:
            eiko_callable = context.get(self.identifier)
        if isinstance(context, EikoBaseType):
            raise EikoInternalError(
                "Something went wrong, an EikoBaseType was passed to "
                "CallExprAST.compile instead of a CompilerContext. "
                "Please report this."
            )

        if isinstance(eiko_callable, FunctionDefinition):
            func_context = CompilerContext(f"func-{self.identifier}", context)
            self_arg = eiko_callable.args[0]
            resource = EikoResource(self_arg.type)
            func_context.set(self_arg.name, resource)
            for passed_arg, arg_definition in zip(self.args, eiko_callable.args[1:]):
                value = passed_arg.compile(func_context)
                if value is None:
                    raise EikoInternalError(
                        "Encountered bad value during compilation. "
                        "This is most likely a bug.\n"
                        "Please report this. (Value of parameter was Python None).\n"
                        f"Related token: {passed_arg.token}."
                    )
                if value.type != arg_definition.type:
                    raise EikoCompilationError(
                        "Bad value was passed. Expected ",
                        token=passed_arg.token,
                    )
                func_context.set(arg_definition.name, value)
            eiko_callable.execute(func_context)
            return resource

        if eiko_callable is None:
            raise EikoCompilationError(
                f"No callable {self.identifier}.",
                token=self.token,
            )

        raise EikoCompilationError(
            f"{self.identifier} is not a callable.",
            token=self.token,
        )


@dataclass
class ResourceDefinitionAST(ExprAST):
    name: str

    def __post_init__(self) -> None:
        self.properties: Dict[str, ResourceProperty] = {}

    def add_property(self, new_property: ResourceProperty) -> None:
        existing_property = self.properties.get(new_property.name)
        if existing_property is not None:
            raise EikoCompilationError(
                f"Redefining property {new_property.name} "
                f"for Resource type {self.name}. ",
                "Reassigning of property values is not allowed.",
                token=new_property.token,
            )

        self.properties[new_property.name] = new_property

    def compile(self, context: CompilerContext) -> ResourceDefinition:
        resource_definition = ResourceDefinition(self.name, self.properties, self.token)

        default_constructor = FunctionDefinition()
        default_constructor.add_arg(FunctionArg("self", self.name))
        for prop in self.properties.values():
            default_constructor.add_arg(
                FunctionArg(prop.name, prop.type, prop.default_value)
            )
            token = prop.token
            if token is None:
                token = Token(TokenType.IDENTIFIER, prop.name, self.token.index)
            default_constructor.add_body_expr(
                AssignmentAST(
                    self.token,
                    DotExprAST(
                        Token(TokenType.DOT, ".", token.index),
                        VariableAST(Token(TokenType.IDENTIFIER, "self", token.index)),
                        VariableAST(token),
                    ),
                    VariableAST(token),
                ),
            )

        resource_definition.add_constructor(self.name, default_constructor)
        context.set(self.name, resource_definition, self.token)

        return resource_definition
