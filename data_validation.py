from typing import Any, List
from pydantic import BaseModel, StrictBool, StrictInt, ValidationError
from enum import Enum
from typing import Optional


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


class Options(BaseModel):
    headless: StrictBool
    slow_mo: StrictInt
    args: List[Any]

    class Config:
        extra = "forbid"


class Step(BaseModel):
    func: StepFunc
    args: dict[str, Any]

    class Config:
        extra = "forbid"


class DataRequest(BaseModel):
    options: Options
    steps: list[Step]
    browser_session: Optional[dict] = None

    class Config:
        extra = "forbid"




def validate(data):
    try:
        return True, DataRequest(**data).model_dump()
    except ValidationError as e:
        return False, {
            "loc": e.errors()[0]["loc"],
            "message": e.errors()[0]["msg"]
            } 
        
