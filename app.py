from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from models import db, Company, Quote, QuoteItem, Invoice, InvoiceItem
from pdf_generator import generate_quote_pdf, generate_invoice_pdf
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotequip.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

# Create required directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'temp'), exist_ok=True)

# Initialize database tables
def init_db():
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Create all tables fresh

init_db()

def generate_quote_number(company_id):
    # Get the latest quote number for this company
    latest_quote = Quote.query.filter_by(company_id=company_id).order_by(Quote.id.desc()).first()
    
    if latest_quote:
        # Extract the number from the latest quote number
        latest_num = int(latest_quote.quote_number.split('-')[1])
        new_num = latest_num + 1
    else:
        new_num = 1
    
    return f"QTE-{new_num:04d}"

def generate_invoice_number(company_id):
    # Get the latest invoice number for this company
    latest_invoice = Invoice.query.filter_by(company_id=company_id).order_by(Invoice.id.desc()).first()
    
    if latest_invoice:
        # Extract the number from the latest invoice number
        latest_num = int(latest_invoice.invoice_number.split('-')[1])
        new_num = latest_num + 1
    else:
        new_num = 1
    
    return f"INV-{new_num:04d}"

@app.route('/')
def index():
    companies = Company.query.all()
    return render_template('index.html', companies=companies)

@app.route('/create_quote', methods=['GET', 'POST'])
def create_quote_view():
    if request.method == 'POST':
        try:
            company_id = int(request.form['company_id'])
            quote_number = generate_quote_number(company_id)
            
            # Create new quote
            new_quote = Quote(
                quote_number=quote_number,
                date=datetime.now(),
                valid_until=datetime.now() + timedelta(days=7),
                company_id=company_id,
                to_name=request.form['to_name'],
                to_registration_number=request.form['to_registration_number'],
                to_vat_number=request.form['to_vat_number'],
                to_email=request.form['to_email'],
                to_address=request.form['to_address']
            )
            
            # Process quote items
            items_data = zip(
                request.form.getlist('item_description[]'),
                request.form.getlist('item_quantity[]'),
                request.form.getlist('item_unit_price[]'),
                request.form.getlist('item_discount[]')
            )
            
            subtotal = 0
            for desc, qty, price, disc in items_data:
                quantity = int(qty)
                unit_price = float(price)
                discount = float(disc) if disc else 0
                
                # Calculate item total with discount
                item_total = quantity * unit_price * (1 - discount/100)
                subtotal += item_total
                
                # Create quote item
                quote_item = QuoteItem(
                    quote=new_quote,
                    description=desc,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount,
                    total=item_total
                )
                new_quote.items.append(quote_item)
            
            # Calculate quote totals
            new_quote.subtotal = subtotal
            new_quote.vat_amount = subtotal * 0.15  # 15% VAT
            new_quote.total = subtotal + new_quote.vat_amount
            
            # Save to database
            db.session.add(new_quote)
            db.session.commit()
            
            flash('Quote created successfully!', 'success')
            return redirect(url_for('view_quote', quote_id=new_quote.id))
            
        except Exception as e:
            flash(f'Error creating quote: {str(e)}', 'error')
            return redirect(url_for('create_quote_view'))

    companies = Company.query.all()
    return render_template('create_quote.html', companies=companies)

@app.route('/quote/<int:quote_id>')
def view_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    return render_template('view_quote.html', quote=quote)

@app.route('/quotes')
def list_quotes():
    companies = Company.query.all()
    quotes = Quote.query.order_by(Quote.date.desc()).all()
    return render_template('list_quotes.html', quotes=quotes, companies=companies)

@app.route('/invoices')
def list_invoices():
    companies = Company.query.all()
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('list_invoices.html', invoices=invoices, companies=companies)

@app.route('/create_invoice/<int:quote_id>', methods=['GET', 'POST'])
def create_invoice(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    if request.method == 'POST':
        invoice_date = datetime.strptime(request.form['invoice_date'], '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        apply_vat = 'is_vat_registered' in request.form
        
        # Calculate totals based on VAT status
        subtotal = quote.subtotal
        vat_amount = quote.vat_amount if apply_vat else 0
        total = quote.total if apply_vat else subtotal
        
        invoice = Invoice(
            quote=quote,
            company_id=quote.company_id,
            invoice_number=generate_invoice_number(quote.company_id),
            date=invoice_date,
            due_date=due_date,
            to_name=quote.to_name,
            to_registration_number=quote.to_registration_number,
            to_vat_number=quote.to_vat_number,
            to_address=quote.to_address,
            to_email=quote.to_email,
            subtotal=subtotal,
            vat_amount=vat_amount,
            total=total
        )
        
        # Copy quote items to invoice items
        for quote_item in quote.items:
            invoice_item = InvoiceItem(
                invoice=invoice,
                description=quote_item.description,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount=quote_item.discount,
                total=quote_item.total
            )
            db.session.add(invoice_item)
        
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice.id))
        
    return render_template('create_invoice.html', quote=quote)

@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('view_invoice.html', invoice=invoice)

@app.route('/mark_invoice_paid/<int:invoice_id>', methods=['POST'])
def mark_invoice_paid(invoice_id):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice.paid = True
        db.session.commit()
        flash('Invoice marked as paid!', 'success')
    except Exception as e:
        flash(f'Error marking invoice as paid: {str(e)}', 'error')
    return redirect(url_for('view_invoice', invoice_id=invoice_id))

@app.route('/create_company', methods=['GET', 'POST'])
def create_company_view():
    if request.method == 'POST':
        # Handle logo upload
        logo_filename = None
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                logo_filename = secure_filename(logo.filename)
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

        # Format bank details
        bank_details = f"""Bank: {request.form['bank_name']}
Account Number: {request.form['bank_account_number']}
Branch Code: {request.form['bank_branch_code']}
Account Type: {request.form['bank_account_type']}"""

        # Create new company
        new_company = Company(
            company_name=request.form['company_name'],
            registration_number=request.form['registration_number'],
            vat_number=request.form['vat_number'],
            telephone=request.form['telephone'],
            email=request.form['email'],
            address=request.form['address'],
            logo=logo_filename,
            bank_details=bank_details
        )
        
        db.session.add(new_company)
        db.session.commit()
        flash('Company added successfully!', 'success')
        return redirect(url_for('index'))
            
    return render_template('create_company.html')

@app.route('/edit_company/<int:company_id>', methods=['GET', 'POST'])
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    if request.method == 'POST':
        try:
            # Update company details
            company.company_name = request.form['company_name']
            company.registration_number = request.form['registration_number']
            company.vat_number = request.form['vat_number']
            company.telephone = request.form['telephone']
            company.email = request.form['email']
            company.address = request.form['address']
            
            # Handle logo upload
            if 'logo' in request.files:
                logo = request.files['logo']
                if logo.filename != '':
                    # Delete old logo if it exists
                    if company.logo:
                        old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)
                    
                    # Save new logo
                    logo_filename = secure_filename(logo.filename)
                    logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
                    company.logo = logo_filename

            # Update bank details
            bank_details = f"""Bank: {request.form['bank_name']}
Account Number: {request.form['bank_account_number']}
Branch Code: {request.form['bank_branch_code']}
Account Type: {request.form['bank_account_type']}"""
            company.bank_details = bank_details

            db.session.commit()
            flash('Company updated successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error updating company: {str(e)}', 'error')
            return redirect(url_for('edit_company', company_id=company_id))
    
    # Parse bank details for form
    bank_details = {}
    if company.bank_details:
        for line in company.bank_details.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                bank_details[key] = value.strip()
    
    return render_template('edit_company.html', company=company, bank_details=bank_details)

@app.route('/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    try:
        # Delete company logo if it exists
        if company.logo:
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo)
            if os.path.exists(logo_path):
                os.remove(logo_path)
        
        # Delete the company
        db.session.delete(company)
        db.session.commit()
        flash('Company deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting company: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/download_quote_pdf/<int:quote_id>')
def download_quote_pdf(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    
    # Ensure temp directory exists
    if not os.path.exists('temp'):
        os.makedirs('temp')
    
    # Generate PDF
    pdf_path = f"temp/quote_{quote.quote_number}.pdf"
    generate_quote_pdf(quote)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"quote_{quote.quote_number}.pdf"
    )

@app.route('/download_invoice_pdf/<int:invoice_id>')
def download_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Ensure temp directory exists
    if not os.path.exists('temp'):
        os.makedirs('temp')
    
    # Generate PDF
    pdf_path = f"temp/invoice_{invoice.invoice_number}.pdf"
    generate_invoice_pdf(invoice)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"invoice_{invoice.invoice_number}.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
