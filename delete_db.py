import os

if os.path.exists('quotequip.db'):
    os.remove('quotequip.db')
    print("Database deleted successfully")
