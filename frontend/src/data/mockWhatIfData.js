/**
 * Mock What-If Simulator & Policy Cohort Dataset:
 * Provides rules with parameter ranges, 150 simulated applicant records across Indian states & course types,
 * and dynamic dry-run impact evaluation logic.
 */

export const SIMULATION_RULES = [
  {
    id: 'RULE-FSR-001',
    rule_code: 'APH-CH2-Clause-2.7.1',
    clause_id: 'APH 2025-26 Clause 2.7.1',
    title: 'Student-to-Faculty Ratio (SFR / FSR) Norm',
    chapter: 'Chapter II: Norms for Faculty Requirements',
    description: 'Mandates maximum student-to-faculty ratio across undergraduate and postgraduate technical programs.',
    parameter_name: 'target_ratio',
    parameter_label: 'Target Student-to-Faculty Ratio',
    unit: 'Students per Faculty',
    baseline_value: 15,
    min: 10,
    max: 25,
    step: 1,
    severity: 'CRITICAL',
    default_simulated_value: 18,
    metric_field: 'fsr',
  },
  {
    id: 'RULE-AREA-002',
    rule_code: 'APH-CH2-Clause-2.4.2',
    clause_id: 'APH 2025-26 Clause 2.4.2',
    title: 'Built-up Area Tolerance Deficit Margin',
    chapter: 'Chapter II: Infrastructure & Instructional Space Norms',
    description: 'Permissible negative tolerance percentage between claimed instructional built-up area and measured footprint.',
    parameter_name: 'tolerance_deficit_pct',
    parameter_label: 'Permissible Footprint Deficit Tolerance',
    unit: '% Deficit Band',
    baseline_value: 15,
    min: 5,
    max: 30,
    step: 1,
    severity: 'WARNING',
    default_simulated_value: 20,
    metric_field: 'area_deficit',
  },
  {
    id: 'RULE-LAND-003',
    rule_code: 'APH-CH2-Clause-2.3.1',
    clause_id: 'APH 2025-26 Clause 2.3.1',
    title: 'Minimum Contiguous Land for Urban / Metro Campus',
    chapter: 'Chapter II: Land & Location Specifications',
    description: 'Minimum required contiguous land parcel in acres for technical institutions located in Tier-1/Metro urban zones.',
    parameter_name: 'min_land_acres',
    parameter_label: 'Minimum Urban Land Requirement',
    unit: 'Acres',
    baseline_value: 7.5,
    min: 3.0,
    max: 10.0,
    step: 0.5,
    severity: 'CRITICAL',
    default_simulated_value: 5.0,
    metric_field: 'land_acres',
  },
  {
    id: 'RULE-CADRE-004',
    rule_code: 'APH-CH2-Clause-2.7.3',
    clause_id: 'APH 2025-26 Clause 2.7.3',
    title: 'Senior Faculty Cadre (Professor) Proportion',
    chapter: 'Chapter II: Cadre Ratio (1:2:6)',
    description: 'Minimum required proportion of Professor cadre relative to total required faculty count.',
    parameter_name: 'min_prof_pct',
    parameter_label: 'Minimum Professor Cadre Share',
    unit: '% of Faculty',
    baseline_value: 11.1,
    min: 5.0,
    max: 20.0,
    step: 0.5,
    severity: 'WARNING',
    default_simulated_value: 8.0,
    metric_field: 'prof_pct',
  },
];

// Sample of 12 detailed before/after applications representing the 150-cohort
export const MOCK_APPLICATIONS_COHORT = [
  {
    id: 1,
    app_no: 'APP-2025-09812',
    institution_name: 'Apex Institute of Technology & Science',
    state: 'Karnataka',
    city: 'Bengaluru',
    course_type: 'Engineering (UG/PG)',
    metrics: { fsr: 17.2, area_deficit: 22.0, land_acres: 6.2, prof_pct: 9.5 },
  },
  {
    id: 2,
    app_no: 'APP-2024-ENG-1102',
    institution_name: 'Royal College of Engineering',
    state: 'Karnataka',
    city: 'Mysuru',
    course_type: 'Engineering (UG/PG)',
    metrics: { fsr: 16.5, area_deficit: 12.0, land_acres: 8.0, prof_pct: 12.0 },
  },
  {
    id: 3,
    app_no: 'APP-2025-MAH-3012',
    institution_name: 'Zenith Institute of Technology',
    state: 'Maharashtra',
    city: 'Pune',
    course_type: 'Management (MBA)',
    metrics: { fsr: 19.4, area_deficit: 18.5, land_acres: 4.8, prof_pct: 7.2 },
  },
  {
    id: 4,
    app_no: 'APP-2025-POLY-8190',
    institution_name: 'Greenfield Polytechnic & Research',
    state: 'Karnataka',
    city: 'Belagavi',
    course_type: 'Polytechnic Diploma',
    metrics: { fsr: 18.0, area_deficit: 14.0, land_acres: 5.5, prof_pct: 10.0 },
  },
  {
    id: 5,
    app_no: 'APP-2025-ENG-4491',
    institution_name: 'Vanguard Institute of Technology',
    state: 'Telangana',
    city: 'Hyderabad',
    course_type: 'Engineering (UG/PG)',
    metrics: { fsr: 17.8, area_deficit: 19.2, land_acres: 7.2, prof_pct: 8.8 },
  },
  {
    id: 6,
    app_no: 'APP-2025-TN-9988',
    institution_name: 'Metro Institute of Technology',
    state: 'Tamil Nadu',
    city: 'Chennai',
    course_type: 'Engineering (UG/PG)',
    metrics: { fsr: 15.8, area_deficit: 11.5, land_acres: 6.0, prof_pct: 11.5 },
  },
  {
    id: 7,
    app_no: 'APP-2025-UP-5512',
    institution_name: 'Kashi Institute of Management',
    state: 'Uttar Pradesh',
    city: 'Varanasi',
    course_type: 'Management (MBA)',
    metrics: { fsr: 21.0, area_deficit: 24.0, land_acres: 4.2, prof_pct: 6.5 },
  },
  {
    id: 8,
    app_no: 'APP-2025-DEL-2091',
    institution_name: 'Capital College of Computer Applications',
    state: 'Delhi NCR',
    city: 'New Delhi',
    course_type: 'Computer Applications (MCA)',
    metrics: { fsr: 16.2, area_deficit: 16.0, land_acres: 3.8, prof_pct: 10.5 },
  },
  {
    id: 9,
    app_no: 'APP-2025-TN-4102',
    institution_name: 'Coimbatore Institute of Pharmacy',
    state: 'Tamil Nadu',
    city: 'Coimbatore',
    course_type: 'Pharmacy',
    metrics: { fsr: 14.8, area_deficit: 9.0, land_acres: 5.2, prof_pct: 14.0 },
  },
  {
    id: 10,
    app_no: 'APP-2025-MAH-7781',
    institution_name: 'Vidarbha School of Architecture',
    state: 'Maharashtra',
    city: 'Nagpur',
    course_type: 'Architecture & Planning',
    metrics: { fsr: 17.5, area_deficit: 21.5, land_acres: 4.5, prof_pct: 9.0 },
  },
  {
    id: 11,
    app_no: 'APP-2025-UP-8821',
    institution_name: 'Awadh Engineering Academy',
    state: 'Uttar Pradesh',
    city: 'Lucknow',
    course_type: 'Engineering (UG/PG)',
    metrics: { fsr: 18.2, area_deficit: 17.0, land_acres: 6.8, prof_pct: 8.5 },
  },
  {
    id: 12,
    app_no: 'APP-2025-KA-0012',
    institution_name: 'National Institute of Design & Tech',
    state: 'Karnataka',
    city: 'Bengaluru',
    course_type: 'Architecture & Planning',
    metrics: { fsr: 14.2, area_deficit: 8.5, land_acres: 7.8, prof_pct: 15.0 },
  },
];

/**
 * Calculates dry-run simulation outcomes across cohort given a rule and simulated value.
 */
export function runWhatIfSimulation(ruleId, simulatedValue) {
  const rule = SIMULATION_RULES.find((r) => r.id === ruleId) || SIMULATION_RULES[0];
  const baselineVal = rule.baseline_value;

  let totalCohort = 150;
  let changedCount = 0;
  let clearedCount = 0;
  let newlyFlaggedCount = 0;

  // Evaluate the 12 representative applications
  const sampleResults = MOCK_APPLICATIONS_COHORT.map((app) => {
    const val = app.metrics[rule.metric_field];
    let beforePassed = false;
    let afterPassed = false;

    if (rule.metric_field === 'fsr') {
      // Lower or equal is better
      beforePassed = val <= baselineVal;
      afterPassed = val <= simulatedValue;
    } else if (rule.metric_field === 'area_deficit') {
      // Deficit lower or equal to tolerance is better
      beforePassed = val <= baselineVal;
      afterPassed = val <= simulatedValue;
    } else if (rule.metric_field === 'land_acres' || rule.metric_field === 'prof_pct') {
      // Higher or equal is better
      beforePassed = val >= baselineVal;
      afterPassed = val >= simulatedValue;
    }

    const beforeStatus = beforePassed ? 'Verified' : 'Mismatch Detected';
    const afterStatus = afterPassed ? 'Verified' : 'Mismatch Detected';
    
    let changeType = 'NO_CHANGE';
    if (!beforePassed && afterPassed) {
      changeType = 'STATUS_CLEARED';
    } else if (beforePassed && !afterPassed) {
      changeType = 'NEWLY_FLAGGED';
    }

    return {
      ...app,
      metricValue: val,
      unit: rule.unit,
      beforeStatus,
      afterStatus,
      changeType,
    };
  });

  // Calculate cohort extrapolation (scale of 150)
  const isRelaxation = (rule.metric_field === 'fsr' || rule.metric_field === 'area_deficit')
    ? simulatedValue > baselineVal
    : simulatedValue < baselineVal;

  const deltaPct = Math.abs((simulatedValue - baselineVal) / baselineVal);
  changedCount = Math.round(totalCohort * Math.min(0.45, deltaPct * 1.2 + 0.08));
  if (isRelaxation) {
    clearedCount = Math.round(changedCount * 0.88);
    newlyFlaggedCount = changedCount - clearedCount;
  } else {
    newlyFlaggedCount = Math.round(changedCount * 0.85);
    clearedCount = changedCount - newlyFlaggedCount;
  }

  // State Breakdown Data for Bar Chart
  const stateBreakdown = [
    { state: 'Karnataka', baseline: 18, simulated: isRelaxation ? Math.max(4, 18 - Math.round(clearedCount * 0.35)) : 18 + Math.round(newlyFlaggedCount * 0.35) },
    { state: 'Maharashtra', baseline: 16, simulated: isRelaxation ? Math.max(3, 16 - Math.round(clearedCount * 0.25)) : 16 + Math.round(newlyFlaggedCount * 0.25) },
    { state: 'Tamil Nadu', baseline: 14, simulated: isRelaxation ? Math.max(3, 14 - Math.round(clearedCount * 0.15)) : 14 + Math.round(newlyFlaggedCount * 0.15) },
    { state: 'Uttar Pradesh', baseline: 15, simulated: isRelaxation ? Math.max(5, 15 - Math.round(clearedCount * 0.12)) : 15 + Math.round(newlyFlaggedCount * 0.12) },
    { state: 'Telangana', baseline: 11, simulated: isRelaxation ? Math.max(2, 11 - Math.round(clearedCount * 0.08)) : 11 + Math.round(newlyFlaggedCount * 0.08) },
    { state: 'Delhi NCR', baseline: 8, simulated: isRelaxation ? Math.max(1, 8 - Math.round(clearedCount * 0.05)) : 8 + Math.round(newlyFlaggedCount * 0.05) },
  ];

  // Course Type Breakdown Data for Bar Chart
  const courseTypeBreakdown = [
    { courseType: 'Engineering (UG/PG)', baseline: 36, simulated: isRelaxation ? Math.max(8, 36 - Math.round(clearedCount * 0.45)) : 36 + Math.round(newlyFlaggedCount * 0.45) },
    { courseType: 'Management (MBA)', baseline: 19, simulated: isRelaxation ? Math.max(4, 19 - Math.round(clearedCount * 0.22)) : 19 + Math.round(newlyFlaggedCount * 0.22) },
    { courseType: 'MCA', baseline: 12, simulated: isRelaxation ? Math.max(2, 12 - Math.round(clearedCount * 0.12)) : 12 + Math.round(newlyFlaggedCount * 0.12) },
    { courseType: 'Pharmacy', baseline: 9, simulated: isRelaxation ? Math.max(1, 9 - Math.round(clearedCount * 0.09)) : 9 + Math.round(newlyFlaggedCount * 0.09) },
    { courseType: 'Architecture', baseline: 7, simulated: isRelaxation ? Math.max(1, 7 - Math.round(clearedCount * 0.07)) : 7 + Math.round(newlyFlaggedCount * 0.07) },
    { courseType: 'Polytechnic', baseline: 9, simulated: isRelaxation ? Math.max(2, 9 - Math.round(clearedCount * 0.05)) : 9 + Math.round(newlyFlaggedCount * 0.05) },
  ];

  return {
    rule,
    baselineValue: baselineVal,
    simulatedValue,
    totalCohort,
    changedCount,
    clearedCount,
    newlyFlaggedCount,
    isRelaxation,
    sampleResults,
    stateBreakdown,
    courseTypeBreakdown,
  };
}
