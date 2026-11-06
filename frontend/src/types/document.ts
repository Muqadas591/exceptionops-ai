export interface DocumentRecord {
  id: number;
  original_filename: string;
  extension: string;
  content_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListParams {
  limit?: number;
  offset?: number;
}

export interface DocumentUploadError {
  message: string;
  statusCode?: number;
}