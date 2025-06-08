# A2A Stock Management System with Gemini LLM

A sophisticated multi-agent system built with Google's A2A framework and enhanced with Gemini LLM for intelligent inventory management and supplier coordination.

## 🚀 Features

### Core A2A Framework
- **Multi-agent architecture** using Google's A2A communication patterns
- **Redis-based message transport** for reliable agent communication
- **Service discovery and registry** for dynamic agent management
- **Asynchronous message handling** with proper error handling

### Gemini LLM Integration
- **Intelligent offer generation** by supplier agents using LLM
- **Smart offer evaluation** and ranking with AI analysis
- **Automated report generation** for manager decision-making
- **Enhanced email communications** with AI-generated content
- **Market analysis and pricing intelligence**

### System Components
- **Inventory Agent**: Monitors stock levels with intelligent threshold analysis
- **Supplier Agents**: Generate competitive offers using LLM pricing strategies
- **Stock Manager Agent**: Evaluates offers using AI-powered decision making
- **Manager Agent**: Handles approvals with LLM-enhanced reporting
- **Oracle Database Integration**: Enterprise-grade data persistence
- **Real-time Web Dashboard**: Live monitoring and control interface

## 📋 Prerequisites

### Required Software
- Python 3.9+
- Oracle Database 11g or higher
- Redis Server 6.0+
- Node.js 16+ (for frontend)

### API Keys
- **Gemini API Key**: Required for LLM functionality
  ```bash
  export GEMINI_API_KEY="your_gemini_api_key_here"
  ```

### System Dependencies
- Oracle Instant Client
- Redis server running on localhost:6379
- SMTP server access for email notifications

## 🛠️ Installation

### 1. Clone and Setup Backend
```bash
git clone <repository-url>
cd a2a-stock-management/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Oracle Database Setup
```sql
-- Create database user
CREATE USER inventory IDENTIFIED BY password;
GRANT CONNECT, RESOURCE TO inventory;
GRANT CREATE TABLE, CREATE SEQUENCE TO inventory;
GRANT UNLIMITED TABLESPACE TO inventory;
```

### 3. Redis Setup
```bash
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
```

### 4. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano config/config.yaml
```

Update the following in `config/config.yaml`:
```yaml
oracle:
  host: your-oracle-host
  username: inventory
  password: your-password

email:
  username: your-email@gmail.com
  password: your-app-password
  manager_emails:
    - manager@company.com

gemini:
  api_key: ""  # Set via GEMINI_API_KEY environment variable
```

### 5. Environment Variables
```bash
# Required
export GEMINI_API_KEY="your_gemini_api_key"

# Optional
export ORACLE_PASSWORD="your_oracle_password"
export EMAIL_PASSWORD="your_email_password"
export REDIS_URL="redis://localhost:6379"
```

## 🚀 Running the System

### Start Backend Services
```bash
# Ensure Redis is running
redis-cli ping

# Start the A2A system
cd backend
python main.py
```

### Start Frontend Dashboard
```bash
# In a new terminal
npm install
npm run dev
```

### Verify System Status
```bash
# Check API endpoints
curl http://localhost:8000/api/status
curl http://localhost:8000/api/inventory
```

## 🧪 Testing the LLM-Enhanced Workflow

### 1. Simulate Stock Depletion
```bash
# Via API
curl -X POST http://localhost:8000/api/simulate/stock-depletion \
  -H "Content-Type: application/json" \
  -d '{"product_id": "COMP_B"}'

# Or via SQL
UPDATE inventory 
SET current_stock = 5 
WHERE product_id = 'COMP_B';
```

### 2. Monitor AI-Enhanced Process
1. **Inventory Agent** detects low stock and triggers alert
2. **Supplier Agents** generate intelligent offers using Gemini LLM
3. **Stock Manager** evaluates offers with AI analysis
4. **Manager Agent** sends LLM-enhanced approval email
5. **Human Manager** receives detailed AI report and recommendations

### 3. Expected LLM Enhancements
- **Intelligent Pricing**: Suppliers use market analysis for competitive offers
- **Smart Evaluation**: Multi-criteria decision making with confidence scores
- **Rich Reports**: Executive summaries with risk assessments
- **Enhanced Communications**: Professional emails with AI insights

## 📊 Web Dashboard Features

### Real-time Monitoring
- **Live inventory status** with color-coded alerts
- **Agent communication** visualization
- **Supplier offer comparison** with LLM confidence scores
- **System logs** with AI-generated insights

### Interactive Controls
- **Manual approval/rejection** of purchase requests
- **Stock simulation** for testing workflows
- **Agent status monitoring** and health checks
- **Real-time updates** via WebSocket connections

## 🔧 Configuration Options

### LLM Settings
```yaml
gemini:
  model_name: "gemini-pro"  # or "gemini-pro-vision"
  temperature: 0.7          # Creativity level (0.0-1.0)
  max_tokens: 2048          # Response length limit
  timeout: 30               # Request timeout in seconds
```

### Agent Behavior
```yaml
inventory:
  check_interval: 60        # Stock check frequency (seconds)
  
stock_manager:
  offer_timeout: 300        # Wait time for offers (seconds)
  selection_criteria:
    price_weight: 0.4       # Price importance (0.0-1.0)
    speed_weight: 0.3       # Delivery speed importance
    reliability_weight: 0.3 # Supplier reliability importance

manager:
  auto_approve_threshold: 1000.0  # Auto-approve below this amount
```

### Supplier Strategies
```yaml
suppliers:
  '1':
    pricing_strategy: competitive  # competitive, premium, standard
    location: US-East
    catalog:
      WIDGET_A:
        base_price: 10.50
        min_order_quantity: 50
```

## 🐛 Troubleshooting

### Common Issues

#### Gemini API Errors
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API access
python -c "import google.generativeai as genai; genai.configure(api_key='$GEMINI_API_KEY'); print('API key valid')"
```

#### Database Connection
```bash
# Test Oracle connection
python -c "import cx_Oracle; print(cx_Oracle.connect('user/pass@host:port/service'))"

# Check Oracle environment
echo $ORACLE_HOME
echo $LD_LIBRARY_PATH
```

#### Redis Connection
```bash
# Test Redis
redis-cli ping

# Check Redis logs
sudo journalctl -u redis-server -f
```

#### Agent Communication
```bash
# Check Redis messages
redis-cli monitor

# View agent logs
tail -f logs/system.log | grep "Agent"
```

### Performance Optimization

#### Database Tuning
```sql
-- Add indexes for better performance
CREATE INDEX idx_inventory_stock ON inventory(current_stock);
CREATE INDEX idx_products_category ON products(category);
```

#### Redis Optimization
```bash
# Increase Redis memory
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### LLM Response Caching
```python
# Enable response caching in production
GEMINI_CACHE_RESPONSES = True
CACHE_TTL = 3600  # 1 hour
```

## 📈 Monitoring and Logging

### System Metrics
- **Agent response times** and message throughput
- **LLM API usage** and response quality
- **Database performance** and connection health
- **Email delivery** success rates

### Log Analysis
```bash
# View system logs
tail -f logs/system.log

# Filter by agent type
grep "InventoryAgent" logs/system.log

# Monitor LLM interactions
grep "Gemini" logs/system.log
```

### Health Checks
```bash
# System status
curl http://localhost:8000/api/status

# Individual agent status
curl http://localhost:8000/api/agents/inventory_agent/status
```

## 🔒 Security Considerations

### API Key Management
- Store Gemini API key in environment variables
- Use separate keys for development/production
- Implement key rotation policies

### Database Security
- Use strong passwords and encrypted connections
- Implement proper user permissions
- Regular security updates

### Email Security
- Use app-specific passwords for Gmail
- Implement email encryption for sensitive data
- Validate email addresses and content

## 🚀 Deployment

### Docker Deployment
```bash
# Build container
docker build -t a2a-stock-management .

# Run with environment variables
docker run -d \
  --name a2a-system \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -e ORACLE_PASSWORD=$ORACLE_PASSWORD \
  -p 8000:8000 \
  a2a-stock-management
```

### Production Considerations
- Use production-grade Redis cluster
- Implement proper logging aggregation
- Set up monitoring and alerting
- Configure load balancing for high availability

## 📚 API Documentation

### REST Endpoints
- `GET /api/status` - System status and health
- `GET /api/inventory` - Current inventory levels
- `GET /api/offers` - Active supplier offers
- `GET /api/approvals` - Pending manager approvals
- `POST /api/approvals/{id}/approve` - Approve purchase request
- `POST /api/approvals/{id}/reject` - Reject purchase request

### WebSocket Events
- `inventory_update` - Real-time stock level changes
- `new_offer` - New supplier offers received
- `agent_status_update` - Agent state changes
- `system_log` - System events and messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review system logs in `logs/system.log`
- Verify configuration in `config/config.yaml`
- Test individual components using the API endpoints

## 🔮 Future Enhancements

- **Advanced LLM Models**: Integration with GPT-4, Claude, or other models
- **Predictive Analytics**: Demand forecasting using historical data
- **Multi-language Support**: International supplier communication
- **Blockchain Integration**: Supply chain transparency and verification
- **Mobile App**: Manager approval interface for mobile devices