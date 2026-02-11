from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.db import Base, engine
from app.routers import items, purchase, slots


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Vending Machine API", lifespan=lifespan)


# -------------------------------
# Centralized Exception Handler
# -------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    error_type = exc.args[0]

    if error_type == "slot_not_found":
        return JSONResponse(status_code=404, content={"detail": "Slot not found"})

    if error_type == "item_not_found":
        return JSONResponse(status_code=404, content={"detail": "Item not found"})

    if error_type == "slot_not_empty":
        return JSONResponse(
            status_code=400,
            content={"detail": "Cannot delete slot with items inside"},
        )

    if error_type == "out_of_stock":
        return JSONResponse(
            status_code=400,
            content={"detail": {"error": "Item out of stock"}},
        )

    if error_type == "invalid_quantity":
        return JSONResponse(status_code=400, content={"detail": "Invalid quantity"})

    if error_type == "quantity_exceeds_stock":
        return JSONResponse(
            status_code=400,
            content={"detail": "Quantity exceeds available stock"},
        )

    if error_type == "capacity_exceeded":
        return JSONResponse(
            status_code=400,
            content={"detail": "Total items would exceed slot capacity"},
        )

    if error_type == "invalid_price":
        return JSONResponse(status_code=400, content={"detail": "Invalid price"})

    if error_type == "unsupported_denomination":
        return JSONResponse(
            status_code=400,
            content={"detail": "Unsupported denomination"},
        )

    if error_type == "insufficient_cash":
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "error": "Insufficient cash",
                    "required": exc.args[1],
                    "inserted": exc.args[2],
                }
            },
        )

    if error_type == "change_not_possible":
        return JSONResponse(
            status_code=400,
            content={"detail": "Cannot return exact change"},
        )

    return JSONResponse(status_code=400, content={"detail": "Bad request"})


# -------------------------------
# Routers
# -------------------------------
app.include_router(slots.router)
app.include_router(items.router)
app.include_router(purchase.router)


@app.get("/health")
def health():
    return {"status": "ok"}
