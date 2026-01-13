from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.booking import router as bookingRouter
from app.routes.group import router as groupRouter
from app.routes.groupBooking import router as groupBookingRouter
from app.routes.user import router as userRouter
from app.routes.allocation import router as allocationRouter

app = FastAPI(title="Shuttle Bus Planning System")

# Enable CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(userRouter)
app.include_router(bookingRouter)
app.include_router(groupRouter)
app.include_router(groupBookingRouter)
app.include_router(allocationRouter)

@app.get("/health")
def healthCheck():
    return {
        "status": "OK",
        "service": "shuttle-backend"
    }
