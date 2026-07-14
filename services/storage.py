import os
from supabase import create_client, Client
from config import Config

class SupabaseStorageService:
    def __init__(self):
        self.bucket_name = 'attendance-data'
        self.client = None
        
        if Config.SUPABASE_URL and Config.SUPABASE_KEY:
            try:
                self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            except Exception as e:
                print(f"[Storage] Failed to initialize Supabase client: {e}")

    def is_configured(self):
        return self.client is not None

    def upload_file(self, local_file_path, storage_path):
        """Uploads a local file to Supabase Storage."""
        if not self.is_configured():
            return False, "Supabase not configured."
            
        try:
            with open(local_file_path, 'rb') as f:
                # Upsert ensures it overwrites if it already exists
                self.client.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=f,
                    file_options={"upsert": "true"}
                )
            return True, f"Successfully uploaded {storage_path}"
        except Exception as e:
            return False, f"Upload failed: {str(e)}"

    def download_file(self, storage_path, local_destination):
        """Downloads a file from Supabase Storage to the local file system."""
        if not self.is_configured():
            return False, "Supabase not configured."
            
        try:
            res = self.client.storage.from_(self.bucket_name).download(storage_path)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_destination), exist_ok=True)
            with open(local_destination, 'wb') as f:
                f.write(res)
            return True, f"Successfully downloaded {storage_path}"
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def list_files(self, prefix=""):
        """Lists files in the bucket matching the prefix."""
        if not self.is_configured():
            return []
            
        try:
            res = self.client.storage.from_(self.bucket_name).list(prefix)
            return res if isinstance(res, list) else []
        except Exception as e:
            print(f"[Storage] List failed: {e}")
            return []

# Create a singleton instance
storage_service = SupabaseStorageService()
