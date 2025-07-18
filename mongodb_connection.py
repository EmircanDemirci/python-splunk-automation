import pymongo
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class MongoConnector:
    def __init__(self, connection_string, database_name, collection_name):
        """
        MongoDB bağlantısı için constructor
        
        Args:
            connection_string (str): MongoDB bağlantı string'i
            database_name (str): Veritabanı adı
            collection_name (str): Koleksiyon adı
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.database = None
        self.collection = None
    
    def connect(self):
        """
        MongoDB'ye bağlan ve koleksiyonu döndür
        
        Returns:
            pymongo.collection.Collection: MongoDB koleksiyonu
        """
        try:
            # MongoDB client'ı oluştur
            self.client = MongoClient(self.connection_string)
            
            # Bağlantıyı test et
            self.client.admin.command('ping')
            logger.info("MongoDB bağlantısı başarılı")
            
            # Database ve collection'ı al
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            return self.collection
            
        except Exception as e:
            logger.error(f"MongoDB bağlantı hatası: {e}")
            raise e
    
    def close_connection(self):
        """MongoDB bağlantısını kapat"""
        if self.client:
            self.client.close()
            logger.info("MongoDB bağlantısı kapatıldı")
    
    def test_connection(self):
        """Bağlantıyı test et"""
        try:
            if self.client:
                # Ping komutu ile bağlantıyı test et
                self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"Bağlantı testi başarısız: {e}")
            return False