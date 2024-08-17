# E-commerce API for Office Supplies

This project is a secure E-commerce API for managing office supplies, built with FastAPI and SQLAlchemy. It provides endpoints for managing products, users, orders, and includes features like API key authentication and request logging.

## Features

- Product management (CRUD operations)
- User registration and management
- Order processing
- Category listing
- Product search functionality
- Stock management
- API key authentication
- Request logging
- Swagger UI documentation

## Technologies Used

- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- uvicorn

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecommerce-api.git
   cd ecommerce-api
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   The application uses SQLite by default. The database file (`ecommerce.db`) will be created automatically when you run the application for the first time.

### Running the Application

To start the server, run:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once the server is running, you can access the Swagger UI documentation at `http://localhost:8000/api/docs`.

## Authentication

The API uses API key authentication. To use the protected endpoints, you need to:

1. Register a user
2. Generate an auth token
3. Use the auth token to get an API key
4. Include the API key in the `access_token` header for subsequent requests

### Generating an API Key

1. Register a user:
   ```http
   POST /api/users/register
   ```

2. Generate an auth token:
   ```http
   POST /api/auth-token
   ```

3. Use the auth token to get an API key:
   ```http
   POST /api/renew-api-key
   ```

4. Include the API key in the `access_token` header for all protected requests.

## Main Endpoints

- Products: `/api/products/`
- Users: `/api/users/`
- Orders: `/api/orders/`
- Search: `/api/search/`
- Categories: `/api/categories/`
- Logs: `/api/logs`

For a complete list of endpoints and their usage, refer to the Swagger UI documentation.

## Error Handling

The API uses standard HTTP status codes for error responses. Detailed error messages are included in the response body.

## Logging

All API requests are logged and can be viewed using the `/api/logs` endpoint.

## Security Considerations

- API keys are hashed before being stored in the database.
- User passwords should be hashed (implementation not shown in the provided code).
- API keys expire after 72 hours and need to be renewed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under a Creative Commons license. Do Not Commercially Use 4.0 International License. This means that you are free to use and modify this software for non-commercial purposes as long as you credit the original authors. Commercial use is not permitted without the express permission of the authors.