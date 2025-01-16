from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(100))
    vat_number = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    logo = db.Column(db.String(255))
    bank_details = db.Column(db.Text)
    is_vat_registered = db.Column(db.Boolean, default=False)
    quotes = db.relationship('Quote', backref='company', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='company', lazy=True, cascade='all, delete-orphan')

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=False)  
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    to_name = db.Column(db.String(100), nullable=False)
    to_registration_number = db.Column(db.String(50))
    to_vat_number = db.Column(db.String(50))
    to_email = db.Column(db.String(120))
    to_address = db.Column(db.Text)
    items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade='all, delete-orphan')
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    vat_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    
    __table_args__ = (db.UniqueConstraint('company_id', 'quote_number', name='unique_quote_number_per_company'),)

class QuoteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=False)  
    date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    to_name = db.Column(db.String(100), nullable=False)
    to_registration_number = db.Column(db.String(50))
    to_vat_number = db.Column(db.String(50))
    to_email = db.Column(db.String(120))
    to_address = db.Column(db.Text)
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    vat_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    paid = db.Column(db.Boolean, default=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id', ondelete='SET NULL'), unique=True)
    quote = db.relationship('Quote', backref=db.backref('invoice', uselist=False))
    
    __table_args__ = (db.UniqueConstraint('company_id', 'invoice_number', name='unique_invoice_number_per_company'),)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
