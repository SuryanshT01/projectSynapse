// src/types/analysis.ts

export interface RelatedSection {
  doc_name: string;
  section_title: string;
  page: number;
  snippet: string;
  pdf_available?: boolean;
  pdf_url?: string;
  }
  
  // Assuming insights will be a JSON object with various keys
  export interface Insights {
    [key: string]: any;
  }