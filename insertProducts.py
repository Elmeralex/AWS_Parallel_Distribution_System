import pymysql

DB_CONFIG = {
    'host': 'tmeas-database.c2ve0sisuaoc.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'p|1O7HOVS(KaBp7$QQ6Sl64#c4r4',
    'database': 'ecommerce'
}

#Insert items (Default)
products_to_add = [
    {
        "name": "HP Laptop",
        "description": "HP Laptop 15-FD1472TU Gold, FD1473TU BLUE, FD1475TU Silver (Intel Ultra 5 125H, 24GB DDR5, 512GB SSD, Intel® Arc™ Graphics",
        "price": "RM2,600",
        "category": "Personal computers",
        "image_url": "https://cdn1.npcdn.net/images/2491ce81de209e3a7c95535d232b43e9_1766025696.webp?md5id=648e9e6a126696bd6f0eaf62b2b222b0&new_width=1000&new_height=1000&size=max&w=1756978661&from=jpeg&type=1",
        "quantity": 10
    },
    {
        "name": "OATSIDE Original Barista Blend Oat Milk",
        "description": "OATSIDE Barista Blend Original Oat Milk 1L - Dairy Free, Creamy, Zero Added Sugar",
        "price": "RM9.99",
        "category": "Food",
        "image_url": "https://tse4.mm.bing.net/th/id/OIP.bFTE2QwrJ7phSU3jhjmkwwHaHa?rs=1&pid=ImgDetMain&o=7&rm=3",
        "quantity": 10
    },
    {
        "name": "Mini Iron",
        "description": "Mini Iron 220V Seterika Baju 30W Handheld Ironing Machines Steamer Portable Hanging Electric Dry Iron Seterika Wap",
        "price": "RM14.99",
        "category": "Home Appliances",
        "image_url": "https://down-my.img.susercontent.com/file/my-11134208-7r98r-lz71my9y5y0917",
        "quantity": 10
    },
    {
        "name": "Camping Outdoor Tent",
        "description": "Khemah Camping Outdoor Tent for 3-4/6-8 Persons Camping Tent Family Tent Double-Layer Waterproof Rainproof Tent",
        "price": "RM200.99",
        "category": "Sports & Outdoor",
        "image_url": "https://down-my.img.susercontent.com/file/sg-11134202-22100-m5eok0eyi5iv8b",
        "quantity": 10
    }
]

def insert_products():
    try:
        db_conn = pymysql.connect(**DB_CONFIG)
        with db_conn.cursor() as cursor:
            print("Inserting items into RDS...")
            
            for item in products_to_add:
                # Included the quantity column here
                sql = """INSERT INTO products (name, description, price, category, quantity, image_url) 
                         VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (
                    item['name'], 
                    item['description'], 
                    item['price'], 
                    item['category'], 
                    item['quantity'],
                    item['image_url']
                    
                ))
                print(f"Added: {item['name']} (Qty: {item['quantity']})")
        
        db_conn.commit()
        print("\nDatabase updated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db_conn' in locals():
            db_conn.close()

if __name__ == "__main__":
    insert_products()
