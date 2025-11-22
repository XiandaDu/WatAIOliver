from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
from typing import Optional
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application
)
import asyncio
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FutureTimeoutError

MAX_Expr_LEN = 500
TIMEOUT_SECONDS = 3.0
MAX_WORKERS = 2

# whitelisted functions
ALLOWED_MATH = {
    'pi': sp.pi, 'E': sp.E, 'e': sp.E, 'I': sp.I,
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
    'exp': sp.exp, 'log': sp.log, 'ln': sp.ln,
    'sqrt': sp.sqrt, 'root': sp.root, 'Abs': sp.Abs,
    'factorial': sp.factorial, 'gamma': sp.gamma,
}

# data models
class ComputeMode(str, Enum):
    eval = "eval"
    simplify = "simplify"
    factor = "factor"
    differentiate = "differentiate"
    integrate = "integrate"
    solve = "solve"

class ComputeRequest(BaseModel):
    mode: ComputeMode
    expr: str
    var: Optional[str] = None
    lower_bound: Optional[float] = None 
    upper_bound: Optional[float] = None

class ComputeResponse(BaseModel):
    result: Optional[str] = None
    latex: Optional[str] = None
    error_code: Optional[str] = None
    message: str

# core logic functions
def _cpu_bound_worker(mode: str, expr_str: str, var_str: Optional[str], lb, ub) -> dict:
    try:
        # sanitize input (fix for ^ vs ** error)
        expr_str = expr_str.replace('^', '**')

        # robust parsing
        transformations = (standard_transformations + (implicit_multiplication_application,))
        expr = parse_expr(expr_str, local_dict=ALLOWED_MATH, transformations=transformations)
        var = sp.Symbol(var_str) if var_str else None
        result = None

        # execution logic
        if mode == "eval":
            result = sp.N(expr)
        elif mode == "simplify":
            result = sp.simplify(expr)
        elif mode == "factor":
            result = sp.factor(expr)
        elif mode == "differentiate":
            if not var: return {"error": "missing_param", "msg": "Variable required"}
            result = sp.diff(expr, var)
        elif mode == "integrate":
            if not var: return {"error": "missing_param", "msg": "Variable required"}
            if lb is not None and ub is not None:
                result = sp.integrate(expr, (var, lb, ub))
            else:
                result = sp.integrate(expr, var)
            # fallback for unevaluated integrals
            if isinstance(result, sp.Integral):
                if lb is not None and ub is not None:
                    result = result.evalf()
                else:
                    return {
                        "result": str(result).replace('**', '^'),
                        "latex": sp.latex(result),
                        "msg": "No closed-form solution found"
                    }
        elif mode == "solve":
            if not var: return {"error": "missing_param", "msg": "Variable required"}
            sol_set = sp.solveset(expr, var, domain=sp.S.Complexes)
            result = sol_set.tolist() if hasattr(sol_set, 'tolist') else sol_set

        return {
            "result": str(result).replace('**', '^'),
            "latex": sp.latex(result),
            "msg": "success"
        }
    except Exception as e:
        return {"error": "calc_error", "msg": str(e)}

# main api app
app = FastAPI(title="Robust Calculator Microservice")
process_pool = ProcessPoolExecutor(max_workers=MAX_WORKERS)

@app.on_event("shutdown")
def shutdown_event():
    process_pool.shutdown(wait=False)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/compute", response_model=ComputeResponse)
async def compute(request: ComputeRequest):
    if len(request.expr) > MAX_Expr_LEN:
        return ComputeResponse(error_code="length_error", message="Expression too long")
    
    loop = asyncio.get_running_loop()
    try:
        future = loop.run_in_executor(
            process_pool, _cpu_bound_worker,
            request.mode.value, request.expr, request.var, request.lower_bound, request.upper_bound
        )
        data = await asyncio.wait_for(future, timeout=TIMEOUT_SECONDS)
        
        if "error" in data:
            return ComputeResponse(error_code=data["error"], message=data["msg"])
            
        return ComputeResponse(result=data["result"], latex=data.get("latex"), message=data["msg"])

    except asyncio.TimeoutError:
        return ComputeResponse(error_code="timeout", message=f"Computation exceeded {TIMEOUT_SECONDS}s limit")
    except Exception as e:
        return ComputeResponse(error_code="system_error", message=str(e))