from typing import Optional, Any, List, Dict
from pydantic import (
    BaseModel,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
)


class OptionModel(BaseModel):
    headless: Optional[StrictBool] = None
    slow_mo: Optional[StrictInt] = None
    args: Optional[List[Any]] = None


class StepModel(BaseModel):
    func: StrictStr
    args: Dict


class DataToValidate(BaseModel):
    options: OptionModel
    steps: List[StepModel]


def validate(data):
    try:
        validated = DataToValidate(**data)
        return True, validated
    except ValidationError as e:
        error_message = {
            "message": "Erro de validação nos dados enviados.",
            "errors": [
                {
                    "loc": err["loc"],
                    "msg": err["msg"],
                    "type": err["type"]
                }
                for err in e.errors()
            ]
        }
        return False, error_message