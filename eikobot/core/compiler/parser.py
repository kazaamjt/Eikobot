from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

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
from .errors import (
    EikoCompilationError,
    EikoInternalError,
    EikoParserError,
    EikoSyntaxError,
)
from .importer import resolve_import
from .lexer import Lexer
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

        elif isinstance(self.rhs, CallExprAst) and isinstance(lhs, CompilerContext):
            return self.rhs.compile(lhs)

        raise EikoCompilationError(
            "Unable to perform dot expression on given token.",
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

    def to_import_traversable_list(self, import_list: List[str]) -> None:
        if isinstance(self.lhs, VariableAST):
            import_list.append(self.lhs.identifier)
        else:
            raise EikoCompilationError(
                "Unexpected token in import statement.",
                token=self.lhs.token,
            )

        if isinstance(self.rhs, VariableAST):
            import_list.append(self.rhs.identifier)
        elif isinstance(self.rhs, DotExprAST):
            self.rhs.to_import_traversable_list(import_list)
        else:
            raise EikoCompilationError(
                "Unexpected token in import statement.",
                token=self.rhs.token,
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


@dataclass
class ImportExprAST(ExprAST):
    rhs: Union[VariableAST, DotExprAST]

    def compile(self, context: CompilerContext) -> None:
        import_list: List[str] = []
        if isinstance(self.rhs, VariableAST):
            import_list.append(self.rhs.identifier)
        else:
            self.rhs.to_import_traversable_list(import_list)

        resolve_result = resolve_import(import_list, context)
        if resolve_result is None:
            raise EikoCompilationError(
                "Failed to import module, module not found.", token=self.token
            )

        import_path, import_context = resolve_result

        parser = Parser(import_path)
        for expr in parser.parse():
            expr.compile(import_context)


class Parser:
    """
    Parses tokens 1 by 1, and turns them in to Expressions.
    """

    def __init__(self, file: Path) -> None:
        self.lexer = Lexer(file)
        self._current = self.lexer.next_token()
        self._next = self.lexer.next_token()
        self._bin_op_precedence = {
            "=": 10,
            "or": 20,
            "and": 30,
            "==": 50,
            "!=": 50,
            "<": 50,
            ">": 50,
            "<=": 50,
            ">=": 50,
            "+": 60,
            "-": 60,
            "*": 70,
            "/": 70,
            "//": 70,
            "%": 70,
            "u-": 80,
            "unot": 40,
            "**": 90,
            ".": 100,
        }

    def parse(self) -> Iterator[ExprAST]:
        """Parses tokens and constructs the next set of ASTs."""
        expr = self._parse_top_level()
        while not isinstance(expr, EOFExprAST):
            yield expr
            expr = self._parse_top_level()

    def print_op_precedence(self) -> None:
        """outputs every level and ops associated with said level."""
        op_precedents: Dict[int, List[str]] = {}
        for key, value in self._bin_op_precedence.items():
            _list = op_precedents.get(value)
            if _list is None:
                _list = []
                op_precedents[value] = _list
            _list.append(key)

        for level, _list in sorted(op_precedents.items()):
            print(f"{level}: [", ", ".join(_list), "]")

    def _advance(self, skip_indentation: bool = False) -> None:
        self._current = self._next
        self._next = self.lexer.next_token()

        if skip_indentation and self._current.type == TokenType.INDENT:
            self._advance(skip_indentation)

        if (
            self._current.type == TokenType.STRING
            and self._next.type == TokenType.STRING
        ):
            self._next = Token(
                TokenType.STRING,
                self._current.content + self._next.content,
                self._current.index,
            )
            self._advance(skip_indentation)

        if (
            self._current.type == TokenType.INDENT
            and self._current.content == ""
            and self._next.type == TokenType.INDENT
        ):
            self._advance()

    def _parse_top_level(self) -> ExprAST:
        if self._current.type != TokenType.INDENT or self._current.content != "":
            raise EikoParserError(
                f"Unexpected token: {self._current.content}.", token=self._current
            )

        self._advance()
        if self._current.type == TokenType.EOF:
            return EOFExprAST(self._current)

        if self._current.type == TokenType.RESOURCE:
            return self._parse_resource_definition()

        if self._current.type == TokenType.IMPORT:
            return self._parse_import()

        return self._parse_expression()

    def _parse_expression(self, precedence: int = 0) -> ExprAST:
        lhs = self._parse_primary()
        return self._parse_bin_op_rhs(precedence, lhs)

    def _parse_primary(self) -> ExprAST:
        if self._current.type == TokenType.INDENT:
            if self._current.content == "":
                self._advance()
                return self._parse_primary()

        if self._current.content in ["-", "not"]:
            return self._parse_unary_op()

        if self._current.type == TokenType.INTEGER:
            token = self._current
            self._advance()
            return IntExprAST(token)

        if self._current.type == TokenType.FLOAT:
            token = self._current
            self._advance()
            return FloatExprAST(token)

        if self._current.type == TokenType.STRING:
            token = self._current
            self._advance()
            return StringExprAST(token)

        if self._current.type == TokenType.LEFT_PAREN:
            return self._parse_parens()

        if self._current.type == TokenType.IDENTIFIER:
            return self._parse_identifier()

        raise EikoSyntaxError(f"Unexpected token {self._current.type.name}.")

    def _parse_unary_op(self) -> Union[UnaryNegExprAST, UnaryNotExprAST]:
        token = self._current
        self._advance()
        if token.content == "-":
            rhs = self._parse_expression(self._bin_op_precedence["u-"])
            return UnaryNegExprAST(token, rhs)

        rhs = self._parse_expression(self._bin_op_precedence["unot"])
        return UnaryNotExprAST(token, rhs)

    def _parse_parens(self) -> ExprAST:
        self._advance(skip_indentation=True)
        next_expr = self._parse_expression()
        if self._current.type != TokenType.RIGHT_PAREN:
            raise EikoParserError("Unexpected token.", token=self._current)

        self._advance()
        return next_expr

    def _parse_bin_op_rhs(self, expr_precedence: int, lhs: ExprAST) -> ExprAST:
        while True:
            current_predecedence = self._bin_op_precedence.get(self._current.content, 0)
            if current_predecedence < expr_precedence:
                return lhs
            if self._current.type in [
                TokenType.INDENT,
                TokenType.RIGHT_PAREN,
                TokenType.COMMA,
            ]:
                return lhs

            bin_op_token = self._current
            self._advance()
            rhs = self._parse_primary()

            # if current op binds less tightly with rhs than the operator after rhs,
            # let the pending operator take rhs as it's lhs
            next_op_precedence = self._bin_op_precedence.get(self._current.content, 0)
            if expr_precedence < next_op_precedence:
                rhs = self._parse_bin_op_rhs(current_predecedence + 1, rhs)

            if bin_op_token.type == TokenType.ASSIGNMENT_OP:
                lhs = AssignmentAST(bin_op_token, lhs, rhs)
            elif bin_op_token.type == TokenType.DOT:
                lhs = DotExprAST(bin_op_token, lhs, rhs)
            else:
                lhs = BinOpExprAST(bin_op_token, lhs, rhs)

    def _parse_identifier(self) -> Union[VariableAST, CallExprAst]:
        token = self._current
        self._advance()
        if self._current.type == TokenType.LEFT_PAREN:
            self._advance()
            return self._parse_call_expr(token)

        return VariableAST(token)

    def _parse_call_expr(self, name_token: Token) -> CallExprAst:
        call_ast = CallExprAst(name_token)
        while True:
            expr = self._parse_expression()
            call_ast.add_arg(expr)
            if self._current.type == TokenType.RIGHT_PAREN:
                self._advance()
                break

            if self._current.type != TokenType.COMMA:
                raise EikoCompilationError(
                    "Unexpected token. Expected a comma or right parenthesis.",
                    token=self._current,
                )
            self._advance()
            if self._current.type == TokenType.RIGHT_PAREN:
                break

        return call_ast

    def _parse_resource_definition(self) -> ResourceDefinitionAST:
        if self._next.type != TokenType.IDENTIFIER:
            raise EikoCompilationError(
                f"Unexpected token {self._next.content}, "
                "expected resource identifier.",
                token=self._next,
            )

        rd_ast = ResourceDefinitionAST(self._current, self._next.content)

        self._advance()
        self._advance()

        if self._current.content != ":":
            raise EikoCompilationError(
                f"Unexpected token {self._current.content}.",
                token=self._current,
            )

        self._advance()
        if self._current.type != TokenType.INDENT:
            raise EikoCompilationError(
                f"Unexpected token {self._current.content}, "
                "expected indented code block.",
                token=self._current,
            )

        indent = self._current.content
        while self._current.type == TokenType.INDENT:
            if self._current.content == "":
                break
            if self._current.content != indent:
                raise EikoCompilationError(
                    "Unexpected indentation.",
                    token=self._current,
                )
            self._advance()
            prop = self._parse_resource_property()
            rd_ast.add_property(prop)

        return rd_ast

    def _parse_resource_property(self) -> ResourceProperty:
        if self._current.type != TokenType.IDENTIFIER:
            raise EikoCompilationError(
                "Unexpected token. Expected a property identifier.",
                token=self._current,
            )

        token = self._current
        name = self._current.content
        default_value = None

        self._advance()
        if self._current.content == ":":
            self._advance()
            if self._current.type != TokenType.IDENTIFIER:
                raise EikoCompilationError(
                    "Unexpected token. Expected a type identifier.",
                    token=self._current,
                )
            prop_type = self._current.content
            self._advance()

        else:
            raise EikoCompilationError(
                "Unexpected token. Expected a type identifier.",
                token=self._current,
            )

        return ResourceProperty(name, prop_type, default_value, token)

    def _parse_import(self) -> ImportExprAST:
        token = self._current
        self._advance()
        rhs = self._parse_expression()

        if isinstance(rhs, (VariableAST, DotExprAST)):
            return ImportExprAST(token, rhs)

        raise EikoCompilationError(
            "Unable to import given expression.",
            token=token,
        )
