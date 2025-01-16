from datetime import datetime
from models import Company, Quote, Invoice
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

engine = create_engine('sqlite:///quotequip.db')

def create_quote(company_id, quote_data):
    with Session(engine) as session:
        company = session.query(Company).get(company_id)
        if not company:
            raise ValueError("Company not found")
            
        quote_number = f'Q{company.last_quote_number:04d}'
        new_quote = Quote(
            quote_number=quote_number,
            company_id=company.id,
            **quote_data
        )
        
        session.add(new_quote)
        company.last_quote_number += 1
        session.commit()
        
        # Refresh the quote object to ensure all relationships are loaded
        session.refresh(new_quote)
        return new_quote.id  # Return only the ID

def quote_to_invoice(quote_id, due_date):
    with Session(engine) as session:
        quote = session.query(Quote).get(quote_id)
        if not quote:
            raise ValueError("Quote not found")
            
        if quote.invoice:
            raise ValueError("This quote has already been converted to an invoice")
            
        try:
            # Convert string date to datetime object
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid due date format. Please use YYYY-MM-DD format.")
            
        company = quote.company
        invoice_number = f'INV{company.last_invoice_number + 1:04d}'
        
        new_invoice = Invoice(
            invoice_number=invoice_number,
            quote_id=quote.id,
            issue_date=datetime.now(),
            due_date=due_date_obj,
            status='Unpaid'
        )
        
        session.add(new_invoice)
        company.last_invoice_number += 1
        session.commit()
        
        # Refresh to load relationships
        session.refresh(new_invoice)
        return new_invoice

def mark_invoice_paid(invoice_id):
    with Session(engine) as session:
        invoice = session.query(Invoice).get(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
            
        invoice.status = 'Paid'
        session.commit()
        return invoice
