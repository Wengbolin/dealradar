import json
from market_control import generate_strategy

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):

    try:
        with open("arbitrage_cache.json", "r") as f:
            deals = json.load(f)
    except:
        deals = []

    strategy_list = generate_strategy(deals)
    strategy = strategy_list[0] if strategy_list else None

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "strategy": strategy
        }
    )

@router.get("/feed", response_class=HTMLResponse)
def feed(request: Request):
    return templates.TemplateResponse("feed.html", {"request": request})

@router.get("/models", response_class=HTMLResponse)
def models(request: Request):
    return templates.TemplateResponse("models.html", {"request": request})

@router.get("/deals", response_class=HTMLResponse)
def deals(request: Request):
    return templates.TemplateResponse("deals.html", {"request": request})

@router.get("/radar", response_class=HTMLResponse)
def radar(request: Request):
    return templates.TemplateResponse("radar.html", {"request": request})

@router.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/account", response_class=HTMLResponse)
def account(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})

@router.get("/cancel", response_class=HTMLResponse)
def cancel(request: Request):
    return templates.TemplateResponse("cancel.html", {"request": request})

@router.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

@router.get("/signals", response_class=HTMLResponse)
def signals(request: Request):
    return templates.TemplateResponse("signals.html", {"request": request})

@router.get("/success")
def success():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/account")
