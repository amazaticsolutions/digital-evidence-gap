import { Send, Video, Image as ImageIcon, Mic, ChevronDown, ExternalLink, Play, Camera, Plus, ArrowLeft, Upload, Trash2, FolderOpen, ChevronRight } from 'lucide-react';
import { useParams, useNavigate } from 'react-router';
import { useState, useEffect, useRef } from 'react';
import {
  getMessages,
  getEvidenceFiles,
  deleteEvidenceFile,
  getCaseMeta,
  sendMessage,
  type Message,
  type EvidenceFile,
  type CaseMeta,
} from '../../services/chatWorkspace.service';
import { Modal } from '../components/Modal';
import { VideoPlayer } from '../components/VideoPlayer';
import { ImageViewer } from '../components/ImageViewer';
import { EvidenceList } from '../components/EvidenceList';

export function ChatWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);
  const [caseMeta, setCaseMeta] = useState<CaseMeta | null>(null);
  const [input, setInput] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [showUploadDropdown, setShowUploadDropdown] = useState(false);
  const [showEvidenceList, setShowEvidenceList] = useState(false);
  const [selectedSource, setSelectedSource] = useState<{
    filename: string;
    type: 'video' | 'image' | 'audio';
    url: string;
    cameraId: string;
    timestamp: string;
    date: string;
  } | null>(null);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load messages from service
  useEffect(() => {
    if (!id) return;
    getMessages(id).then((res) => {
      if (res.success) setMessages(res.data);
    });
  }, [id]);

  // Load evidence files from service
  useEffect(() => {
    if (!id) return;
    getEvidenceFiles(id).then((res) => {
      if (res.success) setEvidenceFiles(res.data);
    });
  }, [id]);

  // Load case metadata from service
  useEffect(() => {
    if (!id) return;
    getCaseMeta(id).then((res) => {
      if (res.success) setCaseMeta(res.data);
    });
  }, [id]);

  useEffect(() => {
    // Scroll to the bottom of the messages area when new messages are added
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowUploadDropdown(false);
      }
    };

    if (showUploadDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUploadDropdown]);

  const toggleSources = (messageId: string) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId);
    } else {
      newExpanded.add(messageId);
    }
    setExpandedSources(newExpanded);
  };

  const handleSend = async () => {
    if (!input.trim() || !id) return;
    const content = input.trim();
    setInput('');
    const res = await sendMessage(id, { content });
    if (res.success) {
      setMessages((prev) => [...prev, res.data]);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      console.log('Files uploaded:', files);
      setShowUploadDropdown(false);
    }
  };

  const getCaseTitle = () => caseMeta?.title ?? 'Loading...';
  const getEvidenceCount = () => caseMeta?.evidenceCount ?? '—';

  const handleDeleteEvidence = async (evidenceId: string) => {
    if (!id) return;
    const res = await deleteEvidenceFile(id, evidenceId);
    if (res.success) {
      setEvidenceFiles((prev) => prev.filter((f) => f.id !== evidenceId));
    }
  };

  const getFileTypeFromName = (filename: string): 'video' | 'image' | 'audio' => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext || '')) return 'video';
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext || '')) return 'image';
    if (['mp3', 'wav', 'ogg', 'm4a', 'aac'].includes(ext || '')) return 'audio';
    return 'video'; // default
  };

  const handleSourceClick = (source: { filename: string; cameraId: string; timestamp: string; date: string }) => {
    const type = getFileTypeFromName(source.filename);
    // TODO: Replace with actual file URL from API
    const mockUrl = type === 'video' 
      ? 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
      : 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200';
    
    setSelectedSource({
      ...source,
      type,
      url: mockUrl,
    });
    setShowSourceModal(true);
  };

  const handleEvidenceFileClick = (file: EvidenceFile) => {
    // TODO: Replace with actual file URL from API
    const mockUrl = file.type === 'video' 
      ? 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
      : file.type === 'image'
      ? 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200'
      : 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3';
    
    setSelectedSource({
      filename: file.name,
      cameraId: 'Evidence File',
      timestamp: file.uploadTime,
      date: file.uploadDate,
      type: file.type,
      url: mockUrl,
    });
    setShowSourceModal(true);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="bg-white px-8 py-5 flex-shrink-0 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/past-cases')}
              className="flex items-center justify-center w-10 h-10 bg-gray-50 rounded-xl hover:bg-gray-100 transition-all hover:shadow-md shadow-sm"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" strokeWidth={2} />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-black">{getCaseTitle()}</h1>
              {!showEvidenceList && (
                <button 
                  onClick={() => setShowEvidenceList(!showEvidenceList)}
                  className="flex items-center gap-1.5 mt-1 text-sm text-gray-600 hover:text-black transition-colors group"
                >
                  <FolderOpen className="w-4 h-4 text-gray-500 group-hover:text-black transition-colors" strokeWidth={2} />
                  <span className="font-medium">{getEvidenceCount()} analyzed</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-black transition-all group-hover:translate-x-0.5" strokeWidth={2} />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Content Area - Toggle between Chat and Evidence List */}
      {!showEvidenceList ? (
        /* Messages Area */
        <div className="flex-1 overflow-y-auto px-8 py-6" ref={messagesRef}>
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[75%] ${message.type === 'user' ? 'bg-black text-white shadow-lg' : 'bg-white shadow-md'} rounded-2xl p-5`}>
                  <p className={`leading-relaxed ${message.type === 'user' ? 'text-white' : 'text-black'}`}>
                    {message.content}
                  </p>
                  
                  {message.timestamp && (
                    <p className={`text-xs mt-3 ${message.type === 'user' ? 'text-gray-300' : 'text-gray-500'}`}>
                      {message.timestamp}
                    </p>
                  )}

                  {/* Table Section */}
                  {message.table && (
                    <div className="mt-4 pt-4 border-t border-gray-100 overflow-hidden">
                      <div className="bg-gray-50 rounded-xl overflow-hidden shadow-sm">
                        <table className="w-full border-collapse">
                          <thead className="bg-white">
                            <tr>
                              {message.table.headers.map((header, idx) => (
                                <th key={idx} className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider px-4 py-3">
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-gray-50 divide-y divide-gray-100">
                            {message.table.rows.map((row, idx) => (
                              <tr key={idx} className="hover:bg-white transition-colors">
                                <td className="text-sm text-gray-900 px-4 py-3 whitespace-nowrap">
                                  {row.date}
                                </td>
                                <td className="text-sm text-gray-900 px-4 py-3 whitespace-nowrap font-medium">
                                  {row.time}
                                </td>
                                <td className="text-sm text-gray-700 px-4 py-3 leading-relaxed">
                                  {row.description}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Sources Section */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <button
                        onClick={() => toggleSources(message.id)}
                        className="flex items-center gap-2 text-sm font-medium text-black hover:text-gray-700 transition-colors w-full"
                      >
                        <ExternalLink className="w-4 h-4" strokeWidth={2} />
                        <span>Cite Sources ({message.sources.length})</span>
                        <ChevronDown
                          className={`w-4 h-4 ml-auto transition-transform ${expandedSources.has(message.id) ? 'rotate-180' : ''}`}
                          strokeWidth={2}
                        />
                      </button>

                      {expandedSources.has(message.id) && (
                        <div className="mt-4 space-y-3">
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              onClick={() => handleSourceClick(source)}
                              className="bg-gray-50 rounded-xl p-4 hover:shadow-md transition-all cursor-pointer shadow-sm"
                            >
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 bg-white rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                                  <Play className="w-6 h-6 text-gray-600" strokeWidth={2} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-black mb-2">{source.filename}</p>
                                  <div className="flex items-center gap-3 text-xs text-gray-500">
                                    <div className="flex items-center gap-1.5">
                                      <Camera className="w-3.5 h-3.5" strokeWidth={2} />
                                      <span>{source.cameraId}</span>
                                    </div>
                                    <span>•</span>
                                    <span>{source.date}</span>
                                    <span>•</span>
                                    <span>{source.timestamp}</span>
                                  </div>
                                </div>
                                <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" strokeWidth={2} />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Evidence List Area */
        <EvidenceList
          evidenceFiles={evidenceFiles}
          onBack={() => setShowEvidenceList(false)}
          onDeleteEvidence={handleDeleteEvidence}
          onFileClick={handleEvidenceFileClick}
        />
      )}

      {/* Input Area - Only show in Chat mode */}
      {!showEvidenceList && (
        <div className="bg-white px-8 py-5 flex-shrink-0 shadow-lg">
          <div className="max-w-4xl mx-auto">
            {/* Input Field with Embedded Plus Button and Send */}
            <div className="relative flex items-center gap-3">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask about evidence, request analysis, or search for specific details..."
                  className="w-full pl-5 pr-16 py-3.5 bg-gray-50 rounded-xl focus:outline-none focus:ring-2 focus:ring-black transition-all shadow-md"
                />
                <button
                  onClick={() => setShowUploadDropdown(true)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center w-9 h-9 bg-white text-black rounded-lg hover:bg-gray-100 transition-colors shadow-sm z-10"
                >
                  <Plus className="w-4.5 h-4.5" strokeWidth={2} />
                </button>
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="flex items-center justify-center w-12 h-12 bg-black text-white rounded-xl hover:bg-gray-900 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
              >
                <Send className="w-5 h-5" strokeWidth={2} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Dropdown */}
      {showUploadDropdown && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setShowUploadDropdown(false)} />
          
          {/* Dropdown Menu - Aligned with Plus Button Left Edge */}
          <div className="fixed bottom-[88px] right-[274px] z-50" ref={dropdownRef}>
            <div className="bg-white rounded-xl shadow-2xl w-64 py-1.5">
              <button
                onClick={() => {
                  fileInputRef.current?.click();
                  setShowUploadDropdown(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-black hover:bg-gray-50 transition-colors text-left rounded-lg"
              >
                <Upload className="w-4.5 h-4.5" strokeWidth={2} />
                <span className="text-sm font-medium whitespace-nowrap">Upload from Computer</span>
              </button>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileUpload}
                className="hidden"
                accept="video/*,image/*,audio/*,.pdf,.doc,.docx"
              />
            </div>
          </div>
        </>
      )}

      {/* Source Viewer Modal */}
      <Modal
        isOpen={showSourceModal}
        onClose={() => {
          setShowSourceModal(false);
          setSelectedSource(null);
        }}
        size="full"
      >
        {selectedSource && (
          <div className="space-y-4">
            {/* Source metadata */}
            <div className="bg-gray-50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-black mb-3">
                {selectedSource.filename}
              </h3>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1.5">
                  <Camera className="w-4 h-4" strokeWidth={2} />
                  <span>{selectedSource.cameraId}</span>
                </div>
                <span>•</span>
                <span>{selectedSource.date}</span>
                <span>•</span>
                <span>{selectedSource.timestamp}</span>
              </div>
            </div>

            {/* Viewer */}
            {selectedSource.type === 'video' && (
              <VideoPlayer
                src={selectedSource.url}
                title={selectedSource.filename}
              />
            )}
            {selectedSource.type === 'image' && (
              <ImageViewer
                src={selectedSource.url}
                alt={selectedSource.filename}
                title={selectedSource.filename}
              />
            )}
            {selectedSource.type === 'audio' && (
              <div className="bg-gray-50 rounded-xl p-8 text-center">
                <Mic className="w-16 h-16 text-gray-400 mx-auto mb-4" strokeWidth={2} />
                <p className="text-gray-600 mb-4">Audio player coming soon</p>
                <audio controls className="w-full">
                  <source src={selectedSource.url} />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}