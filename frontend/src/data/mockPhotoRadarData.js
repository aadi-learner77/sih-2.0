/**
 * Mock Photo Radar Clusters & Pair Comparisons Data:
 * Provides structured nodes, edges, and rich forensic metadata for cross-institutional photo reuse.
 */

export const MOCK_RADAR_PAIRS = [
  {
    id: 'PAIR-LAB-001',
    category: 'Computer Laboratory',
    title: 'Computer Center & AI Workstations Re-use',
    severity: 'CRITICAL',
    ai_wording: 'Indicator for review: Cross-institutional photo reuse detected across 2 institutions',
    similarity_score: 98.4,
    hamming_distance: 1,
    clip_cosine: 0.942,
    match_type: 'Near-Duplicate',
    difference_summary: 'Same computer laboratory photo reused with 3.2% crop and +8% warmer color temperature shift.',
    
    // Original Photo (Historical Submission)
    original_photo: {
      institution_id: 'INST_002',
      institution_name: 'Royal College of Engineering',
      city: 'Mysuru, Karnataka',
      application_no: 'APP-2024-ENG-1102',
      academic_year: '2024-25',
      facility_name: 'Computer Center Lab A (60 Systems)',
      submission_date: '2024-06-12',
      file_name: 'computer_lab_original.jpg',
      image_url: '/images/computer_lab_original.jpg',
      phash: 'a8f0c3d2e1b4a5f6',
      resolution: '1920 x 1080',
      ela_score: 0.22,
      ela_status: 'CLEAN',
    },

    // Near-Duplicate Photo (Current Submission)
    duplicate_photo: {
      institution_id: 'INST_001',
      institution_name: 'Apex Institute of Technology & Science',
      city: 'Bengaluru, Karnataka',
      application_no: 'APP-2025-09812',
      academic_year: '2025-26',
      facility_name: 'High Performance AI Computing Lab',
      submission_date: '2025-10-18',
      file_name: 'computer_lab_reused.jpg',
      image_url: '/images/computer_lab_reused.jpg',
      phash: 'a8f0c3d2e1b4a5f7',
      resolution: '1920 x 1080 (Cropped 3.2%)',
      ela_score: 0.68,
      ela_status: 'SUSPICIOUS_COMPRESSION',
    },
  },

  {
    id: 'PAIR-CHEM-002',
    category: 'Chemistry / Materials Lab',
    title: 'Chemistry & Environmental Analysis Laboratory',
    severity: 'CRITICAL',
    ai_wording: 'Indicator for review: Concurrent identical laboratory imagery submitted in same cycle',
    similarity_score: 96.2,
    hamming_distance: 2,
    clip_cosine: 0.915,
    match_type: 'Near-Duplicate',
    difference_summary: 'Identical fume hood and workbench setup with cropped foreground apparatus and altered aspect ratio.',

    original_photo: {
      institution_id: 'INST_005',
      institution_name: 'Vanguard Institute of Technology',
      city: 'Hyderabad, Telangana',
      application_no: 'APP-2025-ENG-4491',
      academic_year: '2025-26',
      facility_name: 'Central Chemical Sciences Research Facility',
      submission_date: '2025-09-02',
      file_name: 'chemistry_lab_photo.jpg',
      image_url: '/images/chemistry_lab_photo.jpg',
      phash: '9e2c4f6a8b0c2e4d',
      resolution: '1600 x 1200',
      ela_score: 0.28,
      ela_status: 'CLEAN',
    },

    duplicate_photo: {
      institution_id: 'INST_004',
      institution_name: 'Greenfield Polytechnic & Research',
      city: 'Belagavi, Karnataka',
      application_no: 'APP-2025-POLY-8190',
      academic_year: '2025-26',
      facility_name: 'Applied Chemistry & Polymer Science Lab',
      submission_date: '2025-10-14',
      file_name: 'chemistry_lab_photo.jpg',
      image_url: '/images/chemistry_lab_photo.jpg',
      phash: '9e2c4f6a8b0c2e4f',
      resolution: '1600 x 1200 (Identical Hash)',
      ela_score: 0.31,
      ela_status: 'CLEAN',
    },
  },

  {
    id: 'PAIR-ROBOTICS-003',
    category: 'Robotics & Automation',
    title: 'Robotics & Mechatronics Fabrication Facility',
    severity: 'WARNING',
    ai_wording: 'Indicator for review: Semantic similarity threshold exceeded on specialized lab equipment',
    similarity_score: 89.8,
    hamming_distance: 5,
    clip_cosine: 0.884,
    match_type: 'Semantically Similar',
    difference_summary: 'Robotics arm assembly with overlapping background equipment; distinct angle of capture.',

    original_photo: {
      institution_id: 'INST_001',
      institution_name: 'Apex Institute of Technology & Science',
      city: 'Bengaluru, Karnataka',
      application_no: 'APP-2025-09812',
      academic_year: '2025-26',
      facility_name: 'Mechatronics & Robotics Cell',
      submission_date: '2025-10-18',
      file_name: 'robotics_lab_apex.jpg',
      image_url: '/images/computer_lab_original.jpg', // Visual fallback
      phash: 'f1e2d3c4b5a69788',
      resolution: '1920 x 1080',
      ela_score: 0.25,
      ela_status: 'CLEAN',
    },

    duplicate_photo: {
      institution_id: 'INST_003',
      institution_name: 'Zenith Institute of Technology',
      city: 'Pune, Maharashtra',
      application_no: 'APP-2025-MAH-3012',
      academic_year: '2025-26',
      facility_name: 'Automated Manufacturing Lab',
      submission_date: '2025-08-25',
      file_name: 'robotics_lab_zenith.jpg',
      image_url: '/images/computer_lab_reused.jpg', // Visual fallback
      phash: 'f1e2d3c4b5a6978d',
      resolution: '1920 x 1080',
      ela_score: 0.34,
      ela_status: 'CLEAN',
    },
  },
];

/**
 * Cluster Graph Model for vis-network:
 * Institutions are NODES, and shared photos are EDGES.
 */
export const MOCK_RADAR_GRAPH = {
  nodes: [
    {
      id: 'INST_001',
      label: 'Apex Institute of Tech\n(Bengaluru, KA)',
      title: 'Apex Institute of Technology & Science\nApplication: APP-2025-09812\nFlags: 2 Shared Photos',
      group: 'target_institution',
      shape: 'box',
      color: { background: '#0284c7', border: '#0369a1' },
      size: 28,
    },
    {
      id: 'INST_002',
      label: 'Royal College of Engg\n(Mysuru, KA)',
      title: 'Royal College of Engineering\nApplication: APP-2024-ENG-1102\nFlags: 1 Shared Photo',
      group: 'matched_institution',
      shape: 'box',
      color: { background: '#e11d48', border: '#be123c' },
      size: 26,
    },
    {
      id: 'INST_003',
      label: 'Zenith Institute\n(Pune, MH)',
      title: 'Zenith Institute of Technology\nApplication: APP-2025-MAH-3012\nFlags: 1 Shared Photo',
      group: 'matched_institution',
      shape: 'box',
      color: { background: '#d97706', border: '#b45309' },
      size: 24,
    },
    {
      id: 'INST_004',
      label: 'Greenfield Polytechnic\n(Belagavi, KA)',
      title: 'Greenfield Polytechnic & Research\nApplication: APP-2025-POLY-8190\nFlags: 1 Shared Photo',
      group: 'cluster_b',
      shape: 'box',
      color: { background: '#7c3aed', border: '#6d28d9' },
      size: 25,
    },
    {
      id: 'INST_005',
      label: 'Vanguard Institute\n(Hyderabad, TS)',
      title: 'Vanguard Institute of Technology\nApplication: APP-2025-ENG-4491\nFlags: 1 Shared Photo',
      group: 'cluster_b',
      shape: 'box',
      color: { background: '#7c3aed', border: '#6d28d9' },
      size: 25,
    },
    {
      id: 'INST_006',
      label: 'National Design Institute\n(Bengaluru, KA)',
      title: 'National Institute of Design & Tech\nApplication: APP-2025-KA-0012\nFlags: Clean',
      group: 'unlinked_clean',
      shape: 'box',
      color: { background: '#10b981', border: '#059669' },
      size: 20,
    },
  ],

  edges: [
    {
      id: 'EDGE_LAB_001',
      from: 'INST_001',
      to: 'INST_002',
      label: 'Computer Lab A\n(98.4% Match)',
      pairId: 'PAIR-LAB-001',
      color: { color: '#e11d48', highlight: '#f43f5e' },
      width: 3.5,
      dashes: false,
    },
    {
      id: 'EDGE_CHEM_002',
      from: 'INST_004',
      to: 'INST_005',
      label: 'Chemistry Lab\n(96.2% Match)',
      pairId: 'PAIR-CHEM-002',
      color: { color: '#7c3aed', highlight: '#a855f7' },
      width: 3.0,
      dashes: false,
    },
    {
      id: 'EDGE_ROBOTICS_003',
      from: 'INST_001',
      to: 'INST_003',
      label: 'Robotics Facility\n(89.8% Match)',
      pairId: 'PAIR-ROBOTICS-003',
      color: { color: '#d97706', highlight: '#f59e0b' },
      width: 2.2,
      dashes: true,
    },
  ],
};

/**
 * Data for live Demo "Simulate Upload":
 * When officer triggers simulated upload, a new photo upload from an applicant is processed.
 */
export const SIMULATED_UPLOAD_PAYLOAD = {
  institution_id: 'INST_007',
  institution_name: 'Metro Institute of Technology (New Applicant)',
  city: 'Chennai, Tamil Nadu',
  application_no: 'APP-2025-TN-9988',
  photo_name: 'Newly_Uploaded_Computer_Lab.jpg',
  category: 'Computer Laboratory',
  image_url: '/images/computer_lab_reused.jpg',
  phash: 'a8f0c3d2e1b4a5f6',
  match_target_inst: 'INST_002', // Matches Royal College
  similarity_score: 99.1,
  hamming_distance: 0,
  match_type: 'Exact Hash Duplicate',
};
