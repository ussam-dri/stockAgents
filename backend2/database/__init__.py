from .oracle_connection import OracleConnection
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
oracle_db = None

def init_db(app):
    # Get Oracle configuration from Config
    from config.config import Config
    config = Config()
    oracle_config = {
        'username': config.oracle.username,
        'password': config.oracle.password,
        'host': config.oracle.host,
        'port': config.oracle.port,
        'service_name': config.oracle.service_name,
        'min_connections': config.oracle.min_connections,
        'max_connections': config.oracle.max_connections
    }
    
    # Initialize Oracle connection
    global oracle_db
    oracle_db = OracleConnection(oracle_config)
    
    # Configure SQLAlchemy to use Oracle
    app.config['SQLALCHEMY_DATABASE_URI'] = f"oracle://{oracle_config['username']}:{oracle_config['password']}@{oracle_config['host']}:{oracle_config['port']}/{oracle_config['service_name']}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        
def get_db_session():
    return db.session

def get_oracle_db():
    return oracle_db

def close_db_session():
    db.session.close()
    if oracle_db:
        oracle_db.close()
