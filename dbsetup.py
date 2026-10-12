import pymysql
import redis

DB_CONFIG = {
    'host': 'tmeas-database.c2ve0sisuaoc.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'p|1O7HOVS(KaBp7$QQ6Sl64#c4r4' 
}


def setup_database():
    try:
        # Connect to the RDS instance generally
        conn = pymysql.connect(**DB_CONFIG)
        conn.autocommit(True) 
        
        with conn.cursor() as cursor:
            # Create and switch to the database
            cursor.execute("CREATE DATABASE IF NOT EXISTS ecommerce")
            cursor.execute("USE ecommerce")

            #Clean up table and redis 
            print("Cleaning up tables and redis")
            # Drop Orders first because it references Products (Foreign Key constraint)
            cursor.execute("DROP TABLE IF EXISTS orders")
            cursor.execute("DROP TABLE IF EXISTS products")

            redis_chache = redis.StrictRedis(
            	host='master.tmeas-redis-cluster.u1kzxf.use1.cache.amazonaws.com',
            	port=6379,
            	ssl=True,
            	decode_responses=True
            )
            redis_chache.flushall() # This deletes everything in Redis for rebuild

            #Table create
            print("Creating Products table")
            cursor.execute("""
                CREATE TABLE products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price VARCHAR(20) NOT NULL,
                    category VARCHAR(50),
                    quantity INT,
                    image_url VARCHAR(255)
                )
            """)

            print("Creating Orders table")
            cursor.execute("""
                CREATE TABLE orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    product_id INT NOT NULL,
                    status VARCHAR(20) DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
        print("Database setup complete")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database()
