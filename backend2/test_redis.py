import redis
import yaml
import sys
import os

def test_redis_connection():
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    redis_config = config['redis']
    
    try:
        # Create Redis client
        r = redis.from_url(redis_config['url'])
        
        # Test connection
        r.ping()
        print("✅ Successfully connected to Redis!")
        
        # Test basic operations
        r.set('test_key', 'Hello Redis!')
        value = r.get('test_key')
        print(f"✅ Successfully set and retrieved value: {value.decode()}")
        
        # Clean up
        r.delete('test_key')
        print("✅ Successfully cleaned up test data")
        
    except redis.ConnectionError as e:
        print("❌ Failed to connect to Redis!")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Redis is installed and running")
        print("2. Check if Redis service is running (services.msc)")
        print("3. Verify Redis port (default: 6379) is not blocked")
        print("4. Check your Redis configuration in config.yaml")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_redis_connection() 