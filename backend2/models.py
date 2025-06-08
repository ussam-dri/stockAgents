from datetime import datetime
from database import db

class StockItem(db.Model):
    __tablename__ = 'stock_items'
    
    product_id = db.Column(db.String(50), primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    available_stock = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, product_name, category, current_stock, unit, available_stock=None):
        self.product_id = f"PROD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.product_name = product_name
        self.category = category
        self.current_stock = current_stock
        self.available_stock = available_stock if available_stock is not None else current_stock
        self.unit = unit
        self.last_updated = datetime.utcnow()
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'category': self.category,
            'current_stock': self.current_stock,
            'available_stock': self.available_stock,
            'unit': self.unit,
            'last_updated': self.last_updated.isoformat()
        }
    
    def __repr__(self):
        return f"<StockItem {self.product_name} ({self.product_id})>" 