from enum import unique

from fastapi import FastAPI, HTTPException, Depends, status, Security, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, lazyload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import hashlib
import secrets

# Konfigurace API klíče
API_KEY = "your-secret-api-key"  # V reálné aplikaci by toto bylo bezpečně uloženo, např. v proměnných prostředí
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Vytvoření SQLite databáze
SQLALCHEMY_DATABASE_URL = "sqlite:///./ecommerce.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Asociační tabulka pro vztah many-to-many mezi Order a Product
order_products = Table('order_products', Base.metadata,
                       Column('order_id', String, ForeignKey('orders.id')),
                       Column('product_id', String, ForeignKey('products.id'))
                       )


# Definice modelů SQLAlchemy
class ProductDB(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    category = Column(String)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    token = Column(String, unique=True, index=True)


class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    total_price = Column(Float)
    status = Column(String)
    created_at = Column(DateTime)

    user = relationship("UserDB")
    products = relationship("ProductDB", secondary=order_products)


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    client_ip = Column(String)
    user_agent = Column(String)
    api_key = Column(String, nullable=True)
    is_successful = Column(Boolean)


# Vytvoření tabulek
Base.metadata.create_all(bind=engine)


# Pydantic modely pro API
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    category: str

    class Config:
        orm_mode = True


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    token: Optional[str] = None

    class Config:
        orm_mode = True


class Order(BaseModel):
    id: str
    user_id: str
    products: List[str]
    total_price: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


app = FastAPI(
    title="\"Zabezpečené\" E-shop API pro kancelářské potřeby s logováním",
    description="Testovací API pro správu produktů, uživatelů a objednávek v e-shopu s kancelářskými potřebami",
    version="1.1.0",
    openapi_tags=[
    ]
)

# Metoda pro hashování API klíče pro účly logování
def hash_api_key(api_key: str) -> str:
    if api_key:
        return hashlib.sha256(api_key.encode()).hexdigest()
    return "NO_API_KEY"

# Middleware pro logování
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        method = request.method
        path = request.url.path
        client_ip = request.client.host
        user_agent = request.headers.get("User-Agent")
        api_key = request.headers.get(API_KEY_NAME)
        #print(f"Receive API key: {api_key}")

        hashed_api_key = hash_api_key(api_key) if api_key else "NO_API_KEY"
        #print(f"Hashed API key: {hashed_api_key}")

        response = await call_next(request)

        status_code = response.status_code
        is_successful = 200 <= status_code < 300

        db = SessionLocal()
        log = APILog(
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            client_ip=client_ip,
            user_agent=user_agent,
            api_key=hashed_api_key,
            is_successful=is_successful
        )
        db.add(log)
        db.commit()
        db.close()

        return response


app.add_middleware(LoggingMiddleware)


# Funkce pro ověření API klíče
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Neplatný nebo chybějící API klíč"
        )


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pomocné funkce
def get_product(product_id: str, db: SessionLocal):
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Produkt nenalezen")
    return product


def get_user(user_id: str, db: SessionLocal):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")
    return user

def generate_unique_token():
    return secrets.token_urlsafe(32)

# API endpointy

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css",
    )


@app.post("/products/", response_model=Product, tags=["Products"])
async def create_product(product: Product, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    db_product = ProductDB(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products/", response_model=List[Product], tags=["Products"])
async def list_products(skip: int = 0, limit: int = 10, category: Optional[str] = None,
                        db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    query = db.query(ProductDB)
    if category:
        query = query.filter(ProductDB.category == category)
    return query.offset(skip).limit(limit).all()


@app.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product_detail(product_id: str, db: SessionLocal = Depends(get_db),
                             api_key: APIKey = Depends(get_api_key)):
    return get_product(product_id, db)


@app.put("/products/{product_id}", response_model=Product, tags=["Products"])
async def update_product(product_id: str, product: Product, db: SessionLocal = Depends(get_db),
                         api_key: APIKey = Depends(get_api_key)):
    db_product = get_product(product_id, db)
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.post("/users/register", response_model=User, tags=["Users"])
async def create_user(user: User, db: SessionLocal = Depends(get_db)):
    token = generate_unique_token()

    user_data = user.dict()
    user_data['token'] = token  # Přidání tokenu do slovníku

    db_user = UserDB(**user_data)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Uživatel s tímto jménem nebo emailem již existuje")

    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        token=db_user.token  # Přidání tokenu do odpovědi
    )


@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user_detail(user_id: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    return get_user(user_id, db)


@app.post("/orders/", response_model=Order, tags=["Orders"])
async def create_order(order: Order, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    db_order = OrderDB(
        id=order.id,
        user_id=order.user_id,
        total_price=order.total_price,
        status=order.status,
        created_at=datetime.now()
    )
    db_products = db.query(ProductDB).filter(ProductDB.id.in_(order.products)).all()
    db_order.products = db_products
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return Order(
        id=db_order.id,
        user_id=db_order.user_id,
        products=[p.id for p in db_order.products],
        total_price=db_order.total_price,
        status=db_order.status,
        created_at=db_order.created_at
    )


@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def get_order_detail(order_id: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Objednávka nenalezena")
    return Order(
        id=order.id,
        user_id=order.user_id,
        products=[p.id for p in order.products],
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at
    )


@app.get("/users/{user_id}/orders/", response_model=List[Order], tags=["Orders"])
async def list_user_orders(user_id: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    get_user(user_id, db)  # Ověření existence uživatele
    orders = db.query(OrderDB).filter(OrderDB.user_id == user_id).all()
    return [Order(
        id=order.id,
        user_id=order.user_id,
        products=[p.id for p in order.products],
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at
    ) for order in orders]


@app.get("/search/", response_model=List[Product], tags=["Default"])
async def search_products(query: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    return db.query(ProductDB).filter(
        (ProductDB.name.ilike(f"%{query}%")) | (ProductDB.description.ilike(f"%{query}%"))
    ).all()


@app.patch("/products/{product_id}/stock", tags=["Products"])
async def update_stock(product_id: str, quantity: int, db: SessionLocal = Depends(get_db),
                       api_key: APIKey = Depends(get_api_key)):
    product = get_product(product_id, db)
    product.stock += quantity
    if product.stock < 0:
        product.stock = 0
    db.commit()
    return {"message": "Stav skladu aktualizován", "new_stock": product.stock}


@app.get("/categories/", tags=["Default"])
async def list_categories(db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    return [category[0] for category in db.query(ProductDB.category).distinct()]


@app.get("/logs", response_model=List[dict], tags=["Other"])
async def get_logs(db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key), limit: int = 100):
    logs = db.query(APILog).order_by(APILog.timestamp.desc()).limit(limit).all()
    return [
        {
            "request_id": log.request_id,
            "timestamp": log.timestamp,
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "client_ip": log.client_ip,
            "is_successful": log.is_successful
        } for log in logs
    ]


@app.get("/test-api-key-hash", tags=["Test"])
async def test_api_key_hash(request: Request, db: SessionLocal = Depends(get_db)):
    api_key = request.headers.get(API_KEY_NAME)
    hashed_key = hash_api_key(api_key)

    # Uložíme testovací záznam do logu
    log = APILog(
        request_id=str(uuid.uuid4()),
        method="GET",
        path="/test-api-key-hash",
        status_code=200,
        client_ip=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        api_key=hashed_key,
        is_successful=True
    )
    db.add(log)
    db.commit()

    # Načteme poslední záznam z logu
    last_log = db.query(APILog).order_by(APILog.id.desc()).first()

    return {
        "original_api_key": api_key,
        "hashed_api_key": hashed_key,
        "stored_in_db": last_log.api_key
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)