/**
 * C.O.V.E.R.T - File Upload Component with Encryption
 */

import { useState, useCallback, useRef } from 'react';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  PhotoIcon,
  VideoCameraIcon,
  XMarkIcon,
  LockClosedIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useReportStore } from '@/stores/reportStore';

interface FileUploadProps {
  accept?: string;
  maxFiles?: number;
  maxSize?: number; // in bytes
  onFilesChange?: (files: File[]) => void;
  showEncryptionStatus?: boolean;
}

interface FilePreview {
  file: File;
  preview?: string;
  encrypted: boolean;
  error?: string;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/gif',
  'video/mp4',
  'application/zip',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(type: string) {
  if (type.startsWith('image/')) return PhotoIcon;
  if (type.startsWith('video/')) return VideoCameraIcon;
  return DocumentIcon;
}

export function FileUpload({
  accept = '.pdf,.jpg,.jpeg,.png,.gif,.mp4,.zip,.doc,.docx',
  maxFiles = 5,
  maxSize = MAX_FILE_SIZE,
  onFilesChange,
  showEncryptionStatus = true,
}: FileUploadProps) {
  const [previews, setPreviews] = useState<FilePreview[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { draft, addFile, removeFile } = useReportStore();

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File type "${file.type}" is not allowed`;
    }

    // Check file size
    if (file.size > maxSize) {
      return `File size exceeds ${formatFileSize(maxSize)} limit`;
    }

    return null;
  }, [maxSize]);

  const processFiles = useCallback(async (files: FileList | File[]) => {
    setError(null);
    const fileArray = Array.from(files);

    // Check max files
    if (draft.files.length + fileArray.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`);
      return;
    }

    const newPreviews: FilePreview[] = [];

    for (const file of fileArray) {
      const validationError = validateFile(file);

      if (validationError) {
        newPreviews.push({
          file,
          encrypted: false,
          error: validationError,
        });
        continue;
      }

      // Create preview for images
      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      newPreviews.push({
        file,
        preview,
        encrypted: false, // Will be encrypted during submission
      });

      // Add to store
      addFile(file);
    }

    setPreviews((prev) => [...prev, ...newPreviews]);
    onFilesChange?.(draft.files);
  }, [draft.files, maxFiles, validateFile, addFile, onFilesChange]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(e.target.files);
    }
  }, [processFiles]);

  const handleRemoveFile = useCallback((index: number) => {
    // Revoke object URL if exists
    if (previews[index]?.preview) {
      URL.revokeObjectURL(previews[index].preview!);
    }

    setPreviews((prev) => prev.filter((_, i) => i !== index));
    removeFile(index);
    onFilesChange?.(draft.files);
  }, [previews, removeFile, draft.files, onFilesChange]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors
          ${isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-neutral-300 hover:border-neutral-400 bg-neutral-50'
          }
          ${draft.files.length >= maxFiles ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={draft.files.length >= maxFiles}
        />

        <CloudArrowUpIcon className={`
          mx-auto h-12 w-12
          ${isDragging ? 'text-primary-500' : 'text-neutral-400'}
        `} />

        <p className="mt-2 text-sm text-neutral-600">
          <span className="font-semibold text-primary-600">Click to upload</span>
          {' or drag and drop'}
        </p>
        <p className="mt-1 text-xs text-neutral-500">
          PDF, Images, Videos up to {formatFileSize(maxSize)}
        </p>
        <p className="mt-1 text-xs text-neutral-400">
          {draft.files.length}/{maxFiles} files
        </p>

        {showEncryptionStatus && (
          <div className="mt-3 flex items-center justify-center text-xs text-green-600">
            <LockClosedIcon className="h-3 w-3 mr-1" />
            Files will be encrypted before upload
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}

      {/* File Previews */}
      {previews.length > 0 && (
        <div className="space-y-2">
          {previews.map((preview, index) => {
            const FileIcon = getFileIcon(preview.file.type);

            return (
              <div
                key={index}
                className={`
                  flex items-center p-3 rounded-lg border
                  ${preview.error
                    ? 'bg-red-50 border-red-200'
                    : 'bg-white border-neutral-200'
                  }
                `}
              >
                {/* Preview/Icon */}
                {preview.preview ? (
                  <img
                    src={preview.preview}
                    alt={preview.file.name}
                    className="h-12 w-12 object-cover rounded"
                  />
                ) : (
                  <div className="h-12 w-12 flex items-center justify-center bg-neutral-100 rounded">
                    <FileIcon className="h-6 w-6 text-neutral-500" />
                  </div>
                )}

                {/* File Info */}
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 truncate">
                    {preview.file.name}
                  </p>
                  <p className="text-xs text-neutral-500">
                    {formatFileSize(preview.file.size)}
                  </p>
                  {preview.error && (
                    <p className="text-xs text-red-600 mt-1">
                      {preview.error}
                    </p>
                  )}
                </div>

                {/* Encryption Status */}
                {!preview.error && showEncryptionStatus && (
                  <div className="flex items-center text-xs text-green-600 mr-3">
                    <LockClosedIcon className="h-3 w-3 mr-1" />
                    Ready
                  </div>
                )}

                {/* Remove Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveFile(index);
                  }}
                  className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Instructions */}
      <div className="text-xs text-neutral-500 space-y-1">
        <p>Accepted formats: PDF, JPEG, PNG, GIF, MP4, ZIP, DOC, DOCX</p>
        <p>All files are encrypted client-side before upload for maximum privacy</p>
      </div>
    </div>
  );
}

export default FileUpload;
