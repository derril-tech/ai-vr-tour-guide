"""
Storage client for file operations.
"""

import logging
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    logging.warning("boto3 not available for S3 operations")

logger = logging.getLogger(__name__)


class StorageClient:
    """S3-compatible storage client."""
    
    def __init__(self, bucket: str, region: str, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.s3_client = None
        
        if HAS_BOTO3:
            try:
                session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                
                # Configure client
                config = {}
                if endpoint:
                    config['endpoint_url'] = endpoint
                
                self.s3_client = session.client('s3', **config)
                logger.info(f"Storage client initialized for bucket {bucket}")
                
            except Exception as e:
                logger.error(f"Failed to initialize storage client: {str(e)}")
    
    async def upload_file(self, key: str, content: bytes, content_type: Optional[str] = None) -> str:
        """Upload file content to storage."""
        if not self.s3_client:
            logger.warning(f"Storage not available, skipping upload of {key}")
            return f"mock://{self.bucket}/{key}"
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                **extra_args
            )
            
            logger.info(f"Uploaded file {key} to {self.bucket}")
            return f"s3://{self.bucket}/{key}"
            
        except ClientError as e:
            logger.error(f"Error uploading file {key}: {str(e)}")
            raise e
    
    async def download_file(self, key: str) -> bytes:
        """Download file content from storage."""
        if not self.s3_client:
            logger.warning(f"Storage not available, cannot download {key}")
            return b""
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read()
            logger.info(f"Downloaded file {key} from {self.bucket}")
            return content
            
        except ClientError as e:
            logger.error(f"Error downloading file {key}: {str(e)}")
            raise e
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from storage."""
        if not self.s3_client:
            logger.warning(f"Storage not available, skipping deletion of {key}")
            return True
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file {key} from {self.bucket}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file {key}: {str(e)}")
            raise e
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in storage."""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for file access."""
        if not self.s3_client:
            return f"mock://{self.bucket}/{key}"
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {key}: {str(e)}")
            raise e


# Global storage client instance
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get storage client instance."""
    global _storage_client
    
    if _storage_client is None:
        from .config import get_settings
        settings = get_settings()
        _storage_client = StorageClient(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            access_key=settings.s3_access_key_id,
            secret_key=settings.s3_secret_access_key,
            endpoint=settings.s3_endpoint
        )
    
    return _storage_client
