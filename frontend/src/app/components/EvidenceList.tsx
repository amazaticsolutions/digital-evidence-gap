import { Video, Image as ImageIcon, Mic, ArrowLeft, Trash2 } from 'lucide-react';
import { useState } from 'react';

export interface EvidenceFile {
  id: string;
  name: string;
  type: 'video' | 'image' | 'audio';
  uploadDate: string;
  uploadTime: string;
  thumbnail?: string;
}

interface EvidenceListProps {
  evidenceFiles: EvidenceFile[];
  onBack: () => void;
  onDeleteEvidence: (evidenceId: string) => void;
  onFileClick?: (file: EvidenceFile) => void;
}

export function EvidenceList({ evidenceFiles, onBack, onDeleteEvidence, onFileClick }: EvidenceListProps) {
  const [activeTab, setActiveTab] = useState<'videos' | 'images' | 'audios'>('videos');

  // Group evidence by date
  const groupEvidenceByDate = (files: EvidenceFile[]) => {
    const grouped: { [key: string]: EvidenceFile[] } = {};
    files.forEach(file => {
      if (!grouped[file.uploadDate]) {
        grouped[file.uploadDate] = [];
      }
      grouped[file.uploadDate].push(file);
    });
    return grouped;
  };

  // Filter evidence by active tab
  const getFilteredEvidence = () => {
    return evidenceFiles.filter(file => {
      if (activeTab === 'videos') return file.type === 'video';
      if (activeTab === 'images') return file.type === 'image';
      if (activeTab === 'audios') return file.type === 'audio';
      return false;
    });
  };

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6 bg-gray-50">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Back Button and Tabs - Single Row */}
        <div className="flex items-center justify-between">
          {/* Back Button - Left Side */}
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-black transition-colors"
          >
            <ArrowLeft className="w-4 h-4" strokeWidth={2} />
            <span className="font-medium">Back to Chat</span>
          </button>

          {/* Tabs - Right Side */}
          <div className="bg-white rounded-xl p-1.5 inline-flex gap-1 shadow-md">
            <button
              onClick={() => setActiveTab('videos')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'videos' 
                  ? 'bg-black text-white shadow-md' 
                  : 'bg-transparent text-gray-600 hover:bg-gray-50 hover:text-black'
              }`}
            >
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4" strokeWidth={2} />
                <span>Videos</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('images')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'images' 
                  ? 'bg-black text-white shadow-md' 
                  : 'bg-transparent text-gray-600 hover:bg-gray-50 hover:text-black'
              }`}
            >
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4" strokeWidth={2} />
                <span>Images</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('audios')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'audios' 
                  ? 'bg-black text-white shadow-md' 
                  : 'bg-transparent text-gray-600 hover:bg-gray-50 hover:text-black'
              }`}
            >
              <div className="flex items-center gap-2">
                <Mic className="w-4 h-4" strokeWidth={2} />
                <span>Audios</span>
              </div>
            </button>
          </div>
        </div>

        {/* Evidence Files */}
        <div className="space-y-4">
          {Object.entries(groupEvidenceByDate(getFilteredEvidence())).map(([date, files]) => (
            <div key={date} className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">{date}</h3>
              {files.map(file => (
                <div
                  key={file.id}
                  onClick={() => onFileClick?.(file)}
                  className="bg-white rounded-xl p-4 hover:shadow-lg transition-all cursor-pointer shadow-md"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                      {file.type === 'video' && <Video className="w-6 h-6 text-gray-600" strokeWidth={2} />}
                      {file.type === 'image' && <ImageIcon className="w-6 h-6 text-gray-600" strokeWidth={2} />}
                      {file.type === 'audio' && <Mic className="w-6 h-6 text-gray-600" strokeWidth={2} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-black mb-2">{file.name}</p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>{file.uploadTime}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteEvidence(file.id);
                      }}
                      className="p-2 hover:bg-gray-50 rounded-lg transition-colors group"
                    >
                      <Trash2 className="w-4.5 h-4.5 text-gray-400 group-hover:text-red-600 transition-colors" strokeWidth={2} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
