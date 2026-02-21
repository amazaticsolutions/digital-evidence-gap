import { Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { MediaUploadCard } from '../components/MediaUploadCard';
import {
  FILE_SIZE_UNITS,
  ACCEPTED_FILE_TYPES,
  UPLOAD_SIMULATION_INTERVAL_MS,
  UPLOAD_SIMULATION_MAX_INCREMENT,
} from '../../constants/newCase.constants';
import { createCase } from '../../services/cases.service';

interface MediaFile {
  id: string;
  name: string;
  type: 'video' | 'image' | 'audio' | 'document';
  size: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
}

export function NewCase() {
  const navigate = useNavigate();
  const [caseTitle, setCaseTitle] = useState('');
  const [caseDescription, setCaseDescription] = useState('');
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Simulate file upload with progress
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const newFile: MediaFile = {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        type: getFileType(file.type),
        size: formatFileSize(file.size),
        progress: 0,
        status: 'uploading',
      };

      setMediaFiles((prev) => [...prev, newFile]);
      setIsUploading(true);

      // Simulate upload progress
      simulateUpload(newFile.id);
    });
  };

  const simulateUpload = (fileId: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * UPLOAD_SIMULATION_MAX_INCREMENT;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setMediaFiles((prev) =>
          prev.map((file) =>
            file.id === fileId ? { ...file, progress: 100, status: 'completed' } : file
          )
        );
        // Check if all uploads are complete
        setMediaFiles((prev) => {
          const allComplete = prev.every((f) => f.status === 'completed');
          if (allComplete) {
            setIsUploading(false);
          }
          return prev;
        });
      } else {
        setMediaFiles((prev) =>
          prev.map((file) =>
            file.id === fileId ? { ...file, progress: Math.floor(progress) } : file
          )
        );
      }
    }, UPLOAD_SIMULATION_INTERVAL_MS);
  };

  const getFileType = (mimeType: string): 'video' | 'image' | 'audio' | 'document' => {
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('audio/')) return 'audio';
    return 'document';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + FILE_SIZE_UNITS[i];
  };

  const handleRemoveFile = (id: string) => {
    setMediaFiles((prev) => prev.filter((file) => file.id !== id));
  };

  const handleCreateCase = async () => {
    if (!caseTitle.trim()) return;

    // Calculate overall upload progress
    const totalFiles = mediaFiles.length;
    const completedFiles = mediaFiles.filter((f) => f.status === 'completed').length;
    const overallProgress = totalFiles > 0 ? Math.floor((completedFiles / totalFiles) * 100) : 100;

    await createCase({
      title: caseTitle,
      description: caseDescription,
      mediaCount: totalFiles,
      uploadProgress: overallProgress,
    });

    // Navigate to past cases to see the processing status
    navigate('/past-cases');
  };

  const uploadedCount = mediaFiles.filter((f) => f.status === 'completed').length;
  const totalCount = mediaFiles.length;
  const overallProgress = totalCount > 0 ? Math.floor((uploadedCount / totalCount) * 100) : 0;

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-5xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-black mb-2">Create New Case</h1>
          <p className="text-gray-600">Add case details and upload evidence files to begin investigation</p>
        </div>

        {/* Form */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Case Details Card */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h2 className="font-semibold text-black mb-5">Case Details</h2>
              
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Case Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={caseTitle}
                    onChange={(e) => setCaseTitle(e.target.value)}
                    placeholder="Enter case title"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Description <span className="text-xs text-gray-400 font-normal">(Optional)</span>
                  </label>
                  <textarea
                    value={caseDescription}
                    onChange={(e) => setCaseDescription(e.target.value)}
                    placeholder="Add case notes or description..."
                    rows={4}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all resize-none"
                  />
                </div>
              </div>
            </div>

            {/* Upload Media Card */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h2 className="font-semibold text-black mb-5">Upload Evidence</h2>

              {/* Upload Area */}
              <label className="block">
                <input
                  type="file"
                  multiple
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-black hover:bg-gray-50 transition-all cursor-pointer">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                      <Upload className="w-6 h-6 text-gray-600" strokeWidth={1.5} />
                    </div>
                    <p className="font-medium text-black mb-1">Click to upload or drag and drop</p>
                    <p className="text-sm text-gray-500">Video, Image, Audio, or Document files</p>
                  </div>
                </div>
              </label>

              {/* Uploaded Files List */}
              {mediaFiles.length > 0 && (
                <div className="mt-6 space-y-3">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-black">Uploaded Files ({mediaFiles.length})</h3>
                    {isUploading && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-2 h-2 bg-black rounded-full animate-pulse" />
                        <span>Processing {overallProgress}%</span>
                      </div>
                    )}
                  </div>
                  {mediaFiles.map((file) => (
                    <MediaUploadCard key={file.id} file={file} onRemove={handleRemoveFile} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Summary & Actions */}
          <div className="space-y-6">
            {/* Summary Card */}
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6 sticky top-8">
              <h3 className="font-semibold text-black mb-4">Summary</h3>
              
              <div className="space-y-4 mb-6">
                <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                  <span className="text-sm text-gray-600">Case Title</span>
                  <span className="text-sm font-medium text-black">
                    {caseTitle || <span className="text-gray-400">Not set</span>}
                  </span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                  <span className="text-sm text-gray-600">Evidence Files</span>
                  <span className="text-sm font-medium text-black">{mediaFiles.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Upload Status</span>
                  <span className="text-sm font-medium text-black">
                    {uploadedCount}/{totalCount} Complete
                  </span>
                </div>
              </div>

              {/* Info Boxes */}
              {isUploading && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
                  <div className="flex gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" strokeWidth={2} />
                    <div>
                      <p className="text-sm text-amber-900 font-medium mb-1">Upload in Progress</p>
                      <p className="text-xs text-amber-700 leading-relaxed">
                        You can create the case now. Processing will continue in background.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {!isUploading && mediaFiles.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
                  <div className="flex gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" strokeWidth={2} />
                    <div>
                      <p className="text-sm text-green-900 font-medium mb-1">Ready to Create</p>
                      <p className="text-xs text-green-700 leading-relaxed">
                        All files uploaded successfully. You can now create the case.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Create Button */}
              <button
                onClick={handleCreateCase}
                disabled={!caseTitle.trim()}
                className="w-full bg-black text-white py-3.5 rounded-xl font-medium hover:bg-gray-900 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-black"
              >
                Create Case
              </button>

              <p className="text-xs text-gray-500 text-center mt-3">
                Case will be saved with current upload status
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
