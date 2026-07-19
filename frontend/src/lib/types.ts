export type AnalysisType =
  | "correlation"
  | "pearson_correlation"
  | "spearman_correlation"
  | "kendall_tau"
  | "partial_correlation"
  | "distance_correlation"
  | "point_biserial"
  | "eta_squared"
  | "descriptive_summary"
  | "frequency_table"
  | "cross_tabulation"
  | "pivot_summary"
  | "quantile_profile"
  | "trimmed_mean"
  | "winsorized_summary"
  | "gini_coefficient"
  | "pareto_analysis"
  | "segmented_kpi_breakdown"
  | "ols"
  | "ridge_regression"
  | "lasso_regression"
  | "elastic_net"
  | "robust_regression"
  | "quantile_regression"
  | "anova"
  | "two_way_anova"
  | "ancova"
  | "logit"
  | "random_forest"
  | "neural_network"
  | "deep_learning"
  | "pca"
  | "kmeans"
  | "ttest"
  | "paired_ttest"
  | "one_sample_ttest"
  | "z_test_mean"
  | "ab_test"
  | "repeated_measures_anova"
  | "chi_square"
  | "fisher_exact"
  | "mcnemar"
  | "cochran_q"
  | "cmh_test"
  | "cramers_v"
  | "phi_coefficient"
  | "theils_u"
  | "goodman_kruskal_lambda"
  | "cohens_kappa"
  | "mann_whitney"
  | "wilcoxon_signed_rank"
  | "sign_test"
  | "kruskal"
  | "friedman"
  | "mood_median"
  | "ks_two_sample"
  | "runs_test"
  | "median_test"
  | "fligner_killeen"
  | "permutation_test"
  | "bootstrap_ci"
  | "poisson_glm"
  | "normality"
  | "shapiro_wilk"
  | "dagostino_k2"
  | "jarque_bera"
  | "kolmogorov_smirnov_1samp"
  | "anderson_darling"
  | "breusch_pagan"
  | "white_test"
  | "durbin_watson"
  | "moving_average"
  | "autocorrelation"
  | "partial_autocorrelation"
  | "ljung_box"
  | "adf_test"
  | "tukey_hsd"
  | "levene"
  | "brown_forsythe"
  | "bartlett"
  | "welch_anova"
  | "auto_runtime_analysis";

export type SupportedLanguage = "python" | "sql" | "r";

export type GenericTable = {
  title?: string;
  columns: string[];
  rows: Record<string, unknown>[];
};

export type ChartPayload =
  | {
      kind: "histogram" | "bar";
      title: string;
      x: string[];
      y: number[];
      x_label?: string;
      explanation?: string;
    }
  | {
      kind: "line";
      title: string;
      x: string[];
      y: number[];
      x_label?: string;
      y_label?: string;
      explanation?: string;
    }
  | {
      kind: "forecast";
      title: string;
      x: string[];
      actual: Array<number | null>;
      forecast: Array<number | null>;
      x_label?: string;
      y_label?: string;
      explanation?: string;
    }
  | {
      kind: "heatmap";
      title: string;
      labels: string[];
      matrix: number[][];
      explanation?: string;
    }
  | {
      kind: "scatter";
      title: string;
      x_label: string;
      y_label: string;
      points: [number, number][];
      explanation?: string;
    }
  | {
      kind: "cluster-scatter";
      title: string;
      x_label: string;
      y_label: string;
      points: [number, number, number][];
      cluster_summary?: Array<Record<string, unknown>>;
      explanation?: string;
    }
  | {
      kind: "anomaly-scatter";
      title: string;
      x_label: string;
      y_label: string;
      threshold?: number;
      points: Array<{
        name: string;
        x: number;
        y: number;
        score: number;
        is_anomaly: boolean;
      }>;
      explanation?: string;
    }
  | {
      kind: "bubble";
      title: string;
      x_label: string;
      y_label: string;
      size_label: string;
      color_label?: string;
      points: Array<{
        name: string;
        x: number;
        y: number;
        size: number;
        category?: string;
        quadrant?: string;
      }>;
      explanation?: string;
    }
  | {
      kind: "quadrant";
      title: string;
      x_label: string;
      y_label: string;
      x_mid: number;
      y_mid: number;
      points: Array<{
        name: string;
        x: number;
        y: number;
        size: number;
        category?: string;
        quadrant?: string;
      }>;
      quadrant_labels?: Record<string, string>;
      explanation?: string;
    };

export type AutoReportPart = {
  id: string;
  title: string;
  narrative: string;
  bullets: string[];
  tables: GenericTable[];
  charts: ChartPayload[];
  data?: Record<string, unknown>;
  evidence_refs?: string[];
};

export type AutoReportPartAssetManifestRow = {
  report_part_id: string;
  report_part_title?: string;
  asset_kind: "text" | "table" | "image" | "structured_data" | string;
  asset_ref: string;
  asset_title?: string;
  source?: string;
  payload_keys?: string;
  management_use?: string;
};

export type AutoReportPartGenerationBlueprint = {
  report_part_id: string;
  report_part_title?: string;
  readiness: "ready" | "partial" | "blocked" | string;
  required_asset_kinds: string[];
  available_asset_refs: Record<string, string[]>;
  missing_asset_kinds: string[];
  text_seed_count?: number;
  narrative_seed?: string;
  bullet_seeds?: string[];
  table_titles?: string[];
  chart_refs?: string[];
  table_count?: number;
  chart_count?: number;
  method_evidence_count?: number;
  semantic_route_field_count?: number;
  pre_method_preprocessing_status?: string;
  input_contract?: Record<string, unknown>;
  runtime_handoff?: {
    target?: string;
    task?: string;
    required_outputs?: string[];
    must_use_pre_method_audit?: boolean;
    must_use_method_route_evidence?: boolean;
    must_preserve_evidence_refs?: boolean;
    allowed_outputs?: string[];
    blocked_if_missing?: string[];
  };
  method_evidence?: Array<Record<string, unknown>>;
  audit_summary?: Record<string, unknown>;
  management_use?: string;
};

export type AutoAnalysisData = {
  report_part_generation_blueprints?: AutoReportPartGenerationBlueprint[];
  report_part_asset_manifest?: AutoReportPartAssetManifestRow[];
  pre_method_routing_audit?: Array<Record<string, unknown>>;
  method_route_evidence?: Array<Record<string, unknown>>;
  method_card_executions?: Array<Record<string, unknown>>;
  method_execution_assets?: Array<Record<string, unknown>>;
  method_execution_packages?: Array<Record<string, unknown>>;
  method_downloads?: Array<{
    method_id?: string;
    method_name?: string;
    method_name_zh?: string;
    family?: string;
    file_name?: string;
    download_kind?: string;
    execution_id?: string;
    asset_count?: number;
    result_ref?: string;
    package_ref?: string;
    runtime_handoff_count?: number;
    pre_method_preprocessing_status?: string;
  }>;
  report_part_bundle?: Record<string, unknown>;
  lab_report?: Record<string, unknown>;
  smart_merge_download?: Record<string, unknown>;
  external_skill_context?: Record<string, unknown>;
  external_skill_ids?: string[];
};

export type DatasetSummary = {
  dataset_id: string;
  name: string;
  filename: string;
  active_sheet: string;
  sheets: Array<{
    name: string;
    storage_file: string;
    rows: number;
    columns: number;
  }>;
  row_count: number;
  column_count: number;
  numeric_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  missing_cells: number;
  sample_rows: Record<string, unknown>[];
  column_summaries: Array<{
    name: string;
    dtype: string;
    missing_count: number;
    missing_ratio: number;
    unique_count: number;
    sample_values: unknown[];
    stats: Record<string, unknown>;
  }>;
  chart_bundle: {
    distribution?: ChartPayload;
    category?: ChartPayload;
    correlation?: ChartPayload;
    scatter?: ChartPayload;
  };
  last_updated: string;
};

export type HistoricalReportTemplate = {
  template_id: string;
  name: string;
  filename: string;
  path: string;
  word_count: number;
  char_count: number;
  preview: string;
  extracted_text: string;
  uploaded_at: string;
};

export type BusinessBackgroundAsset = {
  context_id: string;
  name: string;
  filename: string;
  path: string;
  source_type: string;
  char_count: number;
  preview: string;
  extracted_text: string;
  outline: string[];
  uploaded_at: string;
};

export type Manifest = {
  product: string;
  integrations: Array<{
    name: string;
    repo: string;
    purpose: string;
  }>;
  supported_uploads: string[];
  supported_historical_reports?: string[];
  supported_languages: SupportedLanguage[];
  analysis_types: AnalysisType[];
  runtime_configuration?: string[];
};

export type StatsResult = {
  analysis_type: AnalysisType;
  title: string;
  narrative: string;
  metrics: Record<string, number | string | null>;
  tables: GenericTable[];
  chart?: ChartPayload;
  charts?: ChartPayload[];
  report_parts?: AutoReportPart[];
  data?: unknown;
  downloadables?: Array<{
    name: string;
    path: string;
    file_path?: string;
    purpose?: string;
    is_main?: boolean;
    type?: string;
    download_kind?: string;
    method_id?: string;
    method_name?: string;
    method_name_zh?: string;
    family?: string;
    package_ref?: string;
    method_package_count?: number;
    method_display_package_count?: number;
    method_display_policy?: Record<string, unknown>;
    display_group?: Record<string, unknown>;
    runtime_handoff_count?: number;
    dispatch_plan_count?: number;
    report_part_dispatch_count?: number;
    runtime_dispatch_count?: number;
    pre_method_preprocessing_status?: string;
    report_id?: string;
    external_skill_count?: number;
    external_skill_ids?: string[];
    external_skill_application_required?: boolean;
    external_skill_application_status?: string;
  }>;
};

export type CodeExecutionResult = {
  language: SupportedLanguage;
  dataset_name?: string;
  active_sheet: string;
  stdout: string;
  stderr: string;
  result_kind: "table" | "json" | "text" | "empty" | string;
  table: GenericTable | null;
  result: unknown;
  images: string[];
  elapsed_ms: number;
};

export type WorkbookPreview = {
  name: string;
  activeSheet: string;
  sheets: string[];
  rows: Record<string, unknown>[];
};

export type RuntimeSettings = {
  api_key: string;
  model: string;
  base_url: string;
  provider_label: string;
  relay_note: string;
  rscript_path: string;
};

export type RuntimeSettingsView = {
  api_key_masked: string;
  has_api_key: boolean;
  model: string;
  base_url: string;
  provider_label: string;
  relay_note: string;
  rscript_path: string;
};

export type SmartReportSection = {
  id: string;
  title: string;
  summary: string;
  bullets: string[];
  tables: GenericTable[];
  charts: ChartPayload[];
};

export type SmartReport = {
  report_id: string;
  title: string;
  dataset_id: string;
  dataset_name: string;
  sheet_name: string;
  enable_generic_business_runtime?: boolean;
  related_reports?: Array<{
    report_id: string;
    sheet_name: string;
    executive_summary: string[];
    main_downloadable: {
      name: string;
      path: string;
      purpose: string;
      is_main: boolean;
      type: string;
    };
  }>;
  report_style: "executive" | "deep_dive";
  report_language?: "zh-CN";
  generated_at: string;
  key_metrics: Array<{
    label: string;
    value: string | number;
    detail: string;
  }>;
  requirement_restatement: {
    bullets: string[];
  };
  requirement_confirmation: {
    items: string[];
  };
  data_initial_understanding: {
    bullets: string[];
  };
  output_strategy: {
    bullets: string[];
  };
  generation_plan: string[];
  semantic_layer: {
    mode: string;
    reason?: string;
    title: string;
    subject_type?: string;
    creator_profile: string;
    content_domains: string[];
    audience_profile: string[];
    evidence_points: string[];
    text_findings: string[];
    numeric_findings: string[];
    important_columns: string[];
    recommended_actions: string[];
    model?: string;
    provider_label?: string;
    reasoning_effort?: string;
  };
  executive_summary: string[];
  codex_layer: {
    mode: string;
    reason?: string;
    board_title: string;
    executive_summary_rewrite: string[];
    strategic_recommendations: string[];
    risk_flags: string[];
    next_questions: string[];
    model?: string;
    provider_label?: string;
  };
  historical_report_adaptation?: {
    mode: string;
    reason?: string;
    title: string;
    source_name?: string;
    template_signals: string[];
    adaptation_notes: string[];
    adapted_report_markdown: string;
    model?: string;
    provider_label?: string;
    reasoning_effort?: string;
  };
  historical_style_cli_pipeline_job_id?: string;
  historical_style_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
  };
  historical_style_cli_final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    reverse_spec_markdown_name?: string;
    reverse_spec_markdown_path?: string;
    reverse_spec_markdown_url?: string;
    reverse_spec_json_name?: string;
    reverse_spec_json_path?: string;
    reverse_spec_json_url?: string;
    page_plan_markdown_name?: string;
    page_plan_markdown_path?: string;
    page_plan_markdown_url?: string;
    page_plan_json_name?: string;
    page_plan_json_path?: string;
    page_plan_json_url?: string;
    metadata_artifact_name?: string;
    metadata_artifact_path?: string;
    metadata_artifact_url?: string;
    chart_assets_index_name?: string;
    chart_assets_index_path?: string;
    chart_assets_index_url?: string;
    table_assets_index_name?: string;
    table_assets_index_path?: string;
    table_assets_index_url?: string;
    collage_assets_index_name?: string;
    collage_assets_index_path?: string;
    collage_assets_index_url?: string;
    deck_layout_pack_name?: string;
    deck_layout_pack_path?: string;
    deck_layout_pack_url?: string;
    html_artifact_name?: string;
    html_artifact_path?: string;
    html_artifact_url?: string;
    css_artifact_name?: string;
    css_artifact_path?: string;
    css_artifact_url?: string;
    pdf_artifact_name?: string;
    pdf_artifact_path?: string;
    pdf_artifact_url?: string;
    historical_report_family?: string;
    rendered_page_count?: number;
    planned_page_count?: number;
    chart_asset_count?: number;
    table_asset_count?: number;
    collage_asset_count?: number;
    template_counts?: Record<string, number>;
    page_count_target?: Record<string, unknown>;
    title?: string;
    source_name?: string;
    delivery_summary?: string;
  };
  r_workflow?: {
    enabled: boolean;
    status: string;
    runtime_available: boolean;
    runtime_path: string;
    workflow_dir: string;
    interpretation_summary: string[];
    downloadables: Array<{
      name: string;
      path: string;
      purpose: string;
      is_main: boolean;
      type: string;
    }>;
  };
  requirement_intent?: ReportIntentSpec;
  report_design_spec?: ReportDesignSpec;
  report_design_spec_artifacts?: {
    json_path?: string;
    markdown_path?: string;
  };
  requirement_intent_artifacts?: {
    markdown_path?: string;
    json_path?: string;
  };
  requirement_intent_runtime_status?: string;
  requirement_intent_runtime?: {
    run_id?: string;
    session_id?: string;
    workspace_path?: string;
    error?: string;
    validation_errors?: string[];
    user_requirement_was_empty?: boolean;
  };
  analyst_appendix_premium_pipeline_job_id?: string;
  analyst_appendix_premium_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
  };
  analyst_appendix_premium_final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    markdown_path?: string;
    html_path?: string;
    css_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  ecommerce_long_cli_pipeline_job_id?: string;
  ecommerce_long_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
    stage_outputs?: Record<
      string,
      {
        status?: string;
        validation_status?: string;
        validation_errors?: string[];
        output_files?: string[];
        summary?: string;
      }
    >;
    artifact_index?: Array<{
      name?: string;
      stage_id?: string;
      storage_url?: string;
      artifact_type?: string;
      role?: string;
    }>;
  };
  ecommerce_long_cli_final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    markdown_path?: string;
    html_path?: string;
    css_path?: string;
    chart_insights_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  internet_ops_long_cli_pipeline_job_id?: string;
  internet_ops_long_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
    stage_outputs?: Record<
      string,
      {
        status?: string;
        validation_status?: string;
        validation_errors?: string[];
        output_files?: string[];
        summary?: string;
      }
    >;
    artifact_index?: Array<{
      name?: string;
      stage_id?: string;
      storage_url?: string;
      artifact_type?: string;
      role?: string;
    }>;
  };
  internet_ops_long_cli_final_output?: {
    generate_full_table_version?: boolean;
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    full_table_artifact_name?: string;
    full_table_artifact_path?: string;
    full_table_artifact_url?: string;
    markdown_path?: string;
    markdown_with_tables_path?: string;
    html_path?: string;
    html_with_tables_path?: string;
    css_path?: string;
    chart_insights_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  procurement_sales_long_cli_pipeline_job_id?: string;
  procurement_sales_long_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
    stage_outputs?: Record<
      string,
      {
        status?: string;
        validation_status?: string;
        validation_errors?: string[];
        output_files?: string[];
        summary?: string;
      }
    >;
    artifact_index?: Array<{
      name?: string;
      stage_id?: string;
      storage_url?: string;
      artifact_type?: string;
      role?: string;
    }>;
  };
  procurement_sales_long_cli_final_output?: {
    generate_full_table_version?: boolean;
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    full_table_artifact_name?: string;
    full_table_artifact_path?: string;
    full_table_artifact_url?: string;
    markdown_path?: string;
    markdown_with_tables_path?: string;
    html_path?: string;
    html_with_tables_path?: string;
    css_path?: string;
    chart_insights_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  procurement_sales_long_cli_downloadable?: {
    name?: string;
    path?: string;
    file_path?: string;
    purpose?: string;
    is_main?: boolean;
    type?: string;
  };
  procurement_sales_long_cli_full_table_downloadable?: {
    name?: string;
    path?: string;
    file_path?: string;
    purpose?: string;
    is_main?: boolean;
    type?: string;
  };
  generic_long_cli_pipeline_job_id?: string;
  generic_long_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
    stage_outputs?: Record<
      string,
      {
        status?: string;
        validation_status?: string;
        validation_errors?: string[];
        output_files?: string[];
        summary?: string;
      }
    >;
    artifact_index?: Array<{
      name?: string;
      stage_id?: string;
      storage_url?: string;
      artifact_type?: string;
      role?: string;
    }>;
  };
  generic_long_cli_final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    markdown_path?: string;
    html_path?: string;
    css_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  multi_table_generic_long_cli_pipeline_job_id?: string;
  multi_table_generic_long_cli_pipeline?: {
    status?: string;
    error?: string;
    progress_percent?: number;
    current_stage_id?: string;
    current_stage_title?: string;
    current_stage_detail?: string;
    linked_codex_run_ids?: string[];
    stage_outputs?: Record<
      string,
      {
        status?: string;
        validation_status?: string;
        validation_errors?: string[];
        output_files?: string[];
        summary?: string;
      }
    >;
    artifact_index?: Array<{
      name?: string;
      stage_id?: string;
      storage_url?: string;
      artifact_type?: string;
      role?: string;
    }>;
  };
  multi_table_generic_long_cli_final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    markdown_path?: string;
    html_path?: string;
    css_path?: string;
    review_notes_path?: string;
    delivery_summary?: string;
  };
  linked_codex_pipeline_job_ids?: string[];
  tool_integrations: Array<{
    tool_name: string;
    repo_url: string;
    asset_type: string;
    title: string;
    path: string;
    note: string;
    summary_cards?: Array<{
      name: string;
      value: unknown;
    }>;
  }>;
  sections: SmartReportSection[];
  report_markdown: string;
  report_path: string;
  downloadables: Array<{
    name: string;
    path: string;
    file_path?: string;
    purpose: string;
    is_main: boolean;
    type: string;
  }>;
  main_downloadable: {
    name: string;
    path: string;
    purpose: string;
    is_main: boolean;
    type: string;
  };
};

export type ReportIntentSpec = {
  optimized_user_requirement?: string;
  detected_business_profile?: string;
  business_questions?: string[];
  target_audience?: string;
  core_purpose?: string;
  expected_result?: string;
  analysis_depth?: string;
  required_detail_dimensions?: string[];
  must_include_sections?: string[];
  recommendation_style?: string;
  visual_style?: string;
  color_palette?: string | Record<string, unknown>;
  chart_palette_preset?: string;
  chart_palette_colors?: string[];
  layout_preference?: string;
  pdf_design_brief?: string;
  forbidden_patterns?: string[];
  output_contract?: Record<string, unknown>;
};

export type ReportDesignSpec = {
  version?: string;
  style_preset?: string;
  premium_style_preset?: string;
  visual_style?: string;
  color_palette?: string;
  chart_palette_preset?: string;
  chart_palette_colors?: string[];
  color_source?: string;
  layout_preference?: string;
  pdf_design_brief?: string;
  typography_brief?: string;
  table_style_brief?: string;
  chart_style_brief?: string;
  color_harmony?: {
    mode?: string;
    ratio?: Record<string, string>;
    role_rules?: string[];
    accessibility?: Record<string, unknown>;
  };
  print_constraints?: Record<string, unknown>;
  derived_colors?: {
    primary?: string;
    secondary?: string;
    accent?: string;
    neutral?: string;
    table_header?: string;
    table_header_text?: string;
    background?: string;
    surface?: string;
    subtle?: string;
    divider?: string;
    chart_series?: string[];
  };
  validation_warnings?: string[];
};

export type SmartReportJobEvent = {
  stage_id: string;
  title: string;
  detail: string;
  timestamp: string;
  payload?: Record<string, unknown>;
};

export type RuntimeChildJob = {
  job_id: string;
  run_id: string;
  author_mode?: string;
  runtime_state?: string;
  degradation_state?: string;
  artifact_source?: string;
  parent_report_job_id?: string;
  parent_report_id?: string;
  parent_stage_id?: string;
  child_index?: number;
  stage_id: string;
  purpose: string;
  status: string;
  progress_percent: number;
  current_stage_id: string;
  current_stage_title: string;
  current_stage_detail: string;
};

export type SmartReportJob = {
  job_id: string;
  dataset_id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  progress_percent: number;
  current_stage_id: string;
  current_stage_title: string;
  current_stage_detail: string;
  created_at: string;
  updated_at: string;
  error?: string;
  result_summary?: Record<string, unknown>;
  result?: SmartReport;
  stage_events?: SmartReportJobEvent[];
  runtime_child_jobs?: RuntimeChildJob[];
  runtime_child_job_ids?: string[];
};

export type CodexPipelineArtifact = {
  artifact_id: string;
  stage_id: string;
  name: string;
  path: string;
  storage_url: string;
  artifact_type: string;
  role: string;
  is_primary: boolean;
  created_at: string;
};

export type CodexPipelineJob = {
  pipeline_job_id: string;
  pipeline_type:
    | "r_workflow_premium_pdf"
    | "analyst_appendix_premium_pdf"
    | "generic_long_cli_pipeline"
    | "ecommerce_long_cli_pipeline"
    | "procurement_sales_long_cli_pipeline"
    | "internet_ops_long_cli_pipeline"
    | "multi_table_generic_long_cli_pipeline"
    | "historical_style_report_cli_pipeline";
  workspace_path: string;
  session_id: string;
  stage_order: Array<{
    stage_id: string;
    title: string;
    kind?: string;
    required?: boolean;
    retryable?: boolean;
    depends_on?: string[];
  }>;
  current_stage: {
    stage_id: string;
    title: string;
    status: string;
    attempt: number;
    started_at: string;
    run_id: string;
    task_id: string;
    detail: string;
  };
  stage_outputs: Record<
    string,
    {
      status: string;
      run_id?: string;
      task_id?: string;
      output_files?: string[];
      summary?: string;
      completed_at?: string;
      validation_status?: string;
      validation_errors?: string[];
      render_result?: Record<string, unknown>;
    }
  >;
  artifact_index: CodexPipelineArtifact[];
  final_output?: {
    main_artifact_name?: string;
    main_artifact_path?: string;
    main_artifact_url?: string;
    reverse_spec_markdown_path?: string;
    reverse_spec_json_path?: string;
    page_plan_markdown_path?: string;
    page_plan_json_path?: string;
    chart_assets_index_path?: string;
    table_assets_index_path?: string;
    collage_assets_index_path?: string;
    deck_layout_pack_path?: string;
    markdown_path?: string;
    html_path?: string;
    css_path?: string;
    review_notes_path?: string;
    historical_report_family?: string;
    rendered_page_count?: number;
    planned_page_count?: number;
    template_counts?: Record<string, number>;
    delivery_summary?: string;
  };
  linked_report_id: string;
  linked_codex_run_ids: string[];
  status: string;
  error?: string;
  progress_percent: number;
  current_stage_id: string;
  current_stage_title: string;
  current_stage_detail: string;
  created_at: string;
  updated_at: string;
  result_summary?: Record<string, unknown>;
};

export type ReportDownloadable = {
  name: string;
  path: string;
  file_path?: string;
  purpose: string;
  is_main: boolean;
  type: string;
  download_kind?: string;
  method_id?: string;
  method_name?: string;
  method_name_zh?: string;
  family?: string;
  package_ref?: string;
  method_package_count?: number;
  method_display_package_count?: number;
  method_display_policy?: Record<string, unknown>;
  display_group?: Record<string, unknown>;
  runtime_handoff_count?: number;
  dispatch_plan_count?: number;
  report_part_dispatch_count?: number;
  runtime_dispatch_count?: number;
  pre_method_preprocessing_status?: string;
  external_skill_count?: number;
  external_skill_ids?: string[];
  external_skill_application_required?: boolean;
  external_skill_application_status?: string;
};

export type ReportAgentTurn = {
  turn_id: string;
  task_id?: string;
  run_id?: string;
  native_turn_id?: string;
  status: string;
  user_message?: string;
  started_at?: string;
  completed_at?: string;
  changed_files?: string[];
  artifacts?: ReportDownloadable[] | Array<Record<string, unknown>>;
  revision_intent?: Record<string, unknown>;
  revision_verification?: Record<string, unknown>;
  attempt_count?: number;
  auto_repair_applied?: boolean;
  final_scope_status?: string;
  baseline_artifacts?: Record<string, string>;
};

export type ReportAgentSession = {
  session_id: string;
  report_id: string;
  status: string;
  session_status?: string;
  current_turn_status?: string;
  current_turn?: ReportAgentTurn;
  turns?: ReportAgentTurn[];
  title?: string;
  created_at?: string;
  updated_at?: string;
  current_task_id?: string;
  current_run_id?: string;
  codex_session_id?: string;
  mode?: string;
  codex_thread_id?: string;
  active_turn_id?: string;
  native_connection_status?: string;
  native_protocol_error?: string;
  guidance_injections?: Array<Record<string, unknown>>;
  preview_url?: string;
  preview_artifact?: ReportDownloadable;
  published_versions?: Array<Record<string, unknown>>;
  workspace_path?: string;
  revision_agent_contract_version?: string;
  attachments?: ReportAttachment[];
  attachment_profile_url?: string;
};

export type ReportCatalogItem = {
  report_id: string;
  title: string;
  content_title?: string;
  dataset_id?: string;
  dataset_name?: string;
  business_profile?: string;
  generated_at?: string;
  updated_at?: string;
  main_downloadable?: ReportDownloadable;
  preview_downloadable?: ReportDownloadable;
  preview_url?: string;
  downloadable_count?: number;
  latest_revision_session?: ReportAgentSession | null;
};

export type ReportCatalogDatasetStat = {
  dataset_id: string;
  dataset_name?: string;
  count: number;
};

export type ReportCatalogBusinessProfileStat = {
  business_profile: string;
  count: number;
};

export type ReportCatalogIndexStatus = {
  database_path?: string;
  is_fresh?: boolean;
  last_scan_started_at?: string;
  last_scan_completed_at?: string;
  last_scan_count?: number;
  is_refreshing?: boolean;
  refresh_mode?: string;
  last_error?: string;
  known_report_count?: number;
  is_partial?: boolean;
  indexed_report_count?: number;
};

export type ReportCatalogResponse = {
  reports: ReportCatalogItem[];
  total_count: number;
  returned_count: number;
  offset: number;
  limit: number;
  filters?: {
    keyword?: string;
    dataset_id?: string;
    business_profile?: string;
    sort_by?: string;
  };
  stats?: {
    datasets?: ReportCatalogDatasetStat[];
    business_profiles?: ReportCatalogBusinessProfileStat[];
  };
  index_status?: ReportCatalogIndexStatus;
};

export type ReportCatalogDetail = ReportCatalogItem & {
  manifest?: Record<string, unknown>;
  downloadables: ReportDownloadable[];
  revision_sessions: ReportAgentSession[];
};

export type ReportAgentEvent = {
  event_id: number;
  session_id: string;
  report_id: string;
  turn_id?: string;
  kind: string;
  role?: "user" | "assistant" | "tool" | "system" | string;
  display_kind?: "message" | "tool_call" | "tool_result" | "artifact" | "error" | "status" | string;
  timestamp: string;
  text?: string;
  title?: string;
  stage_id?: string;
  tool_call_id?: string;
  tool_name?: string;
  command?: string;
  path?: string;
  preview_url?: string;
  task_id?: string;
  run_id?: string;
  status?: string;
  exit_code?: number | null;
  duration_ms?: number | null;
  output_preview?: string;
  is_error?: boolean;
  raw_payload?: Record<string, unknown>;
  payload?: Record<string, unknown>;
  artifacts?: ReportDownloadable[];
};

export type ReportAgentFile = {
  name: string;
  relative_path: string;
  file_path?: string;
  type: string;
  size: number;
  modified_at?: string;
  url?: string;
};

export type ReportAttachment = {
  attachment_id: string;
  name: string;
  original_filename?: string;
  type?: string;
  content_type?: string;
  size: number;
  file_path?: string;
  url?: string;
  uploaded_at?: string;
  supplemental_evidence?: boolean;
  profile_status?: string;
  profile_error?: string;
  profile?: {
    row_count?: number;
    column_count?: number;
    numeric_columns?: string[];
    categorical_columns?: string[];
    datetime_columns?: string[];
    chartable_candidates?: Record<string, boolean>;
  };
};

export type ReportAgentDiffFile = {
  kind: string;
  source_path?: string;
  working_path?: string;
  relative_path?: string;
  changed: boolean;
  additions: number;
  deletions: number;
  diff_preview?: string;
};

export type ReportAnnotation = {
  annotation_id: string;
  artifact_url: string;
  artifact_name?: string;
  artifact_id?: string;
  artifact_source?: string;
  artifact_type: "html" | "pdf";
  coordinate_version?: number;
  coordinate_space?: "html_document" | "html_viewport_legacy" | "pdf_page" | string;
  page_number?: number | null;
  target_kind: "page" | "html";
  points: Array<{ x: number; y: number }>;
  shape: "pen" | "rectangle" | "highlight";
  color: string;
  stroke_width: number;
  scroll_offset?: number;
  viewport_width?: number;
  viewport_height?: number;
  document_width?: number;
  document_height?: number;
  page_width?: number;
  page_height?: number;
  render_scale?: number;
  preview_zoom?: number;
  note?: string;
  created_at?: string;
  updated_at?: string;
};

export type RuntimeProcessItem = {
  kind: "report_task" | "pipeline" | "codex_run_task" | "report_agent_turn" | "native_app_server" | "runtime_bootstrap" | string;
  id: string;
  report_id?: string;
  label?: string;
  status: string;
  raw_status?: string;
  observed_status?: string;
  display_status?: string;
  is_active?: boolean;
  is_stale?: boolean;
  scope?: "report" | "active" | string;
  linked_report_title?: string;
  stage_id?: string;
  stage_title?: string;
  progress_percent?: number;
  error?: string;
  can_cancel: boolean;
  can_resume: boolean;
  resume_label?: string;
  disabled_reason?: string;
  started_at?: string;
  updated_at?: string;
  age_seconds?: number | null;
  last_event?: string;
  action_state?: string;
  meta?: Record<string, unknown>;
};

export type RuntimeLearningLedgerEntrySummary = {
  entry_id: string;
  record_key: string;
  source_type: "runtime_run" | "pipeline" | "report" | "report_failure" | string;
  source_id: string;
  status: string;
  report_id?: string;
  linked_report_id?: string;
  report_job_id?: string;
  pipeline_job_id?: string;
  run_id?: string;
  score?: number | null;
  label?: string;
  business_profile?: string;
  pipeline_type?: string;
  prompt_bundle_hash?: string;
  code_version_hash?: string;
  method_signature_hash?: string;
  created_at?: string;
  updated_at?: string;
};

export type RuntimeLearningLedgerEntry = {
  entry_id: string;
  record_key: string;
  source_type: string;
  source_id: string;
  status: string;
  report_id?: string;
  linked_report_id?: string;
  report_job_id?: string;
  pipeline_job_id?: string;
  run_id?: string;
  dataset_id?: string;
  dataset_name?: string;
  sheet_name?: string;
  business_profile?: string;
  report_style?: string;
  pipeline_type?: string;
  workspace_path?: string;
  prompt_version?: {
    prompt_refs?: Array<{
      run_id?: string;
      status?: string;
      stage_id?: string;
      purpose?: string;
      prompt_hash?: string;
      prompt_preview?: string;
      prompt_length?: number;
      created_at?: string;
    }>;
    prompt_bundle_hash?: string;
    prompt_count?: number;
    request_payload_hash?: string;
    requirement_intent_hash?: string;
  };
  code_version?: {
    code_version_hash?: string;
    changed_files_count?: number;
    changed_files_sample?: string[];
    project_git?: {
      head?: string;
      dirty?: boolean;
    };
  };
  statistical_method_version?: {
    method_signature_hash?: string;
    completed_methods?: string[];
    status_counts?: Record<string, number>;
  };
  final_score?: {
    score?: number | null;
    verdict?: string;
    passed?: boolean | null;
    formal_pdf_allowed?: boolean | null;
    release_blocked?: boolean | null;
    gate_fail_items?: string[];
    weaknesses?: string[];
  };
  artifacts?: Record<string, unknown>;
  outcome?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};
