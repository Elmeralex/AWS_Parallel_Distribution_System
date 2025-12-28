import pymysql
import redis

# Configuration - Replace with your real endpoints
RDS_HOST = 'tmeas-database.cluster-cal1sou8l5ld.us-east-1.rds.amazonaws.com'
REDIS_HOST = 'master.tmeas-redis-cluster.ks1nij.use1.cache.amazonaws.com'
DB_USER = 'admin'
DB_PASSWORD = '8J8vO<g[$)A0>*QEEX~9R9sb3Ld<'

def setup_distributed_data():
    try:
        # 1. Setup MySQL (RDS)
        connection = pymysql.connect(
            host=RDS_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )

        with connection.cursor() as cursor:
            # Create Database
            cursor.execute("CREATE DATABASE IF NOT EXISTS ecommerce;")
            cursor.execute("USE ecommerce;")

            # Create Orders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'completed'
                );
            """)
        connection.commit()
        print(" MySQL Database and Table ready.")

        # 2. Setup Redis Stock (ElastiCache)
        r = redis.StrictRedis(host=REDIS_HOST, port=6379, ssl=True, decode_responses=True)
        r.set('laptop_stock', 100)
        print(f" Redis Stock initialized to: {r.get('laptop_stock')}")

    except Exception as e:
        print(f" Setup failed: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    setup_distributed_data()
