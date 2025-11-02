from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional


class ComputeRequest(BaseModel):
    mode: Literal["eval", "simplify", "differentiate", "integrate", "solve"]
    expr: str
    var: Optional[str] = None
    lower: Optional[str] = None
    upper: Optional[str] = None

    @field_validator("var")
    @classmethod
    def _var_required_for_modes(cls, v, info):
        mode = info.data.get("mode")
        if mode in {"differentiate", "integrate", "solve"} and not v:
            raise ValueError(
                "Variable 'var' must be provided for differentiate/integrate/solve modes"
            )
        return v

    @model_validator(mode="after")
    def _check_bounds(self):
        if self.mode == "integrate":
            # XOR check: one is set, but not both
            if bool(self.lower) ^ bool(self.upper):
                raise ValueError(
                    "For definite integrals, 'lower' and 'upper' bounds must be provided together or not at all"
                )
        return self
