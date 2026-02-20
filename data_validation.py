from typing import Any
from pydantic import BaseModel, ValidationError
from enum import Enum
from typing import Optional
import log_config

class StepFunc(str, Enum):
    confirm_popup = "confirm_popup"
    backspace = "backspace"
    create_variables = "create_variables"
    go_to = "go_to"
    wait = "wait"
    read_attribute = "read_attribute"
    read_inner_text = "read_inner_text"
    insert = "insert"
    click = "click"
    select_option = "select_option"
    select = "select"
    save_file = "save_file"
    page_to_pdf = "page_to_pdf"
    set_timeout = "set_timeout"
    switch_page = "switch_page"
    execute_script = "execute_script"
    captcha_solver = "captcha_solver"
    request_pdf = "request_pdf"
    wait_url_change = "wait_url_change"

class Step(BaseModel):
    func: StepFunc
    args: dict[str, Any]

    class Config:
        extra = "forbid"


class DataRequest(BaseModel):
    timeout: Optional[int] = None
    steps: list[Step]
    browser_session: Optional[dict] = None
    class Config:
        extra = "forbid"




def validate(data):
    try:
        validated_data = DataRequest(**data).model_dump()
        return True, {
            "status": "success",
            "data": validated_data
        }
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            error_details.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "type": error["type"],
                "message": error["msg"],
                "input": error.get("input")
            })

        return False, {
            "status": "error",
            "error_count": len(e.errors()),
            "details": error_details
        }

