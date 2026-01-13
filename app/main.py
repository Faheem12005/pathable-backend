from fastapi import FastAPI
from app.routes.booking import router as bookingRouter
from app.routes.group import router as groupRouter
from app.routes.groupBooking import router as groupBookingRouter

app = FastAPI(title="Shuttle Bus Planning System")

app.include_router(bookingRouter)
app.include_router(groupRouter)
app.include_router(groupBookingRouter)

@app.get("/health")
def healthCheck():
    return {
        "status": "OK",
        "service": "shuttle-backend"
    }
