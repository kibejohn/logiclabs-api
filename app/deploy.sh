#!/bin/bash

# Exit on error
set -e

echo "====== Deploying Scorecards Application ======"

# Create virtual environment
echo "Creating virtual environment..."
python -m virtualenv env

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "DATABASE_URL=postgresql://scorecard_user:your_password@localhost/scorecard_db" > .env
    echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
    echo "Please update the .env file with your PostgreSQL credentials."
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Please install it manually."
    exit 1
fi

# Create database if it doesn't exist
echo "Setting up PostgreSQL database..."
PGPASSWORD=postgres psql -U postgres -h localhost -tc "SELECT 1 FROM pg_database WHERE datname = 'scorecard_db'" | grep -q 1 || PGPASSWORD=postgres psql -U postgres -h localhost -c "CREATE DATABASE scorecard_db"

# Create user if it doesn't exist
PGPASSWORD=postgres psql -U postgres -h localhost -tc "SELECT 1 FROM pg_roles WHERE rolname = 'scorecard_user'" | grep -q 1 || PGPASSWORD=postgres psql -U postgres -h localhost -c "CREATE USER scorecard_user WITH ENCRYPTED PASSWORD 'your_password'"

# Grant privileges
PGPASSWORD=postgres psql -U postgres -h localhost -c "GRANT ALL PRIVILEGES ON DATABASE scorecard_db TO scorecard_user"

# Create database tables
echo "Creating database tables..."
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

# Create Gunicorn config
echo "Creating Gunicorn configuration..."
cat > gunicorn_config.py << EOF
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
EOF

# Create startup script
echo "Creating startup script..."
cat > start.sh << EOF
#!/bin/bash
source env/bin/activate
gunicorn app.main:app -c gunicorn_config.py
EOF
chmod +x start.sh

echo "====== Deployment Setup Complete ======"
echo "To run the application:"
echo "1. Update the .env file with your PostgreSQL credentials if necessary"
echo "2. Run ./start.sh"
echo "3. Create an initial admin user by visiting: http://localhost:8000/setup/init?business_name=YourCompany&admin_username=admin&admin_email=admin@example.com&admin_password=securepassword"