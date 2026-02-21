export interface DemoCase {
  id: string;
  title: string;
  description: string;
  mediaCount: number;
  uploadProgress: number;
  status: 'processing' | 'completed' | 'failed';
  createdAt: string;
}

/** The primary demo case that always appears in the Past Cases list. */
export const DEMO_CASE: DemoCase = {
  id: 'demo-traffic-case',
  title: 'Highway Traffic Analysis - Route 66',
  description: 'Traffic surveillance footage analysis for vehicle tracking',
  mediaCount: 1,
  uploadProgress: 100,
  status: 'completed',
  createdAt: new Date('2026-02-18T09:30:00').toISOString(),
};

/** Additional pre-seeded demo cases for a richer initial demonstration. */
export const ADDITIONAL_DEMO_CASES: DemoCase[] = [
  {
    id: 'demo-parking-case',
    title: 'Parking Lot Incident - Mall Plaza',
    description: 'Security camera footage from parking structure',
    mediaCount: 3,
    uploadProgress: 100,
    status: 'completed',
    createdAt: new Date('2026-02-17T14:20:00').toISOString(),
  },
  {
    id: 'demo-processing-case',
    title: 'Bank Security Review - Downtown Branch',
    description: 'Multi-camera surveillance system analysis',
    mediaCount: 8,
    uploadProgress: 100,
    status: 'completed',
    createdAt: new Date('2026-02-19T16:45:00').toISOString(),
  },
  {
    id: 'demo-warehouse-case',
    title: 'Warehouse Theft Investigation',
    description: 'Internal camera footage and access logs',
    mediaCount: 5,
    uploadProgress: 100,
    status: 'completed',
    createdAt: new Date('2026-02-16T11:10:00').toISOString(),
  },
  {
    id: 'demo-intersection-case',
    title: 'Intersection Vehicle Tracking - Main St & 5th Ave',
    description: 'Vehicle movement analysis at busy intersection',
    mediaCount: 1,
    uploadProgress: 100,
    status: 'completed',
    createdAt: new Date('2026-02-15T08:15:00').toISOString(),
  },
];
