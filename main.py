from fastapi import FastAPI, HTTPException, Depends, status, Security, Request, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table, DateTime, Boolean
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import secrets
import logging

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

# Enum pro stav objednávky
class OrderStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Mixin pro timestampy
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Definice modelů SQLAlchemy
class ProductDB(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    category = Column(String)
    is_available = Column(Boolean, default=True)

class UserDB(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    token = Column(String, unique=True, index=True)
    is_activated = Column(Boolean, default=True)

class OrderDB(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    total_price = Column(Float)
    status = Column(SQLAlchemyEnum(OrderStatus), default=OrderStatus.NEW)

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

class APIKeyDB(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    user = relationship("UserDB")

# Vytvoření tabulek
Base.metadata.create_all(bind=engine)


# Pydantic modely pro API
# Model pro vytvoření produktu
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    category: str
    is_available: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)

# Model pro seznam produktů
class ProductList(BaseModel):
    total: int
    products: List[Product]
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)

# Model pro uživatele
class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    token: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ActivationStatus(BaseModel):
    is_activated: bool

    model_config = ConfigDict(from_attributes=True)

# Model pro objednávku
class Order(BaseModel):
    id: str
    user_id: str
    products: List[str]
    total_price: float
    status: OrderStatus = Field(..., description="Status objednávky")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


app = FastAPI(
    title="\"Zabezpečené\" E-shop API pro kancelářské potřeby s logováním",
    description="Testovací API pro správu produktů, uživatelů a objednávek v e-shopu s kancelářskými potřebami",
    version="1.1.0",
    openapi_tags=[
    ]
)
logger = logging.getLogger(__name__)

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


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funkce pro ověření API klíče
async def get_api_key(api_key_header: str = Security(api_key_header), db: SessionLocal = Depends(get_db)):
    if not is_valid_api_key(api_key_header, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Neplatný nebo expirovaný API klíč"
        )

        # Ověření, zda je uživatelský účet aktivní
    api_key_db = db.query(APIKeyDB).filter(APIKeyDB.key == api_key_header).first()
    if not api_key_db:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API klíč nenalezen"
        )

    user = db.query(UserDB).filter(UserDB.id == api_key_db.user_id).first()
    if not user or not user.is_activated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Uživatelský účet není aktivní"
        )

    return api_key_header

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

def generate_api_key():
    return secrets.token_urlsafe(32)

def is_valid_api_key(api_key: str, db: SessionLocal) -> bool:
    logger.info(f"Validating API key: {api_key}")
    try:
        db_api_key = db.query(APIKeyDB).filter(APIKeyDB.key == api_key, APIKeyDB.is_active == True).first()
        if db_api_key and db_api_key.expires_at > datetime.utcnow():
            return True
        return False
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

# API endpointy

@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css",
    )


@app.post("/api/products/", response_model=Product, tags=["Products"])
async def create_product(product: Product, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Attempting to create product: {product.name}")
    try:
        db_product = ProductDB(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product created successfully: {db_product.id}")
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred while creating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error occurred while creating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/products/", response_model=ProductList, tags=["Products"])
async def list_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        category: Optional[str] = None,
        db: SessionLocal = Depends(get_db),
        api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Listing products with skip={skip}, limit={limit}, category={category}")
    try:
        query = db.query(ProductDB)
        if category:
            query = query.filter(ProductDB.category == category)

        total = query.count()
        products_db = query.offset(skip).limit(limit).all()

        products = [Product.from_orm(product) for product in products_db]

        logger.info(f"Found {len(products)} products")
        return ProductList(
            total=total,
            products=products,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(status_code=500, detail="Chyba při získávání produktů")



@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product_detail(product_id: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Fetching product details for product_id: {product_id}")
    try:
        product = get_product(product_id, db)
        return product
    except HTTPException as he:
        logger.warning(f"Product not found: {product_id}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching product details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/api/products/{product_id}", response_model=Product, tags=["Products"])
async def update_product(product_id: str, product: Product, db: SessionLocal = Depends(get_db),
                         api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Attempting to update product with ID: {product_id}")
    try:
        db_product = get_product(product_id, db)
        for key, value in product.dict(exclude_unset=True).items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product updated successfully: {product_id}")
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred while updating product {product_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error occurred while updating product {product_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException as he:
        logger.warning(f"Product not found: {product_id}")
        raise he


@app.post("/api/users/register", response_model=User, tags=["Users"])
async def create_user(user: User, db: SessionLocal = Depends(get_db)):
    logger.info(f"Attempting to create user: {user.username}")
    try:
        token = generate_unique_token()
        user_data = user.dict()
        user_data['token'] = token
        db_user = UserDB(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created successfully: {db_user.id}")
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            token=db_user.token
        )
    except IntegrityError:
        logger.error(f"IntegrityError: User with username {user.username} or email {user.email} already exists")
        db.rollback()
        raise HTTPException(status_code=400, detail="Uživatel s tímto jménem nebo emailem již existuje")
    except Exception as e:
        logger.error(f"Unexpected error occurred while creating user: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/users/{user_id}", response_model=User, tags=["Users"])
async def get_user_detail(user_id: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Fetching user details for user_id: {user_id}")
    try:
        user = get_user(user_id, db)
        return user
    except HTTPException as he:
        logger.warning(f"User not found: {user_id}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching user details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/api/users/{user_id}/activate", response_model=User, tags=["Users"])
async def update_user_activation_status(
        user_id: str,
        status: ActivationStatus,
        db: SessionLocal = Depends(get_db),
        api_key: APIKey = Depends(get_api_key)
):
    try:
        user = get_user(user_id, db)
        user.is_activated = status.is_activated
        db.commit()
        db.refresh(user)
        logger.info(f"User activation status updated: user_id={user_id}, is_activated={status.is_activated}")
        return user
    except HTTPException as he:
        logger.warning(f"Failed to update user activation status: {he.detail}")
        raise he
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating user activation status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Interní chyba serveru při aktualizaci stavu aktivace uživatele")
    except Exception as e:
        logger.error(f"Unexpected error while updating user activation status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Neočekávaná chyba při aktualizaci stavu aktivace uživatele")

@app.post("/api/orders/", response_model=Order, tags=["Orders"])
async def create_order(order: Order, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Received order data: {order.dict()}")
    try:
        # Vytvoříme objekt objednávky
        db_order = OrderDB(
            id=order.id,
            user_id=order.user_id,
            total_price=order.total_price,
            status=order.status,
            created_at=datetime.now()
        )

        # Načteme produkty z databáze podle ID
        db_products = db.query(ProductDB).filter(ProductDB.id.in_(order.products)).all()
        if not db_products:
            raise HTTPException(status_code=404, detail="Žádné produkty nebyly nalezeny pro daná ID")

        logger.info(f"Found {len(db_products)} products for order")

        # Přidáme produkty do objednávky pomocí extend nebo append
        db_order.products.extend(db_products)

        # Přidáme objednávku do databáze
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        logger.info(f"Order created successfully: {db_order.id}")
        return Order(
            id=db_order.id,
            user_id=db_order.user_id,
            products=[p.id for p in db_order.products],
            total_price=db_order.total_price,
            status=db_order.status,
            created_at=db_order.created_at
        )
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.rollback()  # Vrácení transakce v případě chyby
        raise HTTPException(status_code=500, detail="Chyba při vytváření objednávky")


@app.get("/api/orders/{order_id}", response_model=Order, tags=["Orders"])
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

@app.get("/api/users/{user_id}/orders/", response_model=List[Order], tags=["Orders"])
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

@app.patch("/api/orders/{order_id}/status", tags=["Orders"])
async def update_order_status(order_id: str, status: OrderStatus, db: SessionLocal = Depends(get_db),
                              api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Updating order status to: {status}")
    try:
        order = db.query(OrderDB).filter(OrderDB.id == order_id).first();
        if order is None:
            raise HTTPException(status_code=404, detail="Objednávka nenalezena")

        order.status = status
        db.commit()
        db.refresh(order)

        logger.info(f"Order status updated successfully: {order.id}")
        return Order(
            id=order.id,
            user_id=order.user_id,
            products=[p.id for p in order.products],
            total_price=order.total_price,
            status=order.status,
            created_at=order.created_at
        )
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Chyba při aktualizaci stavu objednávky")



@app.get("/api/search/", response_model=List[Product], tags=["Default"])
async def search_products(query: str, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Searching products with query: {query}")
    try:
        products = db.query(ProductDB).filter(
            (ProductDB.name.ilike(f"%{query}%")) | (ProductDB.description.ilike(f"%{query}%"))
        ).all()
        return [Product.from_orm(product) for product in products]
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Chyba při vyhledávání produktů")


@app.patch("/api/products/{product_id}/stock", tags=["Products"])
async def update_stock(product_id: str, quantity: int, db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Updating stock for product_id: {product_id}, quantity change: {quantity}")
    try:
        product = get_product(product_id, db)
        product.stock += quantity
        if product.stock < 0:
            product.stock = 0
        db.commit()
        logger.info(f"Stock updated successfully for product_id: {product_id}, new stock: {product.stock}")
        return {"message": "Stav skladu aktualizován", "new_stock": product.stock}
    except HTTPException as he:
        logger.warning(f"Product not found: {product_id}")
        raise he
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Chyba při aktualizaci stavu skladu")


@app.get("/api/categories/", tags=["Default"])
async def list_categories(db: SessionLocal = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    logger.info("Fetching categories")
    try:
        categories = [category[0] for category in db.query(ProductDB.category).distinct()]
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Chyba při získávání kategorií")


@app.get("/api/logs", response_model=List[dict], tags=["Other"])
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


@app.get("/api/test-api/test-api-key-hash", tags=["Test"])
async def test_api_key_hash(request: Request, db: SessionLocal = Depends(get_db),  api_key: APIKey = Depends(get_api_key)):
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


@app.post("/api/auth-token", tags=["Auth"])
async def generate_auth_token(email: str, token: str, db: SessionLocal = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == email, UserDB.token == token, UserDB.is_activated == True).first()
    if not user:
        raise HTTPException(status_code=400, detail="Neplatný email, token nebo uživatel není aktivován")

    # Deaktivujte všechny staré API klíče uživatele
    db.query(APIKeyDB).filter(APIKeyDB.user_id == user.id).update({"is_active": False})

    # Vytvořte nový API klíč
    new_api_key = generate_api_key()
    expires_at = datetime.utcnow() + timedelta(hours=72)
    db_api_key = APIKeyDB(
        id=str(uuid.uuid4()),
        user_id=user.id,
        key=new_api_key,
        expires_at=expires_at
    )
    db.add(db_api_key)
    db.commit()

    return {"api_key": new_api_key, "expires_at": expires_at}

@app.post("/api/renew-api-key", tags=["Auth"])
async def renew_api_key(current_api_key: str, db: SessionLocal = Depends(get_db)):
    db_api_key = db.query(APIKeyDB).filter(APIKeyDB.key == current_api_key, APIKeyDB.is_active == True).first()
    if not db_api_key:
        raise HTTPException(status_code=400, detail="Neplatný API klíč")

    # Deaktivujte současný API klíč
    db_api_key.is_active = False

    # Vytvořte nový API klíč
    new_api_key = generate_api_key()
    expires_at = datetime.utcnow() + timedelta(hours=72)
    new_db_api_key = APIKeyDB(
        id=str(uuid.uuid4()),
        user_id=db_api_key.user_id,
        key=new_api_key,
        expires_at=expires_at
    )
    db.add(new_db_api_key)
    db.commit()

    return {"api_key": new_api_key, "expires_at": expires_at}
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)