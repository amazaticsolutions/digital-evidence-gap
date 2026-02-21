// ─── Types ───────────────────────────────────────────────────────────────────

export interface Message {
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

export interface EvidenceFile {
  id: string;
  name: string;
  type: 'video' | 'image' | 'audio';
  uploadDate: string;
  uploadTime: string;
  thumbnail?: string;
}

// ─── Demo Messages ─────────────────────────────────────────────────────────

export const DEMO_TRAFFIC_MESSAGES: Message[] = [
  {
    id: '1',
    type: 'ai',
    content:
      "Hello, I'm your AI Evidence Assistant. I've analyzed the uploaded traffic surveillance video (Highway_Route66_Feb18.mp4). The video spans 4 hours of footage from February 18, 2026. Ask me anything about the traffic patterns, vehicle movements, or specific incidents.",
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
    content:
      "I've analyzed the video footage and detected 3 instances where a black sedan (License plate: ABC-1234) passed through the monitored section of Route 66. Here are the details with exact timestamps:\n\n**First Pass:**\nDate: February 18, 2026\nTime: 10:24:18 AM\nDescription: Black sedan traveling eastbound at approximately 55 mph. Vehicle enters frame from west, passes through monitoring zone, and exits on the east side. Weather conditions: Clear, good visibility.\n\n**Second Pass:**\nDate: February 18, 2026\nTime: 12:47:52 PM\nDescription: Same black sedan returning westbound at approximately 52 mph. Driver visible in footage. Vehicle appears to slow down near mile marker 142 before continuing.\n\n**Third Pass:**\nDate: February 18, 2026  \nTime: 2:15:33 PM\nDescription: Black sedan traveling eastbound again at approximately 58 mph. Vehicle maintains consistent speed throughout the frame. No stops or unusual behavior detected.\n\nAll three passes have been verified with clear license plate visibility and consistent vehicle identification markers.",
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

export const DEMO_INTERSECTION_MESSAGES: Message[] = [
  {
    id: '1',
    type: 'ai',
    content:
      "Hello, I'm your AI Evidence Assistant. I've analyzed the uploaded intersection surveillance video (Intersection_MainSt_5thAve_Feb15.mp4). The video contains 6 hours of continuous footage from February 15, 2026. How can I assist with your investigation?",
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
    content:
      "I've detected 3 instances of the silver SUV (License plate: XYZ-7890) passing through the Main St & 5th Ave intersection. Below is a detailed table with timestamps and descriptions:",
    timestamp: '10:18 AM',
    table: {
      headers: ['Date', 'Time', 'Description'],
      rows: [
        {
          date: 'February 15, 2026',
          time: '11:05:23 AM',
          description:
            'Silver SUV traveling northbound at approximately 45 mph. Vehicle enters frame from west, passes through monitoring zone, and exits on the east side. Weather conditions: Clear, good visibility.',
        },
        {
          date: 'February 15, 2026',
          time: '1:32:45 PM',
          description:
            'Same silver SUV returning southbound at approximately 40 mph. Driver visible in footage. Vehicle appears to slow down near the intersection before continuing.',
        },
        {
          date: 'February 15, 2026',
          time: '3:10:12 PM',
          description:
            'Silver SUV traveling northbound again at approximately 48 mph. Vehicle maintains consistent speed throughout the frame. No stops or unusual behavior detected.',
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
    content:
      "Based on the video analysis, I've calculated the duration the silver SUV spent in the camera's field of view during each pass. Here's the detailed breakdown:",
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

export const DEFAULT_MESSAGES: Message[] = [
  {
    id: '1',
    type: 'ai',
    content:
      "Hello, I'm your AI Evidence Assistant. I've analyzed all uploaded evidence files. Ask me anything about the case.",
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
    content:
      'Based on the evidence, at 3:18 PM, a black sedan was observed entering the parking lot from the north entrance. At 3:22 PM, two individuals exited the vehicle and approached the building entrance. The security camera footage shows clear visibility of both subjects.',
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

// ─── Mock Evidence Files ───────────────────────────────────────────────────

export const MOCK_EVIDENCE_FILES: EvidenceFile[] = [
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

// ─── Case ID → Title & Evidence Count Map ─────────────────────────────────

export const CASE_META: Record<string, { title: string; evidenceCount: string }> = {
  'demo-traffic-case': {
    title: 'Highway Traffic Analysis - Route 66',
    evidenceCount: '1 video file',
  },
  'demo-intersection-case': {
    title: 'Intersection Surveillance - Main St & 5th Ave',
    evidenceCount: '1 video file',
  },
};

export const DEFAULT_CASE_META = {
  title: 'State v. Anderson - Robbery Investigation',
  evidenceCount: '47 evidence files',
};
