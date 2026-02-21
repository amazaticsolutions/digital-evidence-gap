import { Send, Video, Image as ImageIcon, Mic, ChevronDown, ExternalLink, Play, Camera, Paperclip, Plus, ArrowLeft, X, Upload, Trash2, FolderOpen, ChevronRight } from 'lucide-react';
import { useParams, useNavigate } from 'react-router';
import { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp?: string;
  table?: {
    headers: string[];
    rows: Array<{
      date: string;
      time: string;
      description: string;
    }>;
  };
  sources?: Array<{
    filename: string;
    cameraId: string;
    timestamp: string;
    date: string;
  }>;
}

interface EvidenceFile {
  id: string;
  name: string;
  type: 'video' | 'image' | 'audio';
  uploadDate: string;
  uploadTime: string;
  thumbnail?: string;
}

const demoTrafficMessages: Message[] = [
  {
    id: '1',
    type: 'ai',
    content: 'Hello, I\'m your AI Evidence Assistant. I\'ve analyzed the uploaded traffic surveillance video (Highway_Route66_Feb18.mp4). The video spans 4 hours of footage from February 18, 2026. Ask me anything about the traffic patterns, vehicle movements, or specific incidents.',
    timestamp: '9:32 AM',
  },
  {
    id: '2',
    type: 'user',
    content: 'Please give me the time when car has been passed on the road',
    timestamp: '9:35 AM',
  },
  {
    id: '3',
    type: 'ai',
    content: 'I\'ve analyzed the video footage and detected 3 instances where a black sedan (License plate: ABC-1234) passed through the monitored section of Route 66. Here are the details with exact timestamps:\n\n**First Pass:**\nDate: February 18, 2026\nTime: 10:24:18 AM\nDescription: Black sedan traveling eastbound at approximately 55 mph. Vehicle enters frame from west, passes through monitoring zone, and exits on the east side. Weather conditions: Clear, good visibility.\n\n**Second Pass:**\nDate: February 18, 2026\nTime: 12:47:52 PM\nDescription: Same black sedan returning westbound at approximately 52 mph. Driver visible in footage. Vehicle appears to slow down near mile marker 142 before continuing.\n\n**Third Pass:**\nDate: February 18, 2026  \nTime: 2:15:33 PM\nDescription: Black sedan traveling eastbound again at approximately 58 mph. Vehicle maintains consistent speed throughout the frame. No stops or unusual behavior detected.\n\nAll three passes have been verified with clear license plate visibility and consistent vehicle identification markers.',
    timestamp: '9:35 AM',
    sources: [
      {
        filename: 'Highway_Route66_Feb18.mp4',
        cameraId: 'CAM-HWY-66-E',
        timestamp: '10:24:18',
        date: 'Feb 18, 2026',
      },
      {
        filename: 'Highway_Route66_Feb18.mp4',
        cameraId: 'CAM-HWY-66-E',
        timestamp: '12:47:52',
        date: 'Feb 18, 2026',
      },
      {
        filename: 'Highway_Route66_Feb18.mp4',
        cameraId: 'CAM-HWY-66-E',
        timestamp: '02:15:33',
        date: 'Feb 18, 2026',
      },
    ],
  },
];

const demoIntersectionMessages: Message[] = [
  {
    id: '1',
    type: 'ai',
    content: 'Hello, I\'m your AI Evidence Assistant. I\'ve analyzed the uploaded intersection surveillance video (Intersection_MainSt_5thAve_Feb15.mp4). The video contains 6 hours of continuous footage from February 15, 2026. How can I assist with your investigation?',
    timestamp: '10:15 AM',
  },
  {
    id: '2',
    type: 'user',
    content: 'Please give me the time when car has been passed on the road',
    timestamp: '10:18 AM',
  },
  {
    id: '3',
    type: 'ai',
    content: 'I\'ve detected 3 instances of the silver SUV (License plate: XYZ-7890) passing through the Main St & 5th Ave intersection. Below is a detailed table with timestamps and descriptions:',
    timestamp: '10:18 AM',
    table: {
      headers: ['Date', 'Time', 'Description'],
      rows: [
        {
          date: 'February 15, 2026',
          time: '11:05:23 AM',
          description: 'Silver SUV traveling northbound at approximately 45 mph. Vehicle enters frame from west, passes through monitoring zone, and exits on the east side. Weather conditions: Clear, good visibility.',
        },
        {
          date: 'February 15, 2026',
          time: '1:32:45 PM',
          description: 'Same silver SUV returning southbound at approximately 40 mph. Driver visible in footage. Vehicle appears to slow down near the intersection before continuing.',
        },
        {
          date: 'February 15, 2026',
          time: '3:10:12 PM',
          description: 'Silver SUV traveling northbound again at approximately 48 mph. Vehicle maintains consistent speed throughout the frame. No stops or unusual behavior detected.',
        },
      ],
    },
    sources: [
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '11:05:23',
        date: 'Feb 15, 2026',
      },
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '13:32:45',
        date: 'Feb 15, 2026',
      },
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '15:10:12',
        date: 'Feb 15, 2026',
      },
    ],
  },
  {
    id: '4',
    type: 'user',
    content: 'please tell for how much time car has passed from this road',
    timestamp: '10:22 AM',
  },
  {
    id: '5',
    type: 'ai',
    content: 'Based on the video analysis, I\'ve calculated the duration the silver SUV spent in the camera\'s field of view during each pass. Here\'s the detailed breakdown:',
    timestamp: '10:22 AM',
    table: {
      headers: ['Date', 'Time', 'Duration in Frame'],
      rows: [
        {
          date: 'February 15, 2026',
          time: '11:05:23 AM',
          description: '8.4 seconds - Vehicle maintained steady speed throughout the monitored zone.',
        },
        {
          date: 'February 15, 2026',
          time: '1:32:45 PM',
          description: '12.7 seconds - Vehicle slowed down mid-frame, increasing time in view.',
        },
        {
          date: 'February 15, 2026',
          time: '3:10:12 PM',
          description: '7.9 seconds - Fastest pass with consistent speed maintained.',
        },
      ],
    },
    sources: [
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '11:05:23',
        date: 'Feb 15, 2026',
      },
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '13:32:45',
        date: 'Feb 15, 2026',
      },
      {
        filename: 'Intersection_MainSt_5thAve_Feb15.mp4',
        cameraId: 'CAM-INT-MS-5A',
        timestamp: '15:10:12',
        date: 'Feb 15, 2026',
      },
    ],
  },
];

const defaultMessages: Message[] = [
  {
    id: '1',
    type: 'ai',
    content: 'Hello, I\'m your AI Evidence Assistant. I\'ve analyzed all uploaded evidence files. Ask me anything about the case.',
    timestamp: '2:34 PM',
  },
  {
    id: '2',
    type: 'user',
    content: 'What happened between 3:15 PM and 3:30 PM on February 14th?',
    timestamp: '2:35 PM',
  },
  {
    id: '3',
    type: 'ai',
    content: 'Based on the evidence, at 3:18 PM, a black sedan was observed entering the parking lot from the north entrance. At 3:22 PM, two individuals exited the vehicle and approached the building entrance. The security camera footage shows clear visibility of both subjects.',
    timestamp: '2:35 PM',
    sources: [
      {
        filename: 'NorthCam_021426_1518.mp4',
        cameraId: 'CAM-N-01',
        timestamp: '15:18:34',
        date: 'Feb 14, 2026',
      },
      {
        filename: 'EntranceCam_021426_1522.mp4',
        cameraId: 'CAM-E-03',
        timestamp: '15:22:11',
        date: 'Feb 14, 2026',
      },
    ],
  },
];

// Mock Evidence Data
const mockEvidenceFiles: EvidenceFile[] = [
  // Videos - Today
  { id: 'v1', name: 'Parking_Lot_NorthCam.mp4', type: 'video', uploadDate: 'February 21, 2026', uploadTime: '09:15 AM' },
  { id: 'v2', name: 'Entrance_MainDoor_021426.mp4', type: 'video', uploadDate: 'February 21, 2026', uploadTime: '09:18 AM' },
  { id: 'v3', name: 'Highway_Route66_Feb18.mp4', type: 'video', uploadDate: 'February 21, 2026', uploadTime: '09:22 AM' },
  
  // Videos - Yesterday
  { id: 'v4', name: 'BackAlley_Camera3_021426.mp4', type: 'video', uploadDate: 'February 20, 2026', uploadTime: '02:45 PM' },
  { id: 'v5', name: 'Intersection_MainSt_5thAve.mp4', type: 'video', uploadDate: 'February 20, 2026', uploadTime: '03:12 PM' },
  { id: 'v6', name: 'SideEntrance_021426_1800.mp4', type: 'video', uploadDate: 'February 20, 2026', uploadTime: '04:30 PM' },
  
  // Videos - Feb 19
  { id: 'v7', name: 'StoreFront_021926_Morning.mp4', type: 'video', uploadDate: 'February 19, 2026', uploadTime: '10:00 AM' },
  { id: 'v8', name: 'LoadingDock_021926.mp4', type: 'video', uploadDate: 'February 19, 2026', uploadTime: '11:20 AM' },
  
  // Images - Today
  { id: 'i1', name: 'License_Plate_ABC1234.jpg', type: 'image', uploadDate: 'February 21, 2026', uploadTime: '08:30 AM' },
  { id: 'i2', name: 'Suspect_Profile_Front.jpg', type: 'image', uploadDate: 'February 21, 2026', uploadTime: '08:35 AM' },
  { id: 'i3', name: 'Vehicle_Damage_RearBumper.jpg', type: 'image', uploadDate: 'February 21, 2026', uploadTime: '08:40 AM' },
  { id: 'i4', name: 'Crime_Scene_Overview.jpg', type: 'image', uploadDate: 'February 21, 2026', uploadTime: '09:00 AM' },
  
  // Images - Yesterday
  { id: 'i5', name: 'Evidence_Tag_47A.jpg', type: 'image', uploadDate: 'February 20, 2026', uploadTime: '01:15 PM' },
  { id: 'i6', name: 'Footprint_Analysis.jpg', type: 'image', uploadDate: 'February 20, 2026', uploadTime: '01:45 PM' },
  { id: 'i7', name: 'Fingerprint_Door_Handle.jpg', type: 'image', uploadDate: 'February 20, 2026', uploadTime: '02:00 PM' },
  { id: 'i8', name: 'Broken_Window_Glass.jpg', type: 'image', uploadDate: 'February 20, 2026', uploadTime: '02:30 PM' },
  
  // Images - Feb 19
  { id: 'i9', name: 'Witness_Statement_Photo1.jpg', type: 'image', uploadDate: 'February 19, 2026', uploadTime: '03:00 PM' },
  { id: 'i10', name: 'Security_Badge_Found.jpg', type: 'image', uploadDate: 'February 19, 2026', uploadTime: '03:30 PM' },
  
  // Audios - Today
  { id: 'a1', name: '911_Call_Recording_021426.mp3', type: 'audio', uploadDate: 'February 21, 2026', uploadTime: '10:00 AM' },
  { id: 'a2', name: 'Witness_Interview_Subject_A.mp3', type: 'audio', uploadDate: 'February 21, 2026', uploadTime: '10:30 AM' },
  
  // Audios - Yesterday
  { id: 'a3', name: 'Detective_Notes_Recording.mp3', type: 'audio', uploadDate: 'February 20, 2026', uploadTime: '11:00 AM' },
  { id: 'a4', name: 'Suspect_Interrogation_Part1.mp3', type: 'audio', uploadDate: 'February 20, 2026', uploadTime: '02:15 PM' },
  { id: 'a5', name: 'Suspect_Interrogation_Part2.mp3', type: 'audio', uploadDate: 'February 20, 2026', uploadTime: '02:45 PM' },
  
  // Audios - Feb 19
  { id: 'a6', name: 'Voicemail_Evidence_021926.mp3', type: 'audio', uploadDate: 'February 19, 2026', uploadTime: '09:30 AM' },
  { id: 'a7', name: 'Traffic_Radio_Dispatch.mp3', type: 'audio', uploadDate: 'February 19, 2026', uploadTime: '10:15 AM' },
];

export function ChatWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [showUploadDropdown, setShowUploadDropdown] = useState(false);
  const [showEvidenceList, setShowEvidenceList] = useState(false);
  const [activeTab, setActiveTab] = useState<'videos' | 'images' | 'audios'>('videos');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load appropriate messages based on case ID
    if (id === 'demo-traffic-case') {
      setMessages(demoTrafficMessages);
    } else if (id === 'demo-intersection-case') {
      setMessages(demoIntersectionMessages);
    } else {
      setMessages(defaultMessages);
    }
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

  const handleSend = () => {
    if (input.trim()) {
      setInput('');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      console.log('Files uploaded:', files);
      setShowUploadDropdown(false);
    }
  };

  const getCaseTitle = () => {
    if (id === 'demo-traffic-case') {
      return 'Highway Traffic Analysis - Route 66';
    } else if (id === 'demo-intersection-case') {
      return 'Intersection Surveillance - Main St & 5th Ave';
    }
    return 'State v. Anderson - Robbery Investigation';
  };

  const getEvidenceCount = () => {
    if (id === 'demo-traffic-case') {
      return '1 video file';
    } else if (id === 'demo-intersection-case') {
      return '1 video file';
    }
    return '47 evidence files';
  };

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
    return mockEvidenceFiles.filter(file => {
      if (activeTab === 'videos') return file.type === 'video';
      if (activeTab === 'images') return file.type === 'image';
      if (activeTab === 'audios') return file.type === 'audio';
      return false;
    });
  };

  const handleDeleteEvidence = (evidenceId: string) => {
    console.log('Delete evidence:', evidenceId);
    // In a real app, this would delete from state/database
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