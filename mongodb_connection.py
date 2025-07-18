import pymongo
import logging

logger = logging.getLogger(__name__)

class MongoConnector:
    def __init__(self, connection_string, database_name, collection_name):
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.database = None
        self.collection = None
    
    def connect(self):
        """MongoDB'ye bağlan ve collection'ı döndür"""
        try:
            self.client = pymongo.MongoClient(self.connection_string)
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Bağlantıyı test et
            self.client.admin.command('ping')
            logger.info(f"✅ MongoDB bağlantısı başarılı: {self.database_name}.{self.collection_name}")
            
            return self.collection
        except Exception as e:
            logger.error(f"❌ MongoDB bağlantı hatası: {e}")
            raise ConnectionError(f"MongoDB'ye bağlanılamadı: {e}")
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.client:
            self.client.close()
            logger.info("🔒 MongoDB bağlantısı kapatıldı")