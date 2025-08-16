import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    load_dotenv()
    
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME")
    
    print(f"Testing connection to: {mongodb_url.replace(':password', ':***')}")
    print(f"Database: {database_name}")
    
    try:
        client = AsyncIOMotorClient(mongodb_url)
        
        # Test the connection
        await client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client[database_name]
        collections = await db.list_collection_names()
        print(f"✅ Database access successful! Collections: {collections}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())
