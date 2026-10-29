
import ast
import math
import operator
import re


BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "factorial": math.factorial,
    "abs": abs,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


class MathError(ValueError):
    pass


def evaluate_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise MathError("Boolean values are not supported.")
        if isinstance(node.value, (int, float)):
            return node.value
        raise MathError("Only numeric constants are allowed.")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)

        if op_type not in BINARY_OPERATORS:
            raise MathError("Unsupported operator.")

        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        if op_type is ast.Pow and abs(right) > 1000:
            raise MathError("Exponent is too large.")

        if op_type in (ast.Mult, ast.Pow) and (
            abs(left) > 1e100 or abs(right) > 1e100
        ):
            raise MathError("Number is too large.")

        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise MathError("Division by zero is undefined.")

        result = BINARY_OPERATORS[op_type](left, right)

        if isinstance(result, complex):
            raise MathError("Complex results are not supported yet.")

        if isinstance(result, (int, float)) and not math.isfinite(result):
            raise MathError("Result is not finite.")

        if isinstance(result, int) and result.bit_length() > 4096:
            raise MathError("Result is too large.")

        return result

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)

        if op_type not in UNARY_OPERATORS:
            raise MathError("Unsupported unary operator.")

        return UNARY_OPERATORS[op_type](evaluate_node(node.operand))

    if isinstance(node, ast.Name):
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise MathError(f"Unknown constant: {node.id}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise MathError("Unsupported function call.")

        name = node.func.id

        if name not in FUNCTIONS or node.keywords:
            raise MathError(f"Unsupported function: {name}")

        args = [evaluate_node(arg) for arg in node.args]

        if len(args) != 1:
            raise MathError("Functions currently accept one argument.")

        return FUNCTIONS[name](*args)

    raise MathError("Unsupported expression.")


def format_result(value):
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MathError("Result is not finite.")
        if value.is_integer():
            return str(int(value))
        return f"{value:.12g}"

    return str(value)


def solve_math(question):
    text = question.strip().lower()

    # Remove common question phrases only at the edges.
    text = re.sub(
        r"^(what is|calculate|solve|find|kitna hota hai|kitna hota h)\s*",
        "",
        text,
    )
    text = re.sub(
        r"\s*(kitna hota hai|kitna hota h|equals|equal to|\?)$",
        "",
        text,
    )

    # Support multiplication and division symbols.
    text = text.replace("×", "*").replace("÷", "/")

    # Reject arbitrary natural-language sentences.
    if not text or len(text) > 200:
        return None

    if not re.fullmatch(
        r"[0-9a-z+\-*/().,%\s]+",
        text,
    ):
        return None

    # A math expression must contain a digit or a known constant/function.
    if not re.search(r"\d", text) and not re.search(
        r"\b(?:pi|e|sqrt|sin|cos|tan|log|log10|factorial|abs)\b",
        text,
    ):
        return None

    # Avoid accidentally interpreting a sentence containing a number.
    remainder = re.sub(
        r"\b(?:pi|e|sqrt|sin|cos|tan|log|log10|factorial|abs)\b",
        "",
        text,
    )
    if re.search(r"[a-df-hj-oq-z]", remainder):
        return None

    try:
        tree = ast.parse(text, mode="eval")
        result = evaluate_node(tree.body)
        return f"{question.strip()} = {format_result(result)}"
    except (SyntaxError, MathError, ArithmeticError, ValueError, OverflowError):
        return None


if __name__ == "__main__":
    tests = [
        "2+2+6 kitna hota h",
        "12 * (3 + 2)",
        "sqrt(81)",
        "2 ** 10",
        "10 / 0",
    ]

    for question in tests:
        print(question, "->", solve_math(question))
