# QuoteQuip - Quote and Invoice Management System

A Flask-based web application for managing quotes and invoices.

## Features

- Create and manage companies with their details
- Generate professional quotes and invoices
- Automatic quote and invoice numbering per company
- PDF generation with company logos
- VAT handling
- Easy conversion from quotes to invoices

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QuoteQuip.git
cd QuoteQuip
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python recreate_db.py
```

## Development Setup

1. Set environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
```

2. Run the development server:
```bash
flask run
```

## Production Deployment

### Option 1: Deploy to Heroku

1. Install the Heroku CLI and login:
```bash
heroku login
```

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
```

4. Deploy:
```bash
git push heroku main
```

### Option 2: Deploy to a Linux Server

1. Install required packages:
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv nginx
```

2. Set up Nginx:
```bash
sudo nano /etc/nginx/sites-available/quotequip
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. Create a symbolic link and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/quotequip /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

4. Set up the application:
```bash
git clone https://github.com/yourusername/QuoteQuip.git
cd QuoteQuip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. Run with Gunicorn:
```bash
gunicorn wsgi:app -b 0.0.0.0:8000
```

## Environment Variables

- `SECRET_KEY`: Secret key for session management
- `DATABASE_URL`: Database connection URL (optional, defaults to SQLite)
- `FLASK_ENV`: Application environment (development/production)

## Database Management

To reset the database:
```bash
python recreate_db.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
