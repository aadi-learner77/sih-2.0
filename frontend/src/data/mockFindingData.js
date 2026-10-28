/**
 * Mock Findings & Evidence Lens Data:
 * Provides rich single-finding dossiers complete with:
 * - Document page preview & bounding box coordinates
 * - 6-Stage Pipeline facts (Claim, Evidence, Rule citation, Source response, AI confidence, Officer action)
 * - Mandatory wording: "Indicator for review"
 * - Graph conflict subgraphs for vis-network
 */

export const MOCK_FINDINGS = [
  {
    id: 'FINDING-DOC-001',
    finding_type: 'DOCUMENT',
    title: 'Statutory Fire Safety Certificate Validity Period',
    clause_id: 'APH 2025-26 Clause 2.14.3',
    clause_title: 'Mandatory Building & Fire Safety NOC Compliance',
    severity: 'CRITICAL',
    ai_wording: 'Indicator for review: Document validity period discrepancy detected',
    application_no: 'APP-2025-09812',
    institution_name: 'Apex Institute of Technology & Science',
    category: 'Extension of Approval (EoA)',

    // Left Column: Document Viewer Specs
    document: {
      filename: 'Karnataka_Fire_Safety_Certificate_2025.pdf',
      document_type: 'Fire Safety Certificate',
      issue_date: '2024-06-15',
      valid_till: '2025-06-14',
      file_hash: '7a9c8b3e1f4d2a6b8e0c3f5a7d9e1b2c4f6a8b0c2e4d6f8a0b2c4e6f8a0b2c4e',
      page_number: 1,
      total_pages: 3,
      preview_url: null, // SVG rendered
      extracted_field: {
        field_name: 'valid_till',
        field_label: 'Validity Expiration Date',
        raw_text: 'Valid up to: 14/06/2025 for academic premises block A & B',
        normalized_value: '2025-06-14',
        ocr_confidence: 0.978,
        // Bounding box percentages for relative positioning
        bounding_box: {
          x: 24, // 24% from left
          y: 44, // 44% from top
          width: 52, // 52% width
          height: 6.5, // 6.5% height
          pixel_x: 180,
          pixel_y: 340,
          pixel_w: 390,
          pixel_h: 48,
        },
      },
      forensics: {
        ela_score: 0.32,
        ela_status: 'CLEAN',
        producer: 'Acrobat PDF Library 15.0 (Authentic)',
        creation_date: '2024-06-15T10:14:00Z',
      },
    },

    // Center Column: 6-Stage Pipeline Strip
    pipeline: {
      claim: {
        stage: 1,
        title: 'Institutional Declaration',
        declared_value: 'Valid till 30-June-2026',
        declared_field: 'valid_till',
        submission_timestamp: '2026-10-18T09:30:00 UTC',
        institution_note: 'Claimed 2-year statutory validity under Karnataka Fire Safety Rules Section 13.',
      },
      evidence: {
        stage: 2,
        title: 'OCR Text & Bounding Box Extraction',
        extracted_text: 'Valid up to: 14/06/2025',
        normalized_value: '2025-06-14',
        field_name: 'valid_till',
        ocr_engine: 'PaddleOCR v3.0 Multi-Modal',
        ocr_confidence: 0.978,
        sha256: '7a9c8b3e1f4d2a6b8e0c3f5a7d9e...',
      },
      rule: {
        stage: 3,
        title: 'Regulation-as-Code Rule Citation',
        handbook_edition: 'AICTE Approval Process Handbook (APH) 2025-26',
        clause_id: 'APH-CH2-Clause-2.14.3',
        clause_citation: 'Clause 2.14.3 (Chapter II) - Fire and Life Safety Standards',
        statutory_norm: 'NOC must remain unexpired and active throughout the academic session 2025-26.',
        compliance_status: 'DEFICIENT (EXPIRED)',
      },
      source_response: {
        stage: 4,
        title: 'State Fire Authority Portal API Lookup',
        issuer_name: 'Karnataka State Fire & Emergency Services Portal',
        query_ref: 'FIR/KA/2024/99102',
        status: 'mismatch_detected',
        latency_ms: 184,
        response_payload: {
          reference_no: 'FIR/KA/2024/99102',
          institution_name: 'Apex Institute of Technology',
          issue_date: '2024-06-15',
          valid_till: '2025-06-14',
          renewal_status: 'Lapsed - Renewal Application Not Received',
        },
        discrepancy_summary: 'Claimed validity (30-Jun-2026) contradicts state registry record (14-Jun-2025). Lapsed by 485 days.',
      },
      ai_confidence: {
        stage: 5,
        title: 'Multi-Modal AI Decision-Support Assessment',
        aggregate_confidence: 0.942,
        risk_level: 'CRITICAL',
        wording: 'Indicator for review: Document validity period discrepancy detected',
        model_rationale: 'High OCR confidence (97.8%) combined with authoritative state API verification confirms certificate expired before the commencement of AY 2025-26.',
        advisory_disclaimer: 'AI outputs are decision-support aids for committee inquiry, not proofs of document alteration.',
      },
      officer_action: {
        stage: 6,
        title: 'Human-in-the-Loop Officer Determination',
        current_status: 'PENDING_OFFICER_REVIEW',
        statutory_guidance: 'Issue show-cause directive granting 15 calendar days to submit active renewed Fire Safety NOC approved by competent fire authority.',
      },
    },

    // Right Column: Default Officer State
    action_panel: {
      default_decision: 'REQUEST_MORE_EVIDENCE',
      mandatory_comment_placeholder: 'Specify reasons for issuing clarification, timeline for resubmission, or inspection referral rationale...',
    },
  },

  {
    id: 'FINDING-GRAPH-002',
    finding_type: 'GRAPH_CONFLICT',
    title: 'Concurrent Full-Time Faculty Appointment (Dual Employment)',
    clause_id: 'APH 2025-26 Clause 2.7.4',
    clause_title: 'Cadre Exclusivity & Full-Time Faculty Verification',
    severity: 'CRITICAL',
    ai_wording: 'Indicator for review: Concurrent full-time tenure detected across multiple institutions',
    application_no: 'APP-2025-09812',
    institution_name: 'Apex Institute of Technology & Science',
    category: 'Extension of Approval (EoA)',

    // Left Column: Conflicting Subgraph Specs for vis-network
    subgraph: {
      conflict_type: 'DUAL_EMPLOYMENT_FACULTY',
      entity_name: 'Dr. R. K. Sharma',
      masked_pan: 'AB****89C',
      masked_aadhaar: 'XXXX-XXXX-9021',
      summary: 'Recorded as full-time regular Professor at Apex Tech (Bengaluru) and Royal College (Mysuru) simultaneously.',
      nodes: [
        { id: 'INST_001', label: 'Apex Institute\n(Bengaluru)', group: 'institution', shape: 'box', color: '#0284c7' },
        { id: 'INST_002', label: 'Royal College of Engg\n(Mysuru)', group: 'institution', shape: 'box', color: '#0284c7' },
        { id: 'FAC_101', label: 'Dr. R. K. Sharma\n[PAN: AB****89C]', group: 'faculty', shape: 'dot', color: '#e11d48', size: 28 },
        { id: 'DOC_CADRE_1', label: 'Faculty Roster 2025\n[Apex Tech]', group: 'document', shape: 'ellipse', color: '#f59e0b' },
        { id: 'DOC_CADRE_2', label: 'Faculty Roster 2025\n[Royal College]', group: 'document', shape: 'ellipse', color: '#f59e0b' },
      ],
      edges: [
        { from: 'INST_001', to: 'FAC_101', label: 'employs (Full-Time)\n2021-08 to Present', color: '#e11d48', dashes: true, width: 2.5 },
        { from: 'INST_002', to: 'FAC_101', label: 'employs (Full-Time)\n2022-01 to Present', color: '#e11d48', dashes: true, width: 2.5 },
        { from: 'DOC_CADRE_1', to: 'FAC_101', label: 'lists professor', color: '#94a3b8' },
        { from: 'DOC_CADRE_2', to: 'FAC_101', label: 'lists professor', color: '#94a3b8' },
      ],
    },

    // Center Column: Pipeline Strip
    pipeline: {
      claim: {
        stage: 1,
        title: 'Institutional Declaration',
        declared_value: 'Dr. R. K. Sharma, Professor & HoD (Full-Time)',
        declared_field: 'faculty_cadre_roster',
        submission_timestamp: '2026-10-18T09:30:00 UTC',
        institution_note: 'Submitted under regular approved faculty roster for Department of Mechanical Engineering.',
      },
      evidence: {
        stage: 2,
        title: 'Cross-Institutional Network Graph Match',
        extracted_text: 'PAN: AB****89C • Aadhaar: XXXX-XXXX-9021 • DOB: 1975-08-12',
        normalized_value: 'Dr. R. K. Sharma (PAN AB****89C)',
        field_name: 'faculty_pan',
        ocr_engine: 'NetworkX Institution Twin Knowledge Graph',
        ocr_confidence: 0.995,
        sha256: '4c6e8a0b2d4f6a8c0e2b4d6f8a...',
      },
      rule: {
        stage: 3,
        title: 'Regulation-as-Code Rule Citation',
        handbook_edition: 'AICTE Approval Process Handbook (APH) 2025-26',
        clause_id: 'APH-CH2-Clause-2.7.4',
        clause_citation: 'Clause 2.7.4 (Chapter II) - Faculty Cadre & Exclusivity Norms',
        statutory_norm: 'Faculty claimed towards mandatory Student-to-Faculty Ratio (SFR 1:15) must serve exclusively on full-time basis.',
        compliance_status: 'DEFICIENT (GHOST FACULTY CONFLICT)',
      },
      source_response: {
        stage: 4,
        title: 'Authoritative AISHE / Income Tax Deductions Match',
        issuer_name: 'National AISHE Higher Education Portal & Form 26AS TDS',
        query_ref: 'FAC-PAN-AB89C-2025',
        status: 'mismatch_detected',
        latency_ms: 220,
        response_payload: {
          pan_masked: 'AB****89C',
          concurrent_employers: [
            { institution: 'Apex Institute of Technology (1-109283711)', role: 'Professor', active: true },
            { institution: 'Royal College of Engineering (1-209384722)', role: 'Professor', active: true },
          ],
        },
        discrepancy_summary: 'Active salary credits and full-time regular employment reported from two institutions located 145km apart.',
      },
      ai_confidence: {
        stage: 5,
        title: 'Multi-Modal AI Decision-Support Assessment',
        aggregate_confidence: 0.995,
        risk_level: 'CRITICAL',
        wording: 'Indicator for review: Concurrent full-time tenure detected across multiple institutions',
        model_rationale: 'Deterministic match on masked PAN (AB****89C) + exact DOB match (12-Aug-1975) + overlapping service dates constitutes an indicator for review under exclusivity guidelines.',
        advisory_disclaimer: 'AI outputs are decision-support aids for committee inquiry, not proofs of document alteration.',
      },
      officer_action: {
        stage: 6,
        title: 'Human-in-the-Loop Officer Determination',
        current_status: 'PENDING_OFFICER_REVIEW',
        statutory_guidance: 'Issue show-cause notice requesting Aadhaar-enabled biometric attendance logs and Form 16 from both institutions before determination.',
      },
    },

    // Right Column: Default Officer State
    action_panel: {
      default_decision: 'REQUEST_MORE_EVIDENCE',
      mandatory_comment_placeholder: 'State specific clarification demand, biocentric attendance requirement, or referral to Standing Committee...',
    },
  },

  {
    id: 'FINDING-AREA-003',
    finding_type: 'DOCUMENT',
    title: 'Total Campus Built-Up Area Footprint vs Satellite Polygons',
    clause_id: 'APH 2025-26 Clause 2.4.2',
    clause_title: 'Built-Up Area & Instructional Space Norms',
    severity: 'WARNING',
    ai_wording: 'Indicator for review: Built-up area footprint deficit beyond tolerance threshold',
    application_no: 'APP-2025-09812',
    institution_name: 'Apex Institute of Technology & Science',
    category: 'Extension of Approval (EoA)',

    document: {
      filename: 'Approved_Master_Building_Plan_Block_B.pdf',
      document_type: 'Approved Building Plan',
      issue_date: '2023-11-20',
      valid_till: '2028-11-19',
      file_hash: '9e2c4f6a8b0c2e4d6f8a0b2c4e6f8a0b2c4e6f8a0b2c4e6f8a0b2c4e6f8a0b2c',
      page_number: 2,
      total_pages: 5,
      preview_url: null,
      extracted_field: {
        field_name: 'total_built_up_area_sqm',
        field_label: 'Total Instructional Built-Up Area',
        raw_text: 'TOTAL PROPOSED BUILT-UP AREA: 18,200.00 SQ.M (BLOCK A, B, C & LAB COMPLEX)',
        normalized_value: '18200.0 sqm',
        ocr_confidence: 0.962,
        bounding_box: {
          x: 20,
          y: 58,
          width: 58,
          height: 7,
          pixel_x: 150,
          pixel_y: 440,
          pixel_w: 430,
          pixel_h: 52,
        },
      },
      forensics: {
        ela_score: 0.24,
        ela_status: 'CLEAN',
        producer: 'AutoCAD 2023 Architecture (Authentic)',
        creation_date: '2023-11-18T16:20:00Z',
      },
    },

    pipeline: {
      claim: {
        stage: 1,
        title: 'Institutional Declaration',
        declared_value: '18,200.00 sqm Built-Up Area',
        declared_field: 'total_built_up_area_sqm',
        submission_timestamp: '2026-10-18T09:30:00 UTC',
        institution_note: 'Includes academic block, 12 departmental laboratories, and central library complex.',
      },
      evidence: {
        stage: 2,
        title: 'OCR Extraction from Municipal Building Plan',
        extracted_text: 'TOTAL PROPOSED BUILT-UP AREA: 18,200.00 SQ.M',
        normalized_value: '18200.0 sqm',
        field_name: 'total_built_up_area_sqm',
        ocr_engine: 'PaddleOCR Blueprint Layout Parser',
        ocr_confidence: 0.962,
        sha256: '9e2c4f6a8b0c2e4d6f8a0b2c...',
      },
      rule: {
        stage: 3,
        title: 'Regulation-as-Code Rule Citation',
        handbook_edition: 'AICTE Approval Process Handbook (APH) 2025-26',
        clause_id: 'APH-CH2-Clause-2.4.2',
        clause_citation: 'Clause 2.4.2 (Chapter II) - Instructional, Administrative & Amenities Area Norms',
        statutory_norm: 'Minimum 14,500 sqm required for claimed intake of 480 undergraduate engineering students.',
        compliance_status: 'ADVISORY INDICATOR (GEOSPATIAL DEFICIT)',
      },
      source_response: {
        stage: 4,
        title: 'Open Buildings & OSM Polygon Area Measurement',
        issuer_name: 'Open Buildings / OSM Metric Azimuthal Projection Engine',
        query_ref: 'GEO-LAT-13.08-LON-77.58',
        status: 'mismatch_detected',
        latency_ms: 310,
        response_payload: {
          claimed_area_sqm: 18200.0,
          measured_footprint_sqm: 14196.0,
          discrepancy_ratio: -0.22,
          tolerance_band: [-0.15, 0.25],
        },
        discrepancy_summary: 'Claimed 18,200 sqm exceeds measured polygon footprint (14,196 sqm) by -22% (outside -15% tolerance band).',
      },
      ai_confidence: {
        stage: 5,
        title: 'Multi-Modal AI Decision-Support Assessment',
        aggregate_confidence: 0.884,
        risk_level: 'WARNING',
        wording: 'Indicator for review: Built-up area footprint deficit beyond tolerance threshold',
        model_rationale: 'Geospatial area measurement discrepancy indicates either multi-story floor multiplier mismatch or under-construction blocks.',
        advisory_disclaimer: 'AI outputs are decision-support aids for committee inquiry, not proofs of document alteration.',
      },
      officer_action: {
        stage: 6,
        title: 'Human-in-the-Loop Officer Determination',
        current_status: 'PENDING_OFFICER_REVIEW',
        statutory_guidance: 'Recommend physical inspection or request certified floor-wise municipal completion certificate.',
      },
    },

    action_panel: {
      default_decision: 'RECOMMEND_INSPECTION',
      mandatory_comment_placeholder: 'Specify physical inspection terms or request architect-certified floor plans...',
    },
  },
];
