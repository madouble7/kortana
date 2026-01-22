# E-Commerce AI Features API Documentation

This document describes the new e-commerce-oriented AI features integrated into Kor'tana from the `tanishq-jarsodiwala/stock` repository. These features provide intelligent categorization, inventory analysis, and product recommendations using machine learning.

## Table of Contents

1. [Product Categorization API](#product-categorization-api)
2. [Inventory Analysis API](#inventory-analysis-api)
3. [Recommendation Engine API](#recommendation-engine-api)
4. [Architecture Overview](#architecture-overview)
5. [ML Models](#ml-models)

## Product Categorization API

### Base URL
`/categories`

### Endpoints

#### 1. Classify Product
**POST** `/categories/classify`

Classifies a product into a category using AI.

**Request Body:**
```json
{
  "name": "Wireless Headphones",
  "description": "Bluetooth noise-cancelling over-ear headphones"
}
```

**Response:**
```json
{
  "category": "ELECTRONICS",
  "confidence_score": 0.95,
  "reasoning": "This is clearly an electronic device based on the description"
}
```

**Category Types:**
- `ELECTRONICS`
- `FASHION`
- `HOME`
- `FOOD`
- `BOOKS`
- `SPORTS`
- `HEALTH`
- `AUTOMOTIVE`
- `OTHER`

#### 2. Create Product
**POST** `/categories/products`

Creates a new product with automatic categorization if category is not provided.

**Request Body:**
```json
{
  "name": "Running Shoes",
  "description": "Lightweight athletic footwear for running",
  "category": "SPORTS"  // Optional - will be auto-determined if not provided
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Running Shoes",
  "description": "Lightweight athletic footwear for running",
  "category": "SPORTS",
  "confidence_score": 1.0,
  "created_at": "2026-01-22T06:30:00Z",
  "updated_at": "2026-01-22T06:30:00Z"
}
```

#### 3. List Products
**GET** `/categories/products?skip=0&limit=100`

Retrieves all products with pagination.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 100)

#### 4. Get Product
**GET** `/categories/products/{product_id}`

Retrieves a specific product by ID.

#### 5. Get Products by Category
**GET** `/categories/products/category/{category}?skip=0&limit=100`

Retrieves products filtered by category.

#### 6. Update Product
**PUT** `/categories/products/{product_id}`

Updates a product.

#### 7. Delete Product
**DELETE** `/categories/products/{product_id}`

Deletes a product.

---

## Inventory Analysis API

### Base URL
`/inventory`

### Endpoints

#### 1. Analyze Inventory
**POST** `/inventory/analyze`

Analyzes inventory using financial metrics and provides buy/don't buy recommendation.

**Request Body:**
```json
{
  "product_name": "Tech Stock A",
  "pe_ratio": 15.0,
  "pb_ratio": 2.0,
  "de_ratio": 0.5,
  "roe": 15.0,
  "roa": 8.0
}
```

**Response:**
```json
{
  "recommendation": "Buy",
  "confidence_score": 0.85,
  "analysis": "Based on financial metrics analysis:\n- P/E Ratio: 15.00\n- P/B Ratio: 2.00\n- D/E Ratio: 0.50\n- ROE: 15.00%\n- ROA: 8.00%\n\nRecommendation: Buy with 85.00% confidence"
}
```

**Financial Metrics:**
- **P/E Ratio**: Price to Earnings ratio (indicates stock valuation)
- **P/B Ratio**: Price to Book ratio (valuation based on book value)
- **D/E Ratio**: Debt to Equity ratio (company's debt vs equity)
- **ROE**: Return on Equity (profitability measure)
- **ROA**: Return on Assets (asset utilization efficiency)

#### 2. Create Inventory
**POST** `/inventory/`

Creates a new inventory entry.

**Request Body:**
```json
{
  "product_name": "Widget A",
  "sku": "WGT-001",
  "quantity": 100,
  "status": "IN_STOCK"
}
```

**Stock Status Types:**
- `IN_STOCK`
- `LOW_STOCK`
- `OUT_OF_STOCK`
- `OVERSTOCKED`

#### 3. Create Inventory with Analysis
**POST** `/inventory/with-analysis`

Creates inventory entry with automatic financial analysis.

**Request Body:**
```json
{
  "product_name": "Widget B",
  "pe_ratio": 20.0,
  "pb_ratio": 3.0,
  "de_ratio": 1.0,
  "roe": 12.0,
  "roa": 6.0
}
```

#### 4. List Inventory
**GET** `/inventory/?skip=0&limit=100`

Retrieves all inventory entries with pagination.

#### 5. Get Inventory
**GET** `/inventory/{inventory_id}`

Retrieves a specific inventory entry by ID.

#### 6. Get Inventory by Status
**GET** `/inventory/status/{status}?skip=0&limit=100`

Retrieves inventory filtered by status.

#### 7. Update Inventory
**PUT** `/inventory/{inventory_id}`

Updates an inventory entry.

#### 8. Delete Inventory
**DELETE** `/inventory/{inventory_id}`

Deletes an inventory entry.

---

## Recommendation Engine API

### Base URL
`/recommendations`

### Endpoints

#### 1. Get Recommendations
**POST** `/recommendations/`

Gets personalized product recommendations for a user using embedding-based similarity search.

**Request Body:**
```json
{
  "user_id": "user123",
  "query": "technology products for work",
  "limit": 5
}
```

**Response:**
```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "product_id": 1,
      "product_name": "Laptop",
      "recommendation_score": 0.92,
      "reasoning": "Similarity score: 0.920. Category: electronics."
    },
    {
      "product_id": 3,
      "product_name": "Mouse",
      "recommendation_score": 0.85,
      "reasoning": "Similarity score: 0.850. Category: electronics."
    }
  ],
  "query": "technology products for work"
}
```

#### 2. Create User Preferences
**POST** `/recommendations/preferences`

Creates or updates user preferences for personalized recommendations.

**Request Body:**
```json
{
  "user_id": "user123",
  "preferences": {
    "favorite_categories": ["ELECTRONICS", "BOOKS"],
    "price_range": "medium",
    "interests": "technology, reading"
  }
}
```

#### 3. Get User Preferences
**GET** `/recommendations/preferences/{user_id}`

Retrieves user preferences by user ID.

#### 4. Get Recommendation History
**GET** `/recommendations/history/{user_id}?skip=0&limit=50`

Retrieves past recommendations made for a specific user.

#### 5. Get All Recommendations
**GET** `/recommendations/all?skip=0&limit=100`

Retrieves all recommendations (useful for analytics).

---

## Architecture Overview

### Module Structure

The e-commerce AI features are organized into three modular packages:

```
src/kortana/modules/
├── product_categorization/
│   ├── models.py          # Product database model
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── services.py        # CategorizationService with AI logic
│   └── routers/
│       └── category_router.py  # FastAPI endpoints
├── inventory_analysis/
│   ├── models.py          # Inventory database model
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── services.py        # InventoryAnalysisService with ML model
│   └── routers/
│       └── inventory_router.py  # FastAPI endpoints
└── recommendation_engine/
    ├── models.py          # UserPreference & Recommendation models
    ├── schemas.py         # Pydantic request/response schemas
    ├── services.py        # RecommendationService with embeddings
    └── routers/
        └── recommendation_router.py  # FastAPI endpoints
```

### Database Schema

#### Products Table
- `id`: Integer (Primary Key)
- `name`: String(255)
- `description`: Text
- `category`: Enum (CategoryType)
- `confidence_score`: Float
- `embedding`: JSON (Vector embedding for similarity search)
- `product_metadata`: JSON
- `created_at`: DateTime
- `updated_at`: DateTime

#### Inventory Table
- `id`: Integer (Primary Key)
- `product_name`: String(255)
- `sku`: String(100) (Unique)
- `quantity`: Integer
- `status`: Enum (StockStatus)
- `pe_ratio`: Float
- `pb_ratio`: Float
- `de_ratio`: Float
- `roe`: Float
- `roa`: Float
- `recommendation`: String(50)
- `confidence_score`: Float
- `inventory_metadata`: JSON
- `created_at`: DateTime
- `updated_at`: DateTime

#### User Preferences Table
- `id`: Integer (Primary Key)
- `user_id`: String(255)
- `preferences`: JSON
- `embedding`: JSON (Vector embedding of preferences)
- `created_at`: DateTime
- `updated_at`: DateTime

#### Recommendations Table
- `id`: Integer (Primary Key)
- `user_id`: String(255)
- `product_id`: Integer
- `product_name`: String(255)
- `recommendation_score`: Float
- `reasoning`: Text
- `recommendation_metadata`: JSON
- `created_at`: DateTime

---

## ML Models

### Inventory Analysis Model

**Type:** XGBoost Classifier

**Features:**
- P/E Ratio (Price to Earnings)
- P/B Ratio (Price to Book)
- D/E Ratio (Debt to Equity)
- ROE (Return on Equity)
- ROA (Return on Assets)

**Output:** Binary classification (Buy / Do not buy)

**Model Location:** `data/ml_models/model.pkl`

**Scaler:** StandardScaler (`data/ml_models/scaler.pkl`)

**Feature Adjustment:**
The model applies correlation-based feature adjustment before prediction using the correlation matrix from the original stock repository.

### Product Categorization

**Type:** LLM-based classification

**Provider:** OpenAI (configurable via LLMClientFactory)

**Categories:** 9 predefined categories (ELECTRONICS, FASHION, HOME, FOOD, BOOKS, SPORTS, HEALTH, AUTOMOTIVE, OTHER)

**Process:**
1. Constructs prompt with product name and description
2. Uses LLM to classify into one of 9 categories
3. Extracts confidence score and reasoning from response
4. Falls back to "OTHER" if classification fails

### Recommendation Engine

**Type:** Embedding-based similarity search

**Embeddings:** OpenAI text-embedding-3-small (via existing Kor'tana EmbeddingService)

**Process:**
1. Generates embeddings for product descriptions
2. Generates embeddings for user query and preferences
3. Calculates cosine similarity between query and products
4. Returns top-N most similar products

**Integration:** Seamlessly integrates with existing Kor'tana embedding service and memory system

---

## Usage Examples

### Example 1: Complete Product Workflow

```python
import requests

base_url = "http://localhost:8000"

# 1. Create a product with auto-categorization
response = requests.post(
    f"{base_url}/categories/products",
    json={
        "name": "Smart Watch",
        "description": "Fitness tracking smartwatch with heart rate monitor"
    }
)
product = response.json()
print(f"Product created: {product['name']} - Category: {product['category']}")

# 2. Analyze inventory for similar product
response = requests.post(
    f"{base_url}/inventory/analyze",
    json={
        "product_name": "Smart Watch Stock",
        "pe_ratio": 18.0,
        "pb_ratio": 2.5,
        "de_ratio": 0.8,
        "roe": 14.0,
        "roa": 7.5
    }
)
analysis = response.json()
print(f"Recommendation: {analysis['recommendation']} ({analysis['confidence_score']:.2%} confidence)")

# 3. Get recommendations for a user
response = requests.post(
    f"{base_url}/recommendations/",
    json={
        "user_id": "user001",
        "query": "fitness and health products",
        "limit": 3
    }
)
recommendations = response.json()
print(f"Top recommendations for {recommendations['user_id']}:")
for rec in recommendations['recommendations']:
    print(f"  - {rec['product_name']} (score: {rec['recommendation_score']:.2f})")
```

### Example 2: Set User Preferences

```python
import requests

base_url = "http://localhost:8000"

# Set user preferences
response = requests.post(
    f"{base_url}/recommendations/preferences",
    json={
        "user_id": "user001",
        "preferences": {
            "favorite_categories": ["ELECTRONICS", "SPORTS"],
            "price_range": "medium",
            "brand_preferences": ["Sony", "Nike"]
        }
    }
)
prefs = response.json()
print(f"Preferences set for {prefs['user_id']}")
```

---

## Testing

Integration tests are available in `/tests/test_ecommerce_integration.py`

Run tests with:
```bash
pytest tests/test_ecommerce_integration.py -v
```

---

## Performance Considerations

1. **Embeddings**: Generated lazily and cached in database
2. **ML Model**: Loaded once at service initialization
3. **Similarity Search**: In-memory cosine similarity (consider vector database for large scale)
4. **LLM Calls**: Categorization uses LLM, consider caching results

---

## Future Enhancements

1. **Vector Database**: Integrate Pinecone or similar for scalable similarity search
2. **Collaborative Filtering**: Add user-item interaction tracking for improved recommendations
3. **A/B Testing**: Framework for testing different recommendation strategies
4. **Real-time Inventory**: WebSocket updates for stock status changes
5. **Batch Processing**: Bulk categorization and analysis endpoints
6. **Advanced Analytics**: Dashboard for recommendation metrics and performance

---

## Security

- CodeQL security scans completed: **0 vulnerabilities**
- All user inputs validated via Pydantic schemas
- SQL injection protected by SQLAlchemy ORM
- API key management via environment variables

---

## License

Same as Kor'tana project (MIT License)
