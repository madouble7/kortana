# Getting Started with Kortana

## 🚀 Quick Setup Guide

Welcome to Kortana - a context-aware ethical AI system. This guide will help you set up your development environment and get started with the project.

## 📋 Prerequisites

- Python 3.11+
- Git
- Virtual environment (venv311 recommended)
- VS Code (recommended IDE)

## ⚡ Environment Setup

### 1. Clone and Setup
```cmd
git clone <repository-url>
cd project-kortana
```

### 2. Create Virtual Environment
```cmd
python -m venv venv311
venv311\Scripts\activate.bat
```

### 3. Install Dependencies
```cmd
# Install all required packages
pip install -e .

# Verify key dependencies
python -c "import sqlalchemy, alembic, fastapi; print('Dependencies OK')"
```

## 🗄️ Database Migrations

### Initial Database Setup
```cmd
# Navigate to project root
cd c:\project-kortana

# Upgrade database to latest schema
C:\project-kortana\venv311\Scripts\alembic.exe upgrade head
```

### Verify Database Status
```cmd
# Check current migration
C:\project-kortana\venv311\Scripts\alembic.exe current
# Expected output: df8dc2b048ef (head)

# View migration history
C:\project-kortana\venv311\Scripts\alembic.exe history
```

### 🔧 Database Development Workflow

#### Making Schema Changes
1. **Edit ORM Models**: Make changes in `src/kortana/modules/memory_core/models.py` or relevant module
2. **Generate Migration**:
   ```cmd
   C:\project-kortana\venv311\Scripts\alembic.exe revision --autogenerate -m "describe your change"
   ```
3. **Review Generated Migration**: Always check the auto-generated file in `src/kortana/migrations/versions/`
4. **Apply Migration**:
   ```cmd
   C:\project-kortana\venv311\Scripts\alembic.exe upgrade head
   ```

#### ⚠️ Protected Files - Do Not Modify
- `alembic.ini` - Core Alembic configuration
- `src/kortana/migrations/env.py` - Migration environment setup
- Existing migration files (unless fixing critical issues)

## 🚀 Running the Application

### Start FastAPI Server
```cmd
# Using uvicorn directly
C:\project-kortana\venv311\Scripts\python.exe -m uvicorn src.kortana.main:app --reload --host 127.0.0.1 --port 8000

# Using VS Code task (recommended)
# Use Ctrl+Shift+P -> "Tasks: Run Task" -> "Run Current File with venv311"
```

### Verify Installation
```cmd
# Test API endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/test-db

# Or visit in browser:
# http://127.0.0.1:8000/docs (Interactive API documentation)
```

## 🧪 Testing

### Run Memory Service Tests
```cmd
C:\project-kortana\venv311\Scripts\python.exe test_memory_service.py
```

### Run FastAPI Tests
```cmd
C:\project-kortana\venv311\Scripts\python.exe test_app_import.py
```

## 📁 Project Structure

```
src/kortana/
├── config/
│   └── settings.py          # Configuration management
├── services/
│   └── database.py          # Database services
├── modules/
│   ├── memory_core/
│   │   ├── models.py        # CoreMemory ORM model
│   │   └── services.py      # Memory operations
│   └── ethical_discernment_module/
│       └── evaluators.py    # Ethical assessment stubs
├── migrations/              # Alembic database migrations
└── main.py                  # FastAPI application
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
APP_NAME=kortana
LOG_LEVEL=INFO
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### VS Code Setup
The project includes optimized VS Code settings in `.vscode/settings.json` for:
- Python path configuration
- Linting with Ruff
- Auto-formatting on save
- Integrated terminal setup

## 🆘 Troubleshooting

### Database Issues
```cmd
# Reset database (caution: destroys data)
del kortana_memory_dev.db
C:\project-kortana\venv311\Scripts\alembic.exe upgrade head

# Check migration status
C:\project-kortana\venv311\Scripts\alembic.exe current
```

### Import Errors
```cmd
# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check package installation
pip list | findstr -i "sqlalchemy alembic fastapi"
```

### Server Won't Start
```cmd
# Check port availability
netstat -an | findstr :8000

# Use different port
python -m uvicorn src.kortana.main:app --port 8001
```

## 📚 Next Steps

1. **Explore the API**: Visit `http://127.0.0.1:8000/docs` for interactive documentation
2. **Review Architecture**: Check `docs/project_structure.md` for detailed architecture
3. **Development Workflow**: See `docs/KORTANA_PROJECT_MAP.md` for development guidelines
4. **Testing**: Run the test suite to ensure everything works correctly

## 🎯 Development Priorities

1. Memory core expansion
2. Ethical discernment implementation
3. API endpoint development
4. Authentication layer
5. Comprehensive testing suite

---

**💡 Tip**: Always activate your virtual environment (`venv311\Scripts\activate.bat`) before running any commands!
