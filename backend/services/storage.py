import os
import re
from supabase import create_client, Client
from backend.config import settings

class SupabaseStorage:
    def __init__(self):
        try:
            self.url: str = settings.SUPABASE_URL
            self.key: str = settings.SUPABASE_KEY
            self.bucket: str = settings.SUPABASE_BUCKET
            
            if not self.url or not self.key:
                print("Warning: Supabase credentials missing.")
                self.client = None
            else:
                self.client: Client = create_client(self.url, self.key)
                self._ensure_bucket_exists()

        except Exception as e:
            print(f"Error initializing Supabase: {e}")
            self.client = None

    def _ensure_bucket_exists(self):
        """Check if the configured bucket exists; if not, create it as public."""
        if not self.client:
            return
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            print(f"[DEBUG] Available Buckets: {bucket_names}")

            if self.bucket not in bucket_names:
                print(f"[INFO] Bucket '{self.bucket}' not found. Creating it now...")
                try:
                    self.client.storage.create_bucket(
                        self.bucket,
                        options={"public": True}
                    )
                    print(f"[INFO] Bucket '{self.bucket}' created successfully (public).")
                except Exception as create_err:
                    print(f"[ERROR] Could not create bucket '{self.bucket}': {create_err}")
                    print("[HINT] You may need to use a Supabase Service Role key instead of the anon key,")
                    print("       or create the bucket manually in the Supabase Dashboard.")
            else:
                print(f"[DEBUG] Bucket '{self.bucket}' found.")
                # Try to update the bucket to be public (in case it's private)
                try:
                    self.client.storage.update_bucket(
                        self.bucket,
                        options={"public": True}
                    )
                    print(f"[INFO] Bucket '{self.bucket}' set to public.")
                except Exception as update_err:
                    print(f"[DEBUG] Could not update bucket to public (may need service role key): {update_err}")

        except Exception as e:
            print(f"[DEBUG] Could not list/manage buckets: {e}")

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """
        Uploads file to Supabase Storage and returns a working URL.
        Tries public URL first, falls back to signed URL.
        """
        if not self.client:
            return None
            
        try:
            # Sanitize filename (replace spaces, parens with underscores)
            safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
            
            print(f"[DEBUG] Uploading to Bucket: '{self.bucket}' | File: '{safe_filename}'")

            # Using 'upsert' to overwrite if exists
            self.client.storage.from_(self.bucket).upload(
                path=safe_filename,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            # Try to get a working URL
            url = self._get_file_url(safe_filename)
            print(f"[INFO] Uploaded to Supabase: {url}")
            return url
            
        except Exception as e:
            print(f"[ERROR] Supabase upload failed for '{filename}': {e}")
            if hasattr(e, 'response'):
                print(f"[ERROR] Response: {e.response}")
            return None

    def _get_file_url(self, filename: str) -> str:
        """Get a working URL for a file. Uses signed URL (works for private buckets)."""
        # Use signed URL - works for both private and public buckets
        # Valid for 7 days (604800 seconds). Re-upload refreshes the URL.
        try:
            signed = self.client.storage.from_(self.bucket).create_signed_url(
                filename, 604800
            )
            if signed and signed.get("signedURL"):
                print(f"[DEBUG] Generated signed URL for '{filename}'")
                return signed["signedURL"]
        except Exception as e:
            print(f"[WARN] Could not create signed URL: {e}")

        # Fallback: public URL (only works if bucket is public)
        try:
            public_url = self.client.storage.from_(self.bucket).get_public_url(filename)
            if public_url:
                return public_url
        except Exception:
            pass

        # Last resort: construct URL manually
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{filename}"

