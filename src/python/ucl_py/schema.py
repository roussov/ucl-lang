# =========================================================
# UCL Schema Engine — MAX ∞
# types / unions / refs / constraints / coercion / diagnostics
# =========================================================

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union


# ===================== Diagnostics =====================

@dataclass
class SchemaError:
    message: str
    path: List[str]

    def __str__(self):
        return f"{'.'.join(self.path)}: {self.message}"


# ===================== Base Type =====================

class Type:
    def validate(self, value: Any, path: List[str]):
        raise NotImplementedError


# ===================== Primitive Types =====================

class StringType(Type):
    def validate(self, value, path):
        if not isinstance(value, str):
            raise SchemaError("expected string", path)


class NumberType(Type):
    def validate(self, value, path):
        if not isinstance(value, (int, float)):
            raise SchemaError("expected number", path)


class BoolType(Type):
    def validate(self, value, path):
        if not isinstance(value, bool):
            raise SchemaError("expected boolean", path)


class NullType(Type):
    def validate(self, value, path):
        if value is not None:
            raise SchemaError("expected null", path)


# ===================== Complex Types =====================

class ListType(Type):
    def __init__(self, inner: Type):
        self.inner = inner

    def validate(self, value, path):
        if not isinstance(value, list):
            raise SchemaError("expected list", path)

        for i, v in enumerate(value):
            self.inner.validate(v, path + [str(i)])


class MapType(Type):
    def __init__(self, fields: Dict[str, "Field"], allow_extra=False):
        self.fields = fields
        self.allow_extra = allow_extra

    def validate(self, value, path):
        if not isinstance(value, dict):
            raise SchemaError("expected map", path)

        result = {}

        for k, field in self.fields.items():
            if k not in value:
                if field.required:
                    raise SchemaError(f"missing field '{k}'", path)
                result[k] = field.default
                continue

            result[k] = field.validate(value[k], path + [k])

        if not self.allow_extra:
            for k in value:
                if k not in self.fields:
                    raise SchemaError(f"unexpected field '{k}'", path)

        return result


# ===================== Advanced Types =====================

class UnionType(Type):
    def __init__(self, types: List[Type]):
        self.types = types

    def validate(self, value, path):
        errors = []

        for t in self.types:
            try:
                return t.validate(value, path)
            except SchemaError as e:
                errors.append(str(e))

        raise SchemaError(f"no union match: {errors}", path)


class EnumType(Type):
    def __init__(self, values: List[Any]):
        self.values = values

    def validate(self, value, path):
        if value not in self.values:
            raise SchemaError(f"must be one of {self.values}", path)


class OptionalType(Type):
    def __init__(self, inner: Type):
        self.inner = inner

    def validate(self, value, path):
        if value is None:
            return None
        return self.inner.validate(value, path)


# ===================== Field =====================

@dataclass
class Field:
    type: Type
    required: bool = True
    default: Any = None
    constraints: List[Callable[[Any], bool]] = field(default_factory=list)

    def validate(self, value, path):
        v = self.type.validate(value, path)

        for c in self.constraints:
            if not c(value):
                raise SchemaError("constraint failed", path)

        return v


# ===================== Schema =====================

@dataclass
class Schema:
    fields: Dict[str, Field]
    allow_extra: bool = False

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return MapType(self.fields, self.allow_extra).validate(data, [])


# ===================== Registry =====================

class SchemaRegistry:
    def __init__(self):
        self._schemas: Dict[str, Schema] = {}

    def register(self, name: str, schema: Schema):
        self._schemas[name] = schema

    def get(self, name: str) -> Schema:
        if name not in self._schemas:
            raise KeyError(f"schema not found: {name}")
        return self._schemas[name]


# ===================== Constraints =====================

def min_value(n: float):
    return lambda x: x >= n


def max_value(n: float):
    return lambda x: x <= n


def length(min_len: int = 0, max_len: Optional[int] = None):
    def _check(x):
        if len(x) < min_len:
            return False
        if max_len is not None and len(x) > max_len:
            return False
        return True
    return _check


# ===================== Coercion =====================

def coerce_number(x):
    if isinstance(x, (int, float)):
        return x
    try:
        return float(x)
    except Exception:
        raise ValueError("cannot coerce to number")


def coerce_bool(x):
    if x in [True, "true", "1", 1]:
        return True
    if x in [False, "false", "0", 0]:
        return False
    raise ValueError("cannot coerce to bool")


# ===================== Recursive Support =====================

class RefType(Type):
    def __init__(self, name: str, registry: SchemaRegistry):
        self.name = name
        self.registry = registry

    def validate(self, value, path):
        schema = self.registry.get(self.name)
        return schema.validate(value)


# ===================== Example =====================

if __name__ == "__main__":

    registry = SchemaRegistry()

    user_schema = Schema(fields={
        "name": Field(StringType()),
        "age": Field(NumberType(), constraints=[min_value(0), max_value(120)]),
        "role": Field(EnumType(["admin", "user"])),
        "meta": Field(OptionalType(MapType({}, allow_extra=True)), required=False),
    })

    registry.register("User", user_schema)

    data = {
        "name": "Alice",
        "age": 30,
        "role": "admin",
    }

    try:
        validated = user_schema.validate(data)
        print("VALID:", validated)
    except SchemaError as e:
        print("ERROR:", e)
