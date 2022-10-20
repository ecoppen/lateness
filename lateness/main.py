import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lateness.core.config import load_config
from lateness.core.utils import chunks
from lateness.models.database import Database

logs_file = Path(Path().resolve(), "log.txt")
logs_file.touch(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO"),
    handlers=[logging.FileHandler(logs_file), logging.StreamHandler()],
)

log = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

config_path = Path(Path().resolve(), "config", "config.json")
config = load_config(path=config_path)
log.info(f"{config_path} loaded")

database = Database(config=config.database)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, error: str = "", success: str = ""):
    data: dict = {"page": "index", "years": []}
    try:
        years = get_year_data()
    except OSError:
        return refresh(request=request)
    except urllib.error.HTTPError:
        return refresh(request=request)
    data["years"] = chunks(years["years"], 2)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": data, "error": error, "success": success},
    )


@app.get("/refresh", response_class=HTMLResponse)
def refresh(request: Request):
    data: dict = {"page": "refresh"}
    return templates.TemplateResponse(
        "refresh.html",
        {"request": request, "data": data},
    )


@app.get("/forms", response_class=HTMLResponse)
def read_forms(request: Request, year: int, error: str = ""):
    data: dict = {"page": "forms", "forms": []}
    years = get_year_data()
    if year not in years["years"]:
        return read_root(request=request, error=f"{year} is not in {years['years']}")
    forms = get_year_data(year=year)
    if len(forms["forms"]) < 1:
        return read_root(request=request, error=f"There are no groups in year {year}")
    data["forms"] = chunks(lst=forms["forms"], n=3)
    return templates.TemplateResponse(
        "forms.html", {"request": request, "data": data, "error": error}
    )


@app.get("/form", response_class=HTMLResponse)
def read_form(request: Request, form: str, error: str = ""):
    data: dict = {"page": "form", "form": form, "students": []}
    years = get_year_data()
    year = int(form[:-1])
    if year not in years["years"]:
        return read_root(request=request, error=f"{year} is not in {years['years']}")
    forms = get_year_data(year=year)
    if len(forms["forms"]) < 1:
        return read_root(request=request, error=f"There are no groups in year {year}")
    if form not in forms["forms"]:
        return read_forms(
            request=request, year=year, error=f"{form} is not in {forms['forms']}"
        )
    form_group: dict[str, list] = get_year_data(form=form)
    if len(form_group["students"]) < 1:
        return read_forms(year=year, error=f"There are no students in {form_group}")
    form_group["students"].sort(key=lambda k: k["Surname"])
    data["students"] = chunks(lst=form_group["students"], n=3)
    return templates.TemplateResponse(
        "form.html", {"request": request, "data": data, "error": error}
    )


@app.post("/scan_student")
async def scan_student(request: Request, cardid: str = Form()):
    upn = get_upn_from_card(card=cardid)
    if len(upn["UPN"]) < 1:
        return read_root(request=request, error="Card is invalid")
    return read_student(request=request, upn=upn["UPN"])


@app.get("/student", response_class=HTMLResponse)
def read_student(request: Request, upn: str, error: str = ""):
    data: dict = {"page": "student", "photo": "", "upn": upn, "information": {}}
    if len(upn) != 13:
        return read_root(
            request=request, error=f"{upn} is invalid - it must be 13 characters long"
        )
    if check_image_exists(upn=upn):
        data["photo"] = f"http://{config.api_get}/img/student-photos/{upn}.jpg"
    data["information"] = get_details_from_upn(upn=upn)
    if "Forename" not in data["information"]:
        return read_root(request=request, error=f"Student with upn {upn} not found")
    if len(data["information"]["Forename"]) < 1:
        return read_root(
            request=request, error=f"Student with upn {upn} does not  exist"
        )
    data["information"]["DOB"] = datetime.strptime(
        data["information"]["DOB"], "%Y-%m-%d"
    )
    data["information"]["DOB"] = datetime.strftime(
        data["information"]["DOB"], "%d/%m/%Y"
    )
    return templates.TemplateResponse(
        "student.html", {"request": request, "data": data, "error": error}
    )


@app.get("/year")
def show_form_groups(year: int):
    data = get_year_data(year)
    return data


@app.get("/get_year_data")
def get_year_data(year: Union[None, int] = None, form: Union[None, str] = None):
    url_string = f"http://{config.api_get}/lateness_year_groups.php"
    log.info(f"Requesting: {url_string}")
    with urllib.request.urlopen(url_string) as url:  # nosec
        data = json.load(url)
    if year is None and form is None:
        return data
    if form is None:
        if year in data["years"]:
            url_string = f"http://{config.api_get}/lateness_year_groups.php?year={year}"
            log.info(f"Requesting: {url_string}")
            with urllib.request.urlopen(url_string) as url:  # nosec
                data = json.load(url)

    if year is None:
        year_group: int = int(str(form)[:-1])
        if year_group in data["years"]:
            url_string = (
                f"http://{config.api_get}/lateness_year_groups.php?year={year_group}"
            )
            log.info(f"Requesting: {url_string}")
            with urllib.request.urlopen(url_string) as url:  # nosec
                validation_data = json.load(url)
            if form in validation_data["forms"]:
                url_string = (
                    f"http://{config.api_get}/lateness_year_groups.php?form={form}"
                )
                log.info(f"Requesting: {url_string}")
                with urllib.request.urlopen(url_string) as url:  # nosec
                    data = json.load(url)
    return data


@app.get("/get_upn_from_card")
def get_upn_from_card(card: str):
    url_string = f"http://{config.api_get}/lateness_card_check.php?cardid={card}"
    with urllib.request.urlopen(url_string) as url:  # nosec
        data = json.load(url)
    return data


@app.get("/get_details_from_upn")
def get_details_from_upn(upn: str):
    url_string = f"http://{config.api_get}/lateness_upn_check.php?upn={upn}"
    log.info(f"Requesting: {url_string}")
    with urllib.request.urlopen(url_string) as url:  # nosec
        data = json.load(url)
    return data


@app.get("/check_image_exists")
def check_image_exists(upn: str):
    if len(upn) != 13:
        return False
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    url_string = f"http://{config.api_get}/img/student-photos/{upn}.jpg"
    log.info(f"Requesting: {url_string}")
    try:
        header = urllib.request.urlopen(url_string).getheader("content-type")  # nosec
    except urllib.error.HTTPError:
        return False
    if header in image_formats:
        return True
    return False


@app.post("/lateness_send")
async def lateness_send(request: Request, upn: str, reason: str = Form()):
    today = datetime.now()
    start_time = datetime.combine(today, config.start_time)
    end_time = datetime.combine(today, config.end_time)

    if today < start_time or today > end_time:
        return read_student(
            request=request,
            upn=upn,
            error="Current time is outside the lateness logging hours",
        )

    if len(upn) != 13:
        return read_root(
            request=request, error=f"{upn} is invalid - it must be 13 characters long"
        )

    upn_check = get_details_from_upn(upn=upn)
    if "Forename" not in upn_check:
        return read_root(request=request, error=f"Student with upn {upn} not found")
    if len(upn_check["Forename"]) < 1:
        return read_root(
            request=request, error=f"Student with upn {upn} does not  exist"
        )

    last_lateness = database.get_last_lateness(upn)
    if last_lateness is not None:
        if last_lateness[3].date() == datetime.today().date():
            return read_student(
                request=request,
                upn=upn,
                error="Student has already been logged late for today",
            )
        database.insert_lateness(upn=upn, reason=reason)
    else:
        database.insert_lateness(upn=upn, reason=reason)

    data: dict = {
        "upn": upn,
        "reason": reason,
        "datetime": today.strftime("%Y-%m-%d %H:%M:%S"),
    }
    encoded_data = urllib.parse.urlencode(data).encode()
    url_string = f"http://{config.api_get}/lateness_add_instance.php"
    req = urllib.request.Request(url_string, data=encoded_data, method="POST")
    response = urllib.request.urlopen(req)  # nosec
    response_code = response.read().decode("utf-8")
    if response_code == "1":
        log.info(f"Lateness logged for {upn}")
        return read_root(
            request=request,
            success=f"Instance of lateness saved for {upn_check['Forename']}",
        )
    else:
        log.warning(
            f"Lateness not logged for {upn} with reason {reason} on {datetime} - code: {response_code}"
        )
        return read_root(
            request=request,
            error=f"Instance of lateness not saved for {upn_check['Forename']}, see logs",
        )
