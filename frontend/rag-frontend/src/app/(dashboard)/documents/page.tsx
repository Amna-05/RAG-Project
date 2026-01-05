"use client";

import { useState, useRef } from "react";
import { FileText, Upload, X, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { apiClient } from "@/lib/api/client";

interface Document {
  id: string;
  filename: string;
  size: number;
  uploadedAt: Date;
  status: "pending" | "processing" | "completed" | "failed";
}

/**
 * Documents Page
 *
 * Upload and manage documents with backend integration
 */
export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files) {
      handleFiles(files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    const file = files[0]; // Handle one file at a time
    if (!file) return;

    // Validate file type
    const allowedTypes = [".pdf", ".docx", ".txt", ".json"];
    const fileExt = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      toast.error(`Unsupported file type. Allowed: ${allowedTypes.join(", ")}`);
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error("File size exceeds 10MB limit");
      return;
    }

    // Add to documents list
    const docId = Date.now().toString();
    const newDoc: Document = {
      id: docId,
      filename: file.name,
      size: file.size,
      uploadedAt: new Date(),
      status: "pending",
    };

    setDocuments((prev) => [newDoc, ...prev]);
    setIsUploading(true);

    try {
      // Upload to backend
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiClient.post("/rag/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const data = response.data;

      // Update document status
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === docId ? { ...doc, status: "completed" } : doc
        )
      );

      toast.success(`${file.name} uploaded successfully!`);
    } catch (error) {
      console.error("Upload error:", error);
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === docId ? { ...doc, status: "failed" } : doc
        )
      );
      toast.error("Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const removeDocument = (id: string) => {
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Documents
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Upload PDF, DOCX, TXT, or JSON files
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`rounded-lg border-2 border-dashed p-8 text-center transition ${
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50"
        }`}
      >
        <div className="flex justify-center mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
            <Upload className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
          Drag and drop your documents
        </h3>
        <p className="text-slate-600 dark:text-slate-400 mb-4">
          or click the button to browse
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.json"
          onChange={handleFileInput}
          className="hidden"
          disabled={isUploading}
        />
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="gap-2"
        >
          {isUploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              Browse Files
            </>
          )}
        </Button>
      </div>

      {/* Documents List */}
      {documents.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Uploaded Documents
          </h2>
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border border-slate-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-800"
              >
                <div className="flex items-center gap-3 flex-1">
                  <FileText className="h-5 w-5 text-slate-400" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 dark:text-white truncate">
                      {doc.filename}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {formatFileSize(doc.size)} •{" "}
                      {doc.uploadedAt.toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {doc.status === "pending" || doc.status === "processing" ? (
                    <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Processing...</span>
                    </div>
                  ) : doc.status === "completed" ? (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm">Ready</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm">Failed</span>
                    </div>
                  )}

                  {doc.status !== "pending" && doc.status !== "processing" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDocument(doc.id)}
                      className="text-red-600 dark:text-red-400 hover:text-red-700"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {documents.length === 0 && !isUploading && (
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-8 text-center">
          <p className="text-slate-600 dark:text-slate-400">
            No documents uploaded yet. Start by uploading your first document!
          </p>
        </div>
      )}
    </div>
  );
}
