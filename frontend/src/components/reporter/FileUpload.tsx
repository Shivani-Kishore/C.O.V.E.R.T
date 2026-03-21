/**
 * C.O.V.E.R.T - File Upload Component with Encryption
 */

import { useState, useCallback, useRef, useEffect } from 'react';
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

  useEffect(() => {
    const objectUrls: string[] = [];

    if (draft.files.length > 0) {
      const restored: FilePreview[] = draft.files.map((file) => {
        let preview: string | undefined;
        if (file.type.startsWith('image/')) {
          preview = URL.createObjectURL(file);
          objectUrls.push(preview);
        }
        return { file, preview, encrypted: false };
      });
      setPreviews(restored);
    } else if (draft.fileMetadata.length > 0) {
      const metadataPreviews: FilePreview[] = draft.fileMetadata.map((meta) => ({
        file: new File([], meta.name, { type: meta.type, lastModified: meta.lastModified }),
        encrypted: false,
        error: 'File data lost after page reload. Please re-upload.',
      }));
      setPreviews(metadataPreviews);
    }

    return () => {
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File type "${file.type}" is not allowed`;
    }
    if (file.size > maxSize) {
      return `File size exceeds ${formatFileSize(maxSize)} limit`;
    }
    return null;
  }, [maxSize]);

  const processFiles = useCallback(async (files: FileList | File[]) => {
    setError(null);
    const fileArray = Array.from(files);

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

      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      newPreviews.push({
        file,
        preview,
        encrypted: false,
      });

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
          relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
          transition-all duration-200
          ${isDragging
            ? 'border-neutral-400 bg-neutral-900'
            : 'border-neutral-700 hover:border-neutral-500 bg-neutral-950'
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
          mx-auto h-14 w-14 transition-colors
          ${isDragging ? 'text-white' : 'text-neutral-600'}
        `} />

        <p className="mt-3 text-base text-neutral-400">
          <span className="font-bold text-white">Click to upload</span>
          {' or drag and drop'}
        </p>
        <p className="mt-2 text-sm text-neutral-500">
          PDF, Images, Videos up to {formatFileSize(maxSize)}
        </p>
        <p className="mt-1 text-sm text-neutral-600 font-medium">
          {draft.files.length}/{maxFiles} files
        </p>

        {showEncryptionStatus && (
          <div className="mt-4 inline-flex items-center px-3 py-1.5 bg-green-950/30 text-green-400 border border-green-900/50 rounded-full text-xs font-semibold">
            <LockClosedIcon className="h-3.5 w-3.5 mr-1.5" />
            Files will be encrypted before upload
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center p-3 bg-red-950/20 border border-red-900/50 rounded-lg text-red-400 text-sm">
          <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}

      {/* File Previews */}
      {previews.length > 0 && (
        <div className="space-y-3">
          {previews.map((preview, index) => {
            const FileIcon = getFileIcon(preview.file.type);

            return (
              <div
                key={index}
                className={`
                  flex items-center p-4 rounded-xl border transition-all duration-200
                  ${preview.error
                    ? 'bg-red-950/20 border-red-900/50'
                    : 'bg-neutral-950 border-neutral-800 hover:border-neutral-600'
                  }
                `}
              >
                {/* Preview/Icon */}
                {preview.preview ? (
                  <img
                    src={preview.preview}
                    alt={preview.file.name}
                    className="h-14 w-14 object-cover rounded-lg"
                  />
                ) : (
                  <div className="h-14 w-14 flex items-center justify-center bg-neutral-900 rounded-lg">
                    <FileIcon className="h-7 w-7 text-neutral-500" />
                  </div>
                )}

                {/* File Info */}
                <div className="ml-4 flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {preview.file.name}
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5 font-medium">
                    {formatFileSize(preview.file.size)}
                  </p>
                  {preview.error && (
                    <p className="text-xs text-red-400 mt-1.5 font-medium">
                      {preview.error}
                    </p>
                  )}
                </div>

                {/* Encryption Status */}
                {!preview.error && showEncryptionStatus && (
                  <div className="flex items-center px-2.5 py-1 bg-green-950/30 text-green-400 border border-green-900/50 rounded-lg text-xs font-semibold mr-3">
                    <LockClosedIcon className="h-3.5 w-3.5 mr-1" />
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
                  className="p-2 text-neutral-500 hover:text-red-400 hover:bg-red-950/20 rounded-lg transition-all duration-200"
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
