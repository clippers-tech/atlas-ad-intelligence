"use client";

import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

interface CsvUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export default function CsvUploader({ onUpload, isUploading }: CsvUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.name.endsWith(".csv")) {
      setSelectedFile(file);
    }
  }, []);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleUpload = () => {
    if (selectedFile) onUpload(selectedFile);
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
          isDragOver
            ? "border-violet-400 bg-violet-500/10"
            : "border-gray-700 bg-gray-800/40 hover:border-gray-600"
        }`}
        onClick={() => document.getElementById("csv-file-input")?.click()}
      >
        <input
          id="csv-file-input"
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          className="sr-only"
        />
        <div className="flex flex-col items-center gap-3">
          <div className="text-4xl">📂</div>
          <div>
            <p className="text-sm font-medium text-gray-300">
              {selectedFile
                ? selectedFile.name
                : "Drop your CSV here, or click to browse"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Expected columns: email, stage, revenue, notes
            </p>
          </div>
          {selectedFile && (
            <span className="text-xs text-violet-400 font-medium">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </span>
          )}
        </div>
      </div>

      {/* Upload Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
        >
          {isUploading ? <LoadingSpinner size={16} /> : "⬆️"}
          {isUploading ? "Uploading…" : "Upload CSV"}
        </button>
        {selectedFile && !isUploading && (
          <button
            onClick={() => setSelectedFile(null)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
