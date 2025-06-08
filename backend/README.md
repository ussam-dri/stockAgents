# A2A Stock Management System

A multi-agent system built with Google's A2A (Agent-to-Agent) framework for automated inventory management and supplier coordination.

## Overview

This system manages stock levels between a company's inventory (stored in Oracle database) and multiple suppliers using intelligent agents that communicate and coordinate to ensure optimal stock replenishment.

## Architecture

### Agents

1. **Inventory Agent** (`inventory_agent.py`)
   - Monitors stock levels in Oracle database
   - Triggers out-of-stock events when inventory falls below thresholds
   - Updates stock levels when new inventory arrives

2. **Supplier Agents** (`supplier_agent.py`)
   - Multiple instances representing different suppliers
   - Listen for stock alerts and respond with competitive offers
   - Each has unique pricing strategies and product catalogs

3. **Stock Manager Agent** (`stock_manager_agent.py`)
   - Collects and evaluates supplier offers
   - Selects best offer based on configurable criteria (price, speed, reliability)
   - Requests manager approval for purchases

4. **Manager Agent** (`manager_agent.py`)
   - Handles approval workflow
   - Sends email notifications to human managers
   - Supports auto-approval for purchases below threshold

### Key Features

- **Real-time inventory monitoring** with configurable thresholds
- **Multi-supplier coordination** with competitive bidding
- **Intelligent offer selection** based on weighted criteria
- **Email-based approval workflow** for human oversight
- **Oracle database integration** for enterprise-grade data storage
- **Configurable pricing strategies** per supplier
- **Comprehensive logging and monitoring**

## Prerequisites

- Python 3.9+
- Oracle Database 11g or higher
- SMTP server access for email notifications
- Google A2A framework (or compatible agent framework)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd a2a-stock-management
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Oracle Client**
   - Download Oracle Instant Client from Oracle website
   - Follow installation instructions for your platform
   - Set environment variables (LD_LIBRARY_PATH, ORACLE_HOME)

## Configuration

1. **Database Setup**
   ```sql
   -- Create database user
   CREATE USER inventory IDENTIFIED BY password;
   GRANT CONNECT, RESOURCE TO inventory;
   GRANT CREATE TABLE, CREATE SEQUENCE TO inventory;
   ```

2. **Update Configuration** (`config/config.yaml`)
   ```yaml
   oracle:
     host: your-oracle-host
     port: 1521
     service_name: YOUR_SERVICE
     username: inventory
     password: your-password
   
   email:
     smtp_server: smtp.gmail.com
     username: your-email@gmail.com
     password: your-app-password
     manager_emails:
       - manager@company.com
   ```

3. **Environment Variables** (optional)
   ```bash
   export ORACLE_HOST=localhost
   export ORACLE_PASSWORD=your-password
   export EMAIL_PASSWORD=your-app-password
   ```

## Running the System

1. **Start the system**
   ```bash
   python main.py
   ```

2. **Monitor logs**
   ```bash
   tail -f logs/system.log
   ```

3. **Check system status** (if web interface is enabled)
   ```
   http://localhost:8080/status
   ```

## Testing the Workflow

1. **Simulate low stock**
   ```sql
   UPDATE inventory 
   SET current_stock = 5 
   WHERE product_id = 'COMP_B';
   ```

2. **Monitor system behavior**
   - Inventory agent detects low stock
   - Supplier agents respond with offers
   - Stock manager selects best offer
   - Manager receives approval email

3. **Approve/reject via email**
   - Reply to approval email with "APPROVE" or "REJECT"
   - System processes decision automatically

## Configuration Options

### Inventory Thresholds
```yaml
inventory:
  thresholds:
    WIDGET_A: 50
    COMP_B: 25
    MAT_C: 100
    TOOL_D: 20
```

### Supplier Pricing Strategies
- **competitive**: Lower prices, longer delivery
- **premium**: Higher prices, faster delivery  
- **standard**: Balanced pricing and delivery

### Selection Criteria Weights
```yaml
stock_manager:
  selection_criteria:
    price_weight: 0.4      # 40% weight on price
    speed_weight: 0.3      # 30% weight on delivery speed
    reliability_weight: 0.3 # 30% weight on supplier reliability
```

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    product_id VARCHAR2(50) PRIMARY KEY,
    product_name VARCHAR2(200) NOT NULL,
    category VARCHAR2(100),
    unit VARCHAR2(20) DEFAULT 'units',
    reorder_level NUMBER DEFAULT 50,
    reorder_quantity NUMBER DEFAULT 100
);
```

### Inventory Table
```sql
CREATE TABLE inventory (
    product_id VARCHAR2(50) PRIMARY KEY,
    current_stock NUMBER DEFAULT 0,
    reserved_stock NUMBER DEFAULT 0,
    available_stock NUMBER DEFAULT 0,
    last_updated DATE DEFAULT SYSDATE
);
```

### Stock Transactions Table
```sql
CREATE TABLE stock_transactions (
    transaction_id NUMBER PRIMARY KEY,
    product_id VARCHAR2(50),
    transaction_type VARCHAR2(20),
    quantity NUMBER,
    unit_cost NUMBER(10,2),
    total_cost NUMBER(10,2),
    supplier_id VARCHAR2(50),
    reference_number VARCHAR2(100),
    transaction_date DATE DEFAULT SYSDATE
);
```

## API Endpoints (if web interface enabled)

- `GET /api/status` - System status
- `GET /api/inventory` - Current inventory levels
- `GET /api/agents` - Agent status
- `GET /api/offers` - Active supplier offers
- `POST /api/approve/{request_id}` - Approve purchase request
- `POST /api/reject/{request_id}` - Reject purchase request

## Troubleshooting

### Database Connection Issues
```bash
# Test Oracle connection
python -c "import cx_Oracle; print(cx_Oracle.connect('user/pass@host:port/service'))"
```

### Agent Communication Issues
```bash
# Check agent logs
grep "ERROR" logs/system.log
```

### Email Issues
```bash
# Test SMTP connection
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); print('OK')"
```

## Development

### Adding New Suppliers
1. Update `config/config.yaml` with supplier details
2. Restart system to load new configuration

### Modifying Selection Criteria
1. Update weights in configuration
2. Restart stock manager agent

### Custom Agent Logic
1. Extend base agent classes in `agents/` directory
2. Implement custom `handle_message()` methods

## Monitoring and Alerts

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Potential issues (low stock, delayed responses)
- **ERROR**: System errors requiring attention
- **CRITICAL**: System failures

### Email Notifications
- Stock low alerts
- Purchase approval requests
- Order confirmations
- System error alerts

## Security Considerations

- Database credentials stored in configuration files
- Email passwords should use app-specific passwords
- Agent communication should be encrypted in production
- Access control for approval endpoints

## Performance Tuning

### Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_inventory_stock ON inventory(current_stock);
CREATE INDEX idx_products_category ON products(category);
```

### Agent Configuration
```yaml
inventory:
  check_interval: 30  # More frequent checks for critical systems

stock_manager:
  offer_timeout: 180  # Faster decision making
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Production Considerations
- Use environment variables for sensitive data
- Set up proper logging aggregation
- Configure health checks
- Implement backup strategies for database

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the logs in `logs/system.log`
- Review configuration in `config/config.yaml`
- Contact system administrator

## Version History

- **v1.0.0**: Initial release with basic A2A functionality
- **v1.1.0**: Added email notifications and approval workflow
- **v1.2.0**: Enhanced supplier selection criteria
- **v1.3.0**: Web dashboard and monitoring interface