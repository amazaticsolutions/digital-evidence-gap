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
  const [activeTab, setActiveTab] = useState<'videos' | 'images' | 'audios'>('videos');
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

  const handleDeleteEvidence = async (evidenceId: string) => {
    if (!id) return;
    const res = await deleteEvidenceFile(id, evidenceId);
    if (res.success) {
      setEvidenceFiles((prev) => prev.filter((f) => f.id !== evidenceId));
    }
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
        <div className="flex-1 overflow-y-auto px-8 py-6 bg-gray-50">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Back Button and Tabs - Single Row */}
            <div className="flex items-center justify-between">
              {/* Back Button - Left Side */}
              <button
                onClick={() => setShowEvidenceList(false)}
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
                            handleDeleteEvidence(file.id);
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
    </div>
  );
}